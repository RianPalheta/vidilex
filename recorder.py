from typing import Literal
from datetime import datetime

from rich.console import Console

class Recorder():
    def __init__(self):
        self.console = Console()

    def start(self):
        self.console.clear()
        self.console.print("[white on green] INFO [/white on green] Processando vídeos encontrados no Google Drive. Pressione [yellow]CTRL+C[/yellow] para sair.")
        self.console.line()

    def print(self, base_txt: str, status: Literal['PROCESSANDO', 'FEITO', 'FALHA']):
        datetime_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_length = len(datetime_now) + len(base_txt) + len(status)

        if status == 'PROCESSANDO':
            status = f"[#D3C99B]{status}[/#D3C99B]"
        elif status == 'FEITO':
            status = f"[green]{status}[/green]"
        elif status == 'FALHA':
            status = f"[red]{status}[/red]"

        txt = (f"[#646464]{datetime_now}[/#646464]", f"[white not bold]{base_txt}[/white not bold]", "[#646464]:dots[/#646464]", status)
        txt = " ".join(txt).replace(":dots", "." * (self.console.width - total_length - len(txt)))

        self.console.print(txt)
