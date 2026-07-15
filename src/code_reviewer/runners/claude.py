"""Runner para Claude Code CLI."""

import subprocess
from pathlib import Path

from .base import RunnerExecutionError, RunnerNotFoundError, check_command_exists


class ClaudeCLIRunner:
    """Runner que executa prompts via Claude Code CLI.

    Utiliza o modo print (`-p`), que recebe o prompt via stdin e retorna
    a resposta em stdout de forma não-interativa — ideal para CI/CD.

    O prompt do airev é autocontido (diff + contexto + referências), então
    não é necessário habilitar tools agentic; o modo print padrão basta.

    Instalação:
    - npm install -g @anthropic-ai/claude-code
    - Documentação: https://docs.claude.com/en/docs/claude-code
    """

    @property
    def name(self) -> str:
        """Nome identificador do runner."""
        return "claude"

    def check_availability(self) -> bool:
        """Verifica se o Claude Code CLI está disponível."""
        return check_command_exists("claude")

    def run(self, prompt: str, workdir: Path) -> str:
        """Executa o prompt via Claude Code CLI em modo print.

        Args:
            prompt: O prompt completo para enviar
            workdir: Diretório de trabalho (raiz do repositório analisado)

        Returns:
            Resposta do Claude

        Raises:
            RunnerNotFoundError: Se o Claude Code CLI não estiver instalado
            RunnerExecutionError: Se a execução do CLI falhar
        """
        if not self.check_availability():
            raise RunnerNotFoundError(
                "Claude Code CLI não encontrado no PATH.\n"
                "Instale com: npm install -g @anthropic-ai/claude-code\n"
                "Documentação: https://docs.claude.com/en/docs/claude-code\n"
                "Ou configure outro runner com --runner <nome>"
            )

        # Modo print (-p): não-interativo, prompt via stdin para evitar
        # o limite de ARG_MAX do SO em prompts grandes
        result = subprocess.run(
            ["claude", "-p"],
            input=prompt,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=300,  # 5 minutos de timeout
        )

        # Falha do CLI não pode virar "resposta da IA" — sem esta checagem,
        # erros de autenticação/configuração viram um review vazio silencioso
        if result.returncode != 0:
            error_output = (result.stderr or result.stdout or "").strip()
            raise RunnerExecutionError(
                f"claude CLI falhou (exit code {result.returncode}): "
                f"{error_output[-500:]}"
            )

        return result.stdout.strip()
