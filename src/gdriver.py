import os
from rich.progress import Progress
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from utils import slugify, truncate, MediaFile, DOWNLOAD_PATH

class GDriver:
    def __init__(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        
        self.gdrive = GoogleDrive(gauth)
    
    async def download(self, file: MediaFile) -> str:
        file_name, file_ext = os.path.splitext(file['title'])
        save_path = os.path.join(DOWNLOAD_PATH, f"{slugify(file_name)}{file_ext}")
        
        if not os.path.exists(save_path):
            gfile = self.gdrive.CreateFile({'id': file['id']})
            file_size = int(gfile['fileSize'])
            
            with Progress() as progress:
                task = progress.add_task(f"[blue]BAIXANDO:[/blue] {truncate(file_name)}", total=file_size)
                gfile.GetContentFile(
                    save_path, 
                    callback=lambda current, _: progress.update(task, completed=current)
                )
        
        return save_path
    
    async def get_media(self, directory_id: str) -> list[MediaFile]:
        file_list = self.gdrive.ListFile({'q': f"'{directory_id}' in parents and mimeType='video/mp4'"}).GetList()
        return [{'id': file['id'], 'title': file['title'], 'path': None, 'done': False} for file in file_list]
    
    async def directory_exists(self, id: str) -> bool:
        try:
            directory = self.gdrive.CreateFile({'id': id})
            directory.FetchMetadata(fields='title')
            
            return True
        except Exception as _:
            return False