"""Utilitário de backup de arquivos."""

import shutil
import subprocess


def copiar_arquivo(origem: str, destino: str) -> None:
    """Copia um arquivo para o destino."""
    shutil.copy2(origem, destino)


def compactar(diretorio: str, nome_arquivo: str) -> None:
    """Compacta um diretório em tar.gz."""
    subprocess.run(
        f"tar -czf {nome_arquivo}.tar.gz {diretorio}",
        shell=True,
        check=True,
    )
