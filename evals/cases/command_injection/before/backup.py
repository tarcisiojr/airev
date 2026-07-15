"""Utilitário de backup de arquivos."""

import shutil


def copiar_arquivo(origem: str, destino: str) -> None:
    """Copia um arquivo para o destino."""
    shutil.copy2(origem, destino)
