"""AI Runners - Interface plugável para CLIs de IA."""

from typing import Type

from .base import AIRunner, RunnerNotFoundError
from .copilot import CopilotCLIRunner
from .gemini import GeminiCLIRunner

# Registry de runners disponíveis
RUNNERS: dict[str, Type[AIRunner]] = {
    "gemini": GeminiCLIRunner,
    "copilot": CopilotCLIRunner,
}

# Runner padrão
DEFAULT_RUNNER = "gemini"


def get_runner(name: str) -> AIRunner:
    """Obtém uma instância do runner pelo nome.

    Args:
        name: Nome do runner (gemini, copilot, etc)

    Returns:
        Instância do runner

    Raises:
        ValueError: Se o runner não existir
    """
    if name not in RUNNERS:
        available = ", ".join(RUNNERS.keys())
        raise ValueError(f"Runner '{name}' não encontrado. Disponíveis: {available}")

    return RUNNERS[name]()


def list_runners() -> list[str]:
    """Lista os nomes dos runners disponíveis.

    Returns:
        Lista de nomes de runners
    """
    return list(RUNNERS.keys())


__all__ = [
    "AIRunner",
    "RunnerNotFoundError",
    "GeminiCLIRunner",
    "CopilotCLIRunner",
    "get_runner",
    "list_runners",
    "DEFAULT_RUNNER",
    "RUNNERS",
]
