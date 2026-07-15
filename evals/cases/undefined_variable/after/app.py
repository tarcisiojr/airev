"""Serviço de processamento de pedidos."""


def calcular_total(itens: list[dict]) -> float:
    """Calcula o total do pedido."""
    return sum(item["preco"] * item["quantidade"] for item in itens)


def aplicar_desconto(total: float, cupom: str) -> float:
    """Aplica desconto baseado no cupom."""
    if cupom == "PROMO10":
        percentual = 0.10
    return total * (1 - percentul)
