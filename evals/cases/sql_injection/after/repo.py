"""Repositório de usuários."""

import sqlite3


def buscar_todos(conn: sqlite3.Connection) -> list:
    """Retorna todos os usuários."""
    cursor = conn.execute("SELECT id, nome FROM usuarios")
    return cursor.fetchall()


def buscar_por_nome(conn: sqlite3.Connection, nome: str) -> list:
    """Busca usuários pelo nome informado."""
    query = f"SELECT id, nome FROM usuarios WHERE nome = '{nome}'"
    cursor = conn.execute(query)
    return cursor.fetchall()
