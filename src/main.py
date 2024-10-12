import os, sys, time, asyncio, logging, nest_asyncio, traceback, webbrowser
from InquirerPy import prompt
from rich.panel import Panel
from rich.align import Align
from rich.console import Console
from rich.progress import Progress
from queue import Queue
from typing import Literal
from moviepy.editor import VideoFileClip

from db import DB
from utils import slugify, truncate, create_folders, MediaFile, VIDEO_QUALITY_MAP, DIRECTORY_PATH, TMP_PATH, DOWNLOAD_PATH, DB_PATH
from gdriver import GDriver

nest_asyncio.apply()

class VidiLex():
    def __init__(
        self,
        save_dir: str = "videos",
        output_format: Literal['asf', 'flv', 'mov', 'mp4', 'ogg', 'webm', 'wmv'] = "mp4",
        video_quality: Literal['120p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p'] = "360p",
    ):
        create_folders(save_dir)  
        
        self.db = DB()
        self.task = Queue()
        self.gdrive = GDriver()
        self.console = Console()
        
        self.save_dir = save_dir
        self.output_format = output_format
        self.width, self.height = VIDEO_QUALITY_MAP[video_quality]
        
        logging.basicConfig(
            level=logging.ERROR,                                # Nível de log (ERROR irá capturar exceções)
            format='%(asctime)s - %(levelname)s - %(message)s', # Formato da mensagem de log
            filename=os.path.join(DIRECTORY_PATH, 'errors.log') # Nome do arquivo de log
        )


    def screen_view(self):
        self.console.clear()
        
        logo = """
:::     ::: ::::::::::: ::::::::: ::::::::::: :::        :::::::::: :::    ::: 
:+:     :+:     :+:     :+:    :+:    :+:     :+:        :+:        :+:    :+: 
+:+     +:+     +:+     +:+    +:+    +:+     +:+        +:+         +:+  +:+  
+#+     +:+     +#+     +#+    +:+    +#+     +#+        +#++:++#     +#++:+   
 +#+   +#+      +#+     +#+    +#+    +#+     +#+        +#+         +#+  +#+  
  #+#+#+#       #+#     #+#    #+#    #+#     #+#        #+#        #+#    #+# 
    ###     ########### ######### ########### ########## ########## ###    ### 
        """
        
        self.console.print(
            Align.center(
                Panel.fit(logo, subtitle="Automação de Vídeos")
            )
        )
        self.console.line()
        self.console.print("[white on green] INFO [/white on green] Feito por José Leite e Rian Cristyan para auxiliar nas tarefas deste Egrégio Tribunal de Justiça do Estado do Acre — TJAC.")
        self.console.print("[white on #FFA500] AVISO [/white on #FFA500] Este sistema está em fase de desenvolvimento e pode apresentar algumas instabilidades.")
        self.console.line()

    async def queue(self, answers: dict):
        with self.console.status("[bold green]Validando o ID da pasta no Google Drive...[/bold green]", spinner="bouncingBar"):
            folder_id_is_valid = await self.gdrive.directory_exists(answers['folder_id'])
        
        if not folder_id_is_valid:
            self.console.print("[red]A pasta não foi encontrada. Verifique o ID e tente novamente.[/red]")
            self.db.delete_setting('folder_id')
            
            time.sleep(5)
            self.screen_view()
            return await self.main_menu()
        
        while True:
            with self.console.status("[bold green]Buscando arquivos de mídia no Google Drive...[/bold green]", spinner="bouncingBar"):
                medias = await self.gdrive.get_media(answers['folder_id'])
            
            for media in medias:
                 if not self.db.file_already_processed(media['id']):
                    self.task.put(media)
            
            while not self.task.empty():
                media = self.task.get()
                media['path'] = await self.gdrive.download(media)
                
                try:
                    await self.process_file(media)
                    self.db.save_processed_file(media)
                    self.console.print(f'[green]SUCESSO:[/green] [white]O arquivo "{media["title"].lower()}" foi processado com êxito![/white]')
                except Exception as _:
                    logging.error(traceback.format_exc())
                    self.console.print(f'[red]ERROR:[/red] [white]Algo deu errado ao processar "{media["title"].lower()}"[/white]')
                    
                time.sleep(1)
                self.task.task_done()
                os.remove(media['path'])
            
            await asyncio.sleep(30)

    async def main_menu(self):
        choices = [
            {"name": "🚀 Iniciar Aplicação", "value": "start"},
            {"name": "💖 Fazer uma Doação", "value": "donate"},
            {"name": "🗑️  Limpar Histórico", "value": "clear_history"},
            {"name": "❌ Sair do Aplicativo", "value": "exit"}
        ]
        
        if self.db.get_setting('folder_id') is not None:
            choices.insert(1, {"name": "📂 Trocar a Pasta do Google Drive", "value": "change_folder"})
        
        questions = [
            {
                "type": "list",
                "message": "Escolha uma opção:",
                "choices": choices,
                "name": "menu_option"
            }
        ]
        
        choice = prompt(questions)['menu_option']
                
        self.screen_view()
        
        if choice == "start":
            await self.queue(
                answers=await self.questions()
            )
        elif choice == "change_folder":
            self.db.delete_setting('folder_id')
                
            answers = await self.questions()
            self.screen_view()
            await self.queue(answers)
        elif choice == "donate":
            self.console.print("[bold green]🎉 Muito obrigado por considerar uma doação! Seu apoio faz toda a diferença! 🙌[/bold green]")
            webbrowser.open("https://donate.stripe.com/4gw9DHe1n8Fj5q04gg")
            
            with self.console.status("[yellow]Redirecionando de volta ao menu...[/yellow]", spinner="bouncingBar"):
                time.sleep(5)
            
            self.screen_view()
            await self.main_menu()
        elif choice == "clear_history":
            self.db.clear_processed_files()
            
            answers = await self.questions()
            self.screen_view()
            await self.queue(answers)
        elif choice == "exit":
            with self.console.status("[yellow]Encerrando o aplicativo...[/yellow]", spinner="bouncingBar"):
                time.sleep(2)
            
            self.console.print("[bold magenta]👋 Até mais! Obrigado por usar o aplicativo.[/bold magenta]")
            sys.exit(0)

    async def questions(self):
        answers = dict()
        answers['folder_id'] = self.db.get_setting('folder_id')
        
        if answers['folder_id'] is None:
            folder_id_is_valid = False
            
            while not folder_id_is_valid:
                questions = [
                    {
                        "type": "input",
                        "name": "folder_id",
                        "message": "Digite o ID da pasta do Google Drive (ex: 1A2B3C4D5E):",
                    }
                ]
                
                answers = prompt(questions)

                with self.console.status("[bold green]Validando o ID da pasta no Google Drive...[/bold green]", spinner="bouncingBar"):
                    folder_id_is_valid = await self.gdrive.directory_exists(answers['folder_id'])

                if not folder_id_is_valid:
                    self.console.print("[bold red]ID inválido! Verifique se o ID da pasta do Google Drive está correto e tente novamente.[/bold red]")
                else:
                    self.db.save_setting('folder_id', answers['folder_id'])

        return answers
    
    async def process_file(self, file: MediaFile):
        output_path = os.path.join(
            self.save_dir, 
            f"{slugify(file['title'])}.{self.output_format}"
        )
        
        clip = VideoFileClip(file['path'])
        clip_resized = clip.resize(width=self.width, height=self.height)
        
        with Progress() as progress:
            task = progress.add_task(f"[blue]PROCESSANDO:[/blue] {truncate(file['title'])}", total=100)
            clip_resized.write_videofile(
                output_path,
                codec="libx264",
                logger=None,
                verbose=False,
                on_progress=lambda percent: progress.update(task, completed=percent),
                temp_audiofile=os.path.join(TMP_PATH, f"{file['id']}.mp3")
            )
            
        clip_resized.close()
        
    async def __call__(self):
        self.screen_view()

        try:
            await self.main_menu()
        except KeyboardInterrupt:
            self.screen_view()
            with self.console.status("[yellow]Encerrando o aplicativo...[/yellow]", spinner="bouncingBar"):
                time.sleep(2)
            
            self.console.print("[bold magenta]👋 Até mais! Obrigado por usar o aplicativo.[/bold magenta]")
            sys.exit(0)

async def main():
    await VidiLex("videos", "asf", "360p")()

try:
    asyncio.run(main())
except SystemExit:
    pass