"""Repositório de usuários."""

import sqlite3


def buscar_todos(conn: sqlite3.Connection) -> list:
    """Retorna todos os usuários."""
    cursor = conn.execute("SELECT id, nome FROM usuarios")
    return cursor.fetchall()
