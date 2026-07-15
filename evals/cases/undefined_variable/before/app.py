"""Serviço de processamento de pedidos."""


def calcular_total(itens: list[dict]) -> float:
    """Calcula o total do pedido."""
    return sum(item["preco"] * item["quantidade"] for item in itens)
