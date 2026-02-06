"""Funcionalidades de upgrade do pacote."""

import json
import subprocess
import sys
from pathlib import Path

from rich.console import Console

from .. import __version__
from .version_check import check_for_update, clear_cache


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


def get_installed_version(installer: str) -> str | None:
    """Obtém a versão real instalada do airev consultando o instalador.

    Args:
        installer: "pipx" ou "pip"

    Returns:
        String com a versão instalada ou None se não conseguir obter
    """
    try:
        if installer == "pipx":
            # Tenta usar pipx list --json
            result = subprocess.run(
                ["pipx", "list", "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                venvs = data.get("venvs", {})
                if "airev" in venvs:
                    metadata = venvs["airev"].get("metadata", {})
                    return metadata.get("main_package", {}).get("package_version")
            # Fallback: tenta sem --json (versões antigas do pipx)
            return _get_version_from_pipx_list_text()
        else:
            # pip show airev
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "airev"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("Version:"):
                        return line.split(":", 1)[1].strip()
    except (subprocess.SubprocessError, json.JSONDecodeError, KeyError):
        pass
    return None


def _get_version_from_pipx_list_text() -> str | None:
    """Fallback para obter versão do pipx list sem --json.

    Returns:
        String com a versão ou None se não encontrar
    """
    try:
        result = subprocess.run(
            ["pipx", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            # Procura por linha como "airev 1.0.0" ou "package airev 1.0.0"
            for line in result.stdout.splitlines():
                if "airev" in line.lower():
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "airev" in part.lower() and i + 1 < len(parts):
                            version = parts[i + 1].strip(",")
                            # Verifica se parece uma versão
                            if version and version[0].isdigit():
                                return version
    except subprocess.SubprocessError:
        pass
    return None


def run_upgrade(console: Console | None = None) -> bool:
    """Executa upgrade do pacote.

    Args:
        console: Console Rich para output (opcional)

    Returns:
        True se upgrade foi executado com sucesso, False caso contrário
    """
    if console is None:
        console = Console()

    # Verifica se há atualização disponível
    console.print("[dim]Verificando atualizações...[/]")
    update_info = check_for_update()

    if update_info is None:
        # Limpa cache mesmo quando não há atualização (garante consistência)
        clear_cache()
        console.print(
            f"[green]✓[/] Você já está na versão mais recente ([cyan]{__version__}[/])"
        )
        return False

    installer = detect_installer()

    # Obtém versão antes do upgrade para comparação
    version_before = get_installed_version(installer) or __version__

    console.print(
        f"[yellow]→[/] Atualizando de {version_before} "
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

        # Sempre limpa o cache após tentativa de upgrade
        clear_cache()

        if result.returncode == 0:
            # Verifica se a versão realmente mudou
            version_after = get_installed_version(installer)

            if version_after and version_after != version_before:
                console.print(
                    f"[green]✓[/] Atualizado de {version_before} para {version_after}"
                )
                return True
            else:
                # Comando executou mas versão não mudou
                console.print(
                    f"[green]✓[/] Você já está na versão mais recente "
                    f"([cyan]{version_after or version_before}[/])"
                )
                return False
        else:
            console.print(f"[red]✗[/] Falha ao atualizar: {result.stderr.strip()}")
            console.print(f"[dim]Tente manualmente: {' '.join(cmd)}[/]")
            return False

    except FileNotFoundError:
        clear_cache()
        console.print(f"[red]✗[/] Comando '{cmd[0]}' não encontrado")
        if installer == "pipx":
            console.print("[dim]Tente: pip install --upgrade airev[/]")
        return False
    except Exception as e:
        clear_cache()
        console.print(f"[red]✗[/] Erro inesperado: {e}")
        return False
