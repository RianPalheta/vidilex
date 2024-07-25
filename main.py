import os
import sys
import time
import signal
import queue
import platform
import warnings
import threading

from InquirerPy import prompt
from rich.console import Console
from pydrive2.drive import GoogleDrive
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils import process_video, hide_file_windows, calculate_threads
from google_driver import authenticate_drive, list_files, download_file, folder_exists

from recorder import Recorder

console = Console()
warnings.filterwarnings("ignore")

class ServerAutomation:
    """
    Classe responsável por automatizar o processamento de vídeos em um servidor.

    Args:
        folder_id (str): O ID da pasta no Google Drive onde os vídeos estão armazenados.
        num_threads (int, opcional): O número de threads para processamento paralelo de vídeos. O padrão é 3.
        download_dir (str, opcional): O diretório onde os vídeos serão baixados. O padrão é 'downloads'.
        processed_dir (str, opcional): O diretório onde os vídeos processados serão salvos. O padrão é 'processed'.

    Attributes:
        folder_id (str): O ID da pasta no Google Drive onde os vídeos estão armazenados.
        num_threads (int): O número de threads para processamento paralelo de vídeos.
        download_dir (str): O diretório onde os vídeos serão baixados.
        processed_dir (str): O diretório onde os vídeos processados serão salvos.
        processed_files_path (str): O caminho para o arquivo que armazena os nomes dos vídeos já processados.
        q (Queue): A fila de vídeos a serem processados.
        threads (list): A lista de threads em execução.
        drive (objeto): O objeto de autenticação do Google Drive.
        already_processed_files (set): O conjunto de nomes de vídeos já processados.

    Methods:
        load_processed_files(): Carrega os nomes dos vídeos já processados a partir do arquivo.
        update_processed_files(file_name: str): Atualiza o arquivo com o nome do vídeo processado.
        process_videos(): Processa os vídeos da fila.
        start_processing_threads(): Inicia as threads de processamento de vídeos.
        stop_processing_threads(): Para as threads de processamento de vídeos.
        monitor_folder(): Monitora a pasta de download em busca de novos arquivos.
        setup_directories(): Configura os diretórios de download e processamento.
        run(): Executa o processo de automação do servidor.
    """
    def __init__(self, drive: GoogleDrive, folder_id, num_threads=3, download_dir='downloads', processed_dir='processed', video_quality=240, output_format='.asf'):
        self.drive = drive
        self.folder_id = folder_id
        self.num_threads = num_threads
        self.download_dir = download_dir
        self.processed_dir = processed_dir
        self.processed_files_path = '.processed_files'
        self.video_quality = video_quality
        self.output_format = output_format

        self.q = queue.Queue()
        self.threads = []

        self.recorder = Recorder()

        self.setup_directories()

    def load_processed_files(self):
        if not os.path.exists(self.processed_files_path):
            open(self.processed_files_path, 'w').close()

            if platform.system() == 'Windows':
                hide_file_windows(self.processed_files_path)

        with open(self.processed_files_path, 'r') as file:
            return set(file.read().splitlines())

    def update_processed_files(self, file_name: str):
        with open(self.processed_files_path, 'a') as file:
            file.write(file_name + '\n')

    def process_videos(self):
        while True:
            file_path, original_file_name = self.q.get()
            if file_path and original_file_name is None:
                break
            output_path=file_path.replace(self.download_dir, self.processed_dir)
            original_file_name, _ = os.path.splitext(os.path.basename(original_file_name))

            try:
                self.recorder.print(base_txt=os.path.basename(original_file_name), status='PROCESSANDO')
                process_video(file_path, output_path, height=self.video_quality, ext=self.output_format)
                self.recorder.print(base_txt=os.path.basename(original_file_name), status='FEITO')
            except Exception as e:
                print(e)
                self.recorder.print(base_txt=os.path.basename(original_file_name), status='FALHA')

            self.q.task_done()

    def start_processing_threads(self):
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.process_videos)
            t.start()
            self.threads.append(t)

    def stop_processing_threads(self):
        for _ in range(self.num_threads):
            self.q.put(None)
        for t in self.threads:
            t.join()

    def monitor_folder(self):
        event_handler = self.NewFileHandler(self.q)
        observer = Observer()
        observer.schedule(event_handler, self.download_dir, recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def setup_directories(self):
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        self.already_processed_files = self.load_processed_files()

    class NewFileHandler(FileSystemEventHandler):
        def __init__(self, queue):
            self.queue = queue

        def on_created(self, event):
            if not event.is_directory and event.src_path.endswith(('.mp4', '.avi', '.mov', '.mkv', '.asf')):
                self.queue.put(event.src_path)

    def run(self):
        self.recorder.start()

        def signal_handler(sig, frame):
            self.q.join()
            self.stop_processing_threads()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        self.start_processing_threads()
        while True:
            files = list_files(drive=self.drive, folder_id=self.folder_id)
            for file in files:
                file_path = download_file(
                    drive=self.drive,
                    file_id=file['id'],
                    file_name=file['title'],
                    output_path=self.download_dir
                )
                file_name = os.path.basename(file_path)

                if file_name not in self.already_processed_files:
                    self.q.put((file_path, file['title']))
                    self.already_processed_files.add(file_name)
                    self.update_processed_files(file_name)

            time.sleep(60)  # Verificar novos arquivos a cada minuto

if __name__ == "__main__":
    try:
        drive = authenticate_drive()
    except Exception as e:
        console.clear()
        console.print(f"[red] FALHA [/red] Ocorreu um erro ao autenticar no Google Drive. Por favor, verifique sua conexão e tente novamente.")
        sys.exit(1)

    console.clear()
    console.print("[white on green] INFO [/white on green] Bem-vindo ao EasyConvert, seu serviço automático de conversão e compressão de vídeos do Google Drive!")
    console.line()

    questions = [
        {
            "type": "input",
            "message": "Por favor, insira o ID da pasta para continuar:",
            "name": "folder_id",
            "validate": lambda value: False if not folder_exists(drive, value) else True,
            "invalid_message": "ID da pasta inválido ou inexistente. Por favor, insira um ID válido.",
            "long_instruction": "EX.: https://drive.google.com/drive/folders/[ID]"
        },
        {
            "type": "input",
            "name": "cpu_usage_percentage",
            "message": "Quantos porcento da máquina você deseja usar?",
            "long_instruction": "Digite um valor entre 1 e 100 para definir a porcentagem de uso da CPU.",
            "default": "50",
            "filter": lambda value: int(value),
            "validate": lambda value: value.isdigit() and 1 <= int(value) <= 100 or "Por favor, insira um valor entre 1 e 100.",
        },
        {
            "type": "list",
            "name": "output_format",
            "message": 'Escolha o formato de arquivo de saída:',
            "choices": [".asf", ".avi", ".mkv", ".mov", ".mp4"],
            "default": ".asf"
        },
        {
            "type": "list",
            "name": "video_quality",
            "message": "Escolha a qualidade de saída do vídeo:",
            "choices": ["144p", "240p", "360p", "480p", "720p", "1080p"],
            "default": "240p",
            "long_instruction": "NOTA: Se a qualidade do vídeo original for igual ou menor que a selecionada, esta opção será ignorada."
        }
    ]

    questions_result = prompt(questions)

    server_automation = ServerAutomation(
        drive=drive,
        folder_id=questions_result.get("folder_id"),
        num_threads=calculate_threads(
            questions_result.get("cpu_usage_percentage")
        ),
        output_format=questions_result.get("output_format").replace(".", ""),
        video_quality=int(questions_result.get("video_quality").replace("p", ""))
    )

    print(questions_result)

    server_automation.run()

