import os
import multiprocessing
from moviepy.editor import VideoFileClip

def calculate_threads(percentage: int):
    """
    Calcula o número de threads com base na porcentagem especificada dos núcleos da CPU.

    Args:
        percentage (float): A porcentagem de núcleos da CPU a serem usados (0 a 100).

    Returns:
        int: O número de threads a serem usados.
    """
    if not (0 < percentage <= 100):
        raise ValueError("A porcentagem deve estar entre 0 e 100")
    num_cores = multiprocessing.cpu_count()
    print("Número de núcleos da CPU:", num_cores)
    threads = max(1, int(num_cores * (percentage / 100.0)))
    return threads

def process_video(input_path: str, output_path: str, height: int = 240, ext: str | None = None):
    """
    Processa um vídeo redimensionando sua altura para um valor específico e opcionalmente altera sua extensão.

    Parâmetros:
    - input_path (str): O caminho do arquivo de vídeo de entrada.
    - output_path (str): O caminho do arquivo de vídeo de saída.
    - height (int): A altura desejada para o vídeo de saída. O padrão é 240.
    - ext (str | None): A nova extensão desejada para o vídeo de saída. O padrão é None.

    Exemplo de uso:
    process_video("video.mp4", "output.mp4", height=480, ext="avi")
    """
    clip = VideoFileClip(input_path, verbose=False)

    if clip.h > height:
        clip = clip.resize(height=height)

    if ext and not output_path.endswith(f".{ext}"):
        _, original_ext = os.path.splitext(os.path.basename(output_path))
        output_path = output_path.replace(original_ext, f".{ext}")

    clip.write_videofile(output_path, codec='wmv2' if ext == 'asf' else None, verbose=False, logger=None)
    clip.close()

@staticmethod
def hide_file_windows(file_path):
    """
    Oculta um arquivo no sistema operacional Windows.

    Parâmetros:
    - file_path (str): O caminho completo para o arquivo que será ocultado.

    Retorna:
    Nenhum valor de retorno.

    Exemplo de uso:
    hide_file_windows('C:/caminho/para/o/arquivo.txt')
    """
    import ctypes
    FILE_ATTRIBUTE_HIDDEN = 0x02
    ctypes.windll.kernel32.SetFileAttributesW(file_path, FILE_ATTRIBUTE_HIDDEN)
