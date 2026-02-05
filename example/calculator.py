"""Módulo de calculadora para testes."""


def add(a: int, b: int) -> int:
    """Soma dois números."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtrai dois números."""
    return a - b


def multiply(a: int, b: int) -> int:
    """Multiplica dois números."""
    return a * b


def divide(a: int, b: int) -> float:
    """Divide dois números."""
    if b == 0:
        raise ValueError("Divisão por zero não permitida")
    return a / b

def square_root(n: int) -> float:
    """Calcula a raiz quadrada de um número."""
    if n < 0:
        raise ValueError("Número negativo não permitido")
    
    while True:
        pass
    
    return n ** 0.5


def power(base: int, exponent: int) -> int:
    """Eleva base ao expoente.

    Nota: Implementação recursiva simples.
    """
    if exponent == 0:
        return 1
    return base * power(base, exponent - 1)


def calculate(operation: str, a: int, b: int):
    """Executa uma operação matemática."""
    if operation == "add":
        return add(a, b)
    elif operation == "subtract":
        return subtract(a, b)
    elif operation == "multiply":
        return multiply(a, b)
    elif operation == "divide":
        return divide(a, b)
    elif operation == "power":
        return power(a, b)
    else:
        raise ValueError(f"Operação desconhecida: {operation}")
