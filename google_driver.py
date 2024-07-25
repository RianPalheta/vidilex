import os
from slugify import slugify
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate_drive() -> GoogleDrive:
    """
    Autentica a API do Google Drive e retorna uma instância do GoogleDrive.

    Retorna:
        GoogleDrive: Uma instância do GoogleDrive autenticada com a API do Google Drive.
    """
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)

def list_files(drive: GoogleDrive, folder_id: str):
    """
    Lista todos os arquivos em uma pasta específica no Google Drive.

    Args:
        drive (GoogleDrive): A instância do Google Drive.
        folder_id (str): O ID da pasta para listar os arquivos.

    Returns:
        list: Uma lista de arquivos na pasta especificada.
    """
    query = f"'{folder_id}' in parents and trashed=false"
    return drive.ListFile({'q': query}).GetList()

def download_file(drive: GoogleDrive, file_id: str, file_name: str, output_path: str) -> str:
    """
    Faz o download de um arquivo do Google Drive.

    Parâmetros:
    - drive: Instância do GoogleDrive para autenticação e acesso ao Drive.
    - file_id: ID do arquivo a ser baixado.
    - file_name: Nome do arquivo a ser salvo.
    - output_path: Caminho de saída onde o arquivo será salvo.

    Retorna:
    - O caminho completo do arquivo baixado.

    """
    file = drive.CreateFile({'id': file_id})
    base_name, original_ext = os.path.splitext(os.path.basename(file_name))
    file_name = slugify(base_name) + original_ext
    file_path = os.path.join(output_path, file_name)

    if not os.path.exists(file_path):
        file.GetContentFile(file_path)

    return file_path

def folder_exists(drive: GoogleDrive, folder_id: str) -> bool:
    """
    Verifica se um ID de pasta existe no Google Drive.

    Args:
        drive (GoogleDrive): A instância do Google Drive.
        folder_id (str): O ID da pasta para verificar.

    Returns:
        bool: True se a pasta existir, False caso contrário.
    """
    try:
        folder = drive.CreateFile({'id': folder_id})
        folder.FetchMetadata(fields='id')
        return True
    except Exception as _:
        return False
