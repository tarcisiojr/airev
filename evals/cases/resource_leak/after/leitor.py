"""Leitura de arquivos de configuração."""

import json


def ler_config(caminho: str) -> dict:
    """Lê um arquivo de configuração JSON."""
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def ler_linhas(caminho: str) -> list[str]:
    """Lê as linhas de um arquivo de texto."""
    arquivo = open(caminho, encoding="utf-8")
    linhas = arquivo.readlines()
    return [linha.strip() for linha in linhas]
