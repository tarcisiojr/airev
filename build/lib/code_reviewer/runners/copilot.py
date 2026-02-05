"""Runner para GitHub Copilot CLI."""

import subprocess
import tempfile
from pathlib import Path

from .base import RunnerNotFoundError, check_command_exists


class CopilotCLIRunner:
    """Runner que executa prompts via GitHub Copilot CLI.

    Requer GitHub CLI (gh) com a extensão Copilot instalada.

    Instalação:
    1. Instale gh: https://cli.github.com/
    2. Instale extensão: gh extension install github/gh-copilot
    3. Autentique: gh auth login
    """

    @property
    def name(self) -> str:
        """Nome identificador do runner."""
        return "copilot"

    def check_availability(self) -> bool:
        """Verifica se gh copilot está disponível."""
        if not check_command_exists("gh"):
            return False

        # Verifica se a extensão copilot está instalada
        try:
            result = subprocess.run(
                ["gh", "extension", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return "copilot" in result.stdout.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def run(self, prompt: str, workdir: Path) -> str:
        """Executa o prompt via GitHub Copilot CLI.

        Args:
            prompt: O prompt completo para enviar
            workdir: Diretório de trabalho

        Returns:
            Resposta do Copilot

        Raises:
            RunnerNotFoundError: Se gh copilot não estiver disponível
            subprocess.CalledProcessError: Se a execução falhar
        """
        if not self.check_availability():
            raise RunnerNotFoundError(
                "GitHub Copilot CLI não encontrado.\n"
                "Instale com:\n"
                "  1. gh (https://cli.github.com/)\n"
                "  2. gh extension install github/gh-copilot\n"
                "  3. gh auth login\n"
                "Ou configure outro runner com --runner <nome>"
            )

        # Escreve o prompt em arquivo temporário
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".md",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(prompt)
            prompt_file = f.name

        try:
            # Usa gh copilot explain que aceita prompts longos
            # O prompt é passado via stdin
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_content = f.read()

            result = subprocess.run(
                [
                    "gh",
                    "copilot",
                    "explain",
                    prompt_content[:10000],  # Limita tamanho para evitar problemas
                ],
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=300,
            )

            output = result.stdout
            if result.stderr and "error" in result.stderr.lower():
                output += "\n" + result.stderr

            return output.strip()

        finally:
            Path(prompt_file).unlink(missing_ok=True)
