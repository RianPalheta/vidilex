import os
from datetime import datetime, timezone
from rich.progress import Progress
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from utils import truncate, MediaFile, DOWNLOAD_PATH

class GDriver:
    def __init__(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        
        self.gdrive = GoogleDrive(gauth)
    
    async def download(self, file: MediaFile) -> str:
        save_path = os.path.join(DOWNLOAD_PATH, f"{file['id']}.mp4")
        
        if not os.path.exists(save_path):
            gfile = self.gdrive.CreateFile({'id': file['id']})
            file_size = int(gfile['fileSize'])
            
            with Progress() as progress:
                task = progress.add_task(f"[cyan]BAIXANDO:[/cyan] {truncate(file['title'])}", total=file_size)
                gfile.GetContentFile(
                    save_path, 
                    callback=lambda current, _: progress.update(task, completed=current)
                )
        
        return save_path
    
    async def get_media(self, directory_id: str) -> list[MediaFile]:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        query = (
            f"'{directory_id}' in parents and "
            "mimeType='video/mp4' and "
            f"modifiedDate >= '{today}'"
        )

        files = self.gdrive.ListFile({'q': query}).GetList()
        
        return [{'id': file['id'], 'title': file['title'], 'path': None, 'done': False} for file in files]
    
    async def directory_exists(self, id: str) -> bool:
        try:
            directory = self.gdrive.CreateFile({'id': id})
            directory.FetchMetadata(fields='title')
            
            return True
        except Exception as _:
            return False