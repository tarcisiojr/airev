"""Notificação visual de atualizações disponíveis."""

from rich.console import Console
from rich.panel import Panel

from .version_check import UpdateInfo


def notify_update(info: UpdateInfo, console: Console | None = None) -> None:
    """Exibe notificação de atualização disponível.

    Args:
        info: Informações sobre a atualização
        console: Console Rich (opcional, cria um novo se não fornecido)
    """
    if console is None:
        console = Console()

    message = (
        f"[bold yellow]Nova versão {info.latest_version} disponível[/] "
        f"[dim](atual: {info.current_version})[/]\n\n"
        f"Atualize com:\n"
        f"  [cyan]pipx upgrade airev[/]\n\n"
        f"Ou execute: [cyan]airev upgrade[/]"
    )

    panel = Panel(
        message,
        title="[bold]Atualização disponível[/]",
        border_style="yellow",
        padding=(0, 1),
    )

    console.print(panel)
    console.print()  # Linha em branco após o painel
