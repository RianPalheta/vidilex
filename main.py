import os, re, asyncio, tempfile, unicodedata, nest_asyncio
from InquirerPy import prompt
from rich.console import Console
from rich.progress import Progress
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.auth import RefreshError
from typing import Literal
from queue import Queue
from moviepy.editor import VideoFileClip

nest_asyncio.apply()

class VidiLex():
    video_quality_map = {
        '120p': (160, 120),
        '240p': (426, 240),
        '360p': (640, 360),
        '480p': (854, 480),
        '720p': (1280, 720),
        '1080p': (1920, 1080),
        '1440p': (2560, 1440),
        '2160p': (3840, 2160)
    }
    
    def __init__(
        self,
        output_format: str,
        video_quality: Literal['120p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p'],
        save_dir: str = "audiencias",
    ):
        self.gdrive = None
        self.save_dir = save_dir
        self.output_format = output_format
        self.tempdir = os.path.join(tempfile.gettempdir(), ".vidilex")
        self.width, self.height = self.video_quality_map[video_quality]

        self.running = True
        self.processed_files = set()
        
        self.console = Console()

    def _info(self):
        self.console.clear()
        self.console.print("[white on green] INFO [/white on green] Bem-vindo ao [bold]VidiLex (BETA)[/bold], seu serviço automático de conversão e compressão de vídeos do Google Drive!")
        self.console.print("[white on green] INFO [/white on green] Feito por José Leite e Rian Cristyan para auxiliar nas tarefas deste Egrégio Tribunal de Justiça do Estado do Acre — TJAC.")
        self.console.print("[white on #FFA500] AVISO [/white on #FFA500] Este sistema está em fase de desenvolvimento e pode apresentar algumas instabilidades. Agradecemos sua paciência e feedback enquanto trabalhamos para melhorar sua experiência.")
        self.console.line()

    def _gauth(self):
        SETTINGS_FILE = "gdrive_settings.json"
        CREDENTIALS_FILE = "credentials.json"

        gauth = GoogleAuth()
        
        try:
            gauth.LoadClientConfigFile(SETTINGS_FILE)
            gauth.LoadCredentialsFile(CREDENTIALS_FILE)

            if gauth.credentials is None:
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                gauth.Refresh()
            else:
                gauth.Authorize()

            gauth.SaveCredentialsFile(CREDENTIALS_FILE)
            self.gdrive = GoogleDrive(gauth)

        except RefreshError as _:
            if os.path.exists(CREDENTIALS_FILE):
                os.remove(CREDENTIALS_FILE)
                self._gauth()

    async def _queue(self, answers: dict):
        midia_queue = Queue()
        
        while True:
            with self.console.status("[bold green]Buscando arquivos de mídia...[/bold green]", spinner="dots"):
                midias = await self._list_media_files(answers['folder_id'])
            
            for midia in midias:
                if midia['id'] not in self.processed_files:
                    midia_queue.put(midia)
                    self.processed_files.add(midia['id'])
            
            while not midia_queue.empty():
                media = midia_queue.get()
                media['path'] = await self._download_file(media)
                await self._process_file(media)
                os.remove(media['path'])
                midia_queue.task_done()
            
            await asyncio.sleep(5)
    
    def _slugify(self, value: str) -> str:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')        
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()        
        value = re.sub(r'[-\s]+', '-', value)
        
        return value
    
    def _truncate(self, title: str, max_length: int = 30) -> str:
        if len(title) > max_length:
            return title[:max_length - 6].rstrip() + " [...]"
        return title
    
    def _create_folders(self):
        if not os.path.exists(self.tempdir + "/moviepy") or not os.path.exists(self.tempdir + "/download"):
            os.makedirs(self.tempdir + "/moviepy")
            os.makedirs(self.tempdir + "/download")
            
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    
    async def _gauth_validate_folder_id(self, folder_id: str):
        """Verifica se a pasta existe no Google Drive."""
        
        try:
            folder = self.gdrive.CreateFile({'id': folder_id})
            folder.FetchMetadata(fields='title')
            
            return True
        except Exception as _:
            return False

    async def _questions(self):
        # answers = None
        # folder_id_is_valid = False
        
        # while not folder_id_is_valid:
        #     questions = [
        #         {
        #             "type": "input",
        #             "name": "folder_id",
        #             "message": "Digite o ID da pasta do Google Drive (ex: 1A2B3C4D5E):",
        #         }
        #     ]
            
        #     answers = prompt(questions)

        #     with self.console.status("[bold green]Validando o ID da pasta no Google Drive...[/bold green]", spinner="dots"):
        #         folder_id_is_valid = await self._gauth_validate_folder_id(answers['folder_id'])

        #     if not folder_id_is_valid:
        #         self.console.print("[bold red]ID inválido! Verifique se o ID da pasta do Google Drive está correto e tente novamente.[/bold red]")

        # return answers
        return {'folder_id': '1WlWSZYMb8XnBGYwtbKgwgdqUYTQb0hiZ'}

    async def _list_media_files(self, folder_id: str) -> list[dict[str, str]]:
        file_list = self.gdrive.ListFile({'q': f"'{folder_id}' in parents and mimeType='video/mp4'"}).GetList()
        return [{'id': file['id'], 'title': file['title'], 'path': None} for file in file_list]
    
    async def _download_file(self, file: list):
        file_name, file_ext = os.path.splitext(file['title'])
        slugified_name = self._slugify(file_name)
        
        download_path = os.path.join(self.tempdir, "download", f"{slugified_name}{file_ext}")
        
        if not os.path.exists(download_path):
            gfile = self.gdrive.CreateFile({'id': file['id']})
            file_size = int(gfile['fileSize'])
            
            with Progress() as progress:
                task = progress.add_task(f"[blue]BAIXANDO:[/blue] {self._truncate(file_name)}", total=file_size)
                gfile.GetContentFile(download_path, callback=lambda current, _: progress.update(task, completed=current))
        
        return download_path
        # Codificar e muxar os pacotes de áudio
        packets = []
        for packet in audio_stream.encode(audio_frame):
            packets.append(packet)
        
        return packets
    
    async def _process_file(self, file: list):
        file_name, file_ext = os.path.splitext(file['title'])
        output_path = os.path.join(self.save_dir, f"{self._slugify(file_name)}.{self.output_format}")
        
        clip = VideoFileClip(file['path'])
        clip_resized = clip.resize(width=self.width, height=self.height)
        
        with Progress() as progress:
            task = progress.add_task(f"[blue]PROCESSANDO:[/blue] {self._truncate(file_name)}", total=100)
            clip_resized.write_videofile(
                output_path,
                codec="wmv2",
                verbose=False,
                logger=None,
                on_progress=lambda percent: progress.update(task, completed=percent),
                temp_audiofile=f"{self.tempdir}/moviepy/{self._slugify(file_name)}{file_ext}"
            )
            
        clip_resized.close()
    
    async def __call__(self):
        self._create_folders()
        self._gauth()
        self._info()
        
        await self._queue(
            answers=await self._questions()
        )

async def main():
    vidilex = VidiLex("asf", "360p")
    await vidilex()

asyncio.run(main())
