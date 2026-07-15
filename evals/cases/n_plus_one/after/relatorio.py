"""Geração de relatórios de vendas."""

import sqlite3


def listar_clientes(conn: sqlite3.Connection) -> list:
    """Retorna todos os clientes."""
    cursor = conn.execute("SELECT id, nome FROM clientes")
    return cursor.fetchall()


def total_por_cliente(conn: sqlite3.Connection) -> dict:
    """Calcula o total de vendas de cada cliente."""
    totais = {}
    for cliente_id, nome in listar_clientes(conn):
        cursor = conn.execute(
            "SELECT SUM(valor) FROM vendas WHERE cliente_id = ?",
            (cliente_id,),
        )
        totais[nome] = cursor.fetchone()[0] or 0
    return totais
