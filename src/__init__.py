import os, asyncio, nest_asyncio
from InquirerPy import prompt
from rich.console import Console
from rich.progress import Progress
from queue import Queue
from typing import Literal
from moviepy.editor import VideoFileClip

from utils import slugify, truncate, create_folders, MediaFile, VIDEO_QUALITY_MAP, MOVIEPY_PATH, DOWNLOAD_PATH, DB_PATH
from gdriver import GDriver

nest_asyncio.apply()

class VidiLex():
    def __init__(
        self,
        save_dir: str = "videos",
        output_format: Literal['asf', 'flv', 'mov', 'mp4', 'ogg', 'webm', 'wmv'] = "mp4",
        video_quality: Literal['120p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p'] = "360p",
    ):
        self.gdrive = GDriver()
        self.console = Console()
        self.processed_files = set()
        
        self.save_dir = save_dir
        self.output_format = output_format
        self.width, self.height = VIDEO_QUALITY_MAP[video_quality]

    def information(self):
        self.console.clear()
        self.console.print("[white on green]INFO[/white on green] Bem-vindo ao [bold]VidiLex (BETA)[/bold], seu serviço automático de conversão e compressão de vídeos do Google Drive!")
        self.console.print("[white on green]INFO[/white on green] Feito por José Leite e Rian Cristyan para auxiliar nas tarefas deste Egrégio Tribunal de Justiça do Estado do Acre — TJAC.")
        self.console.print("[white on #FFA500]AVISO[/white on #FFA500] Este sistema está em fase de desenvolvimento e pode apresentar algumas instabilidades. Agradecemos sua paciência e feedback enquanto trabalhamos para melhorar sua experiência.")
        self.console.line()

    async def queue(self, answers: dict):
        queue = Queue()
        
        while True:
            with self.console.status("[bold green]Buscando arquivos de mídia...[/bold green]", spinner="dots"):
                medias = await self.gdrive.get_media(answers['folder_id'])
            
            for media in medias:
                if media['id'] not in self.processed_files:
                    queue.put(media)
                    self.processed_files.add(media['id'])
            
            while not queue.empty():
                media = queue.get()
                
                media['path'] = await self.gdrive.download(media)
                await self.process_file(media)
                media['done'] = True
                
                queue.task_done()
                os.remove(media['path'])
            
            await asyncio.sleep(5)

    async def questions(self):
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
    
    async def process_file(self, file: MediaFile):
        file_name, file_ext = os.path.splitext(file['title'])
        output_path = os.path.join(
            self.save_dir, 
            f"{slugify(file_name)}.{self.output_format}"
        )
        
        clip = VideoFileClip(file['path'])
        clip_resized = clip.resize(width=self.width, height=self.height)
        
        with Progress() as progress:
            task = progress.add_task(f"[blue]PROCESSANDO:[/blue] {truncate(file_name)}", total=100)
            clip_resized.write_videofile(
                output_path,
                codec="wmv2",
                verbose=False,
                logger=None,
                on_progress=lambda percent: progress.update(task, completed=percent),
                temp_audiofile=os.path.join(MOVIEPY_PATH, f"{slugify(file_name)}{file_ext}")
            )
            
        clip_resized.close()
        
    async def __call__(self):
        create_folders(self.save_dir)  
        self.information()

        await self.queue(
            answers=await self.questions()
        ) 

async def main():
    vidilex = VidiLex("videos", "asf", "360p")
    await vidilex()

try:
    asyncio.run(main())
except SystemExit:
    pass