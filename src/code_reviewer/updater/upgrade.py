"""Funcionalidades de upgrade do pacote."""

import subprocess
import sys
from pathlib import Path

from rich.console import Console

from .. import __version__
from .version_check import check_for_update


def detect_installer() -> str:
    """Detecta qual instalador foi usado (pipx ou pip).

    Returns:
        "pipx" se instalado via pipx, "pip" caso contrário
    """
    exe_path = Path(sys.executable)

    # pipx instala em ~/.local/pipx/venvs/
    if "pipx" in exe_path.parts:
        return "pipx"

    return "pip"


def run_upgrade(console: Console | None = None) -> bool:
    """Executa upgrade do pacote.

    Args:
        console: Console Rich para output (opcional)

    Returns:
        True se upgrade foi executado, False se já está atualizado ou falhou
    """
    if console is None:
        console = Console()

    # Verifica se há atualização disponível
    console.print("[dim]Verificando atualizações...[/]")
    update_info = check_for_update()

    if update_info is None:
        console.print(
            f"[green]✓[/] Você já está na versão mais recente ([cyan]{__version__}[/])"
        )
        return False

    installer = detect_installer()
    console.print(
        f"[yellow]→[/] Atualizando de {update_info.current_version} "
        f"para {update_info.latest_version}..."
    )

    # Monta comando de upgrade
    if installer == "pipx":
        cmd = ["pipx", "upgrade", "airev"]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "airev"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            console.print(
                f"[green]✓[/] Atualizado para versão {update_info.latest_version}"
            )
            return True
        else:
            console.print(f"[red]✗[/] Falha ao atualizar: {result.stderr.strip()}")
            console.print(f"[dim]Tente manualmente: {' '.join(cmd)}[/]")
            return False

    except FileNotFoundError:
        console.print(f"[red]✗[/] Comando '{cmd[0]}' não encontrado")
        if installer == "pipx":
            console.print("[dim]Tente: pip install --upgrade airev[/]")
        return False
    except Exception as e:
        console.print(f"[red]✗[/] Erro inesperado: {e}")
        return False
