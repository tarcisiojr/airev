"""Runner para GitHub Copilot CLI."""

import subprocess
from pathlib import Path

from .base import RunnerNotFoundError, check_command_exists


class CopilotCLIRunner:
    """Runner que executa prompts via GitHub Copilot CLI standalone.

    Utiliza o comando `copilot` com flags `--yolo` (auto-aprova tools)
    e `--silent` (output limpo para CI/CD). O prompt é passado via stdin
    para evitar o limite de ARG_MAX do SO em prompts grandes.

    Instalação:
    - Via npm: npm install -g @github/copilot-cli
    - Via Homebrew: brew install github/gh/copilot-cli
    - Via WinGet: winget install GitHub.CopilotCLI

    Documentação: https://github.com/github/copilot-cli
    """

    @property
    def name(self) -> str:
        """Nome identificador do runner."""
        return "copilot"

    def check_availability(self) -> bool:
        """Verifica se o Copilot CLI standalone está disponível."""
        return check_command_exists("copilot")

    def run(self, prompt: str, workdir: Path) -> str:
        """Executa o prompt via Copilot CLI com capacidades agentic.

        Usa flags:
        - --yolo: Auto-aprova todas as tools (leitura de arquivos, etc.)
        - --silent: Output limpo e parseável para CI/CD

        Args:
            prompt: O prompt completo para enviar
            workdir: Diretório de trabalho (usado como contexto para o agente)

        Returns:
            Resposta do Copilot

        Raises:
            RunnerNotFoundError: Se o Copilot CLI não estiver instalado
        """
        if not self.check_availability():
            raise RunnerNotFoundError(
                "GitHub Copilot CLI não encontrado.\n\n"
                "Instale usando uma das opções:\n"
                "  - npm install -g @github/copilot-cli\n"
                "  - brew install github/gh/copilot-cli\n"
                "  - winget install GitHub.CopilotCLI\n\n"
                "Documentação: https://github.com/github/copilot-cli\n\n"
                "Ou configure outro runner com --runner <nome>"
            )

        # Executa copilot com --yolo (auto-approve) e --silent (CI)
        # Prompt passado via stdin para evitar limite de ARG_MAX do SO
        result = subprocess.run(
            ["copilot", "--yolo", "--silent"],
            input=prompt,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=300,  # 5 minutos de timeout
        )

        output = result.stdout
        if result.stderr and "error" in result.stderr.lower():
            output += "\n" + result.stderr

        return output.strip()
