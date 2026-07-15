"""Leitura de arquivos de configuração."""

import json


def ler_config(caminho: str) -> dict:
    """Lê um arquivo de configuração JSON."""
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)
