"""Base interface para AI Runners."""

import shutil
from pathlib import Path
from typing import Protocol, runtime_checkable


class RunnerNotFoundError(Exception):
    """Exceção quando o CLI do runner não está instalado."""

    pass


@runtime_checkable
class AIRunner(Protocol):
    """Interface Protocol para runners de IA.

    Cada implementação encapsula as particularidades de como
    chamar um CLI de IA específico (Gemini, Copilot, Claude, etc).
    """

    @property
    def name(self) -> str:
        """Nome identificador do runner."""
        ...

    def check_availability(self) -> bool:
        """Verifica se o CLI está disponível no sistema.

        Returns:
            True se o CLI está instalado e acessível
        """
        ...

    def run(self, prompt: str, workdir: Path) -> str:
        """Executa o prompt no CLI de IA.

        Args:
            prompt: O prompt completo para enviar à IA
            workdir: Diretório de trabalho (raiz do projeto)

        Returns:
            Resposta da IA como string

        Raises:
            RunnerNotFoundError: Se o CLI não estiver disponível
            subprocess.CalledProcessError: Se a execução falhar
        """
        ...


def check_command_exists(command: str) -> bool:
    """Verifica se um comando existe no PATH.

    Args:
        command: Nome do comando a verificar

    Returns:
        True se o comando existe no PATH
    """
    return shutil.which(command) is not None
