import os, re, unicodedata
from typing import TypedDict

DIRECTORY_PATH = os.path.join(os.path.expanduser('~'), ".vidilex")
DOWNLOAD_PATH = os.path.join(DIRECTORY_PATH, "download")
TMP_PATH = os.path.join(DIRECTORY_PATH, "tmp")
DB_PATH = os.path.join(DIRECTORY_PATH, "vidilex.db")

VIDEO_QUALITY_MAP = {
    '120p': (160, 120),
    '240p': (426, 240),
    '360p': (640, 360),
    '480p': (854, 480),
    '720p': (1280, 720),
    '1080p': (1920, 1080),
    '1440p': (2560, 1440),
    '2160p': (3840, 2160)
}

class MediaFile(TypedDict):
    id: str
    done: bool
    path: str
    title: str

def slugify(value: str) -> str:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')        
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()        
        value = re.sub(r'[-\s]+', '-', value)
        
        return value
    
def truncate(title: str, max_length: int = 30) -> str:
        if len(title) > max_length:
            return title[:max_length - 6].rstrip() + " [...]"
        return title

def create_folders(save_dir: str):
    directories = [
        DIRECTORY_PATH,
        DOWNLOAD_PATH,
        TMP_PATH,        
        save_dir
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
