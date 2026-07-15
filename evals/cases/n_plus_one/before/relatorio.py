"""Geração de relatórios de vendas."""

import sqlite3


def listar_clientes(conn: sqlite3.Connection) -> list:
    """Retorna todos os clientes."""
    cursor = conn.execute("SELECT id, nome FROM clientes")
    return cursor.fetchall()
