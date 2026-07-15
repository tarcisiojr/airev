"""Progress Reporter - Exibe progresso com spinners e mensagens."""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING

from rich.console import Console

from ..i18n import t

if TYPE_CHECKING:
    from code_reviewer.models import ContextGraph, DiffFile


def is_ci_environment() -> bool:
    """Detecta se está rodando em ambiente CI.

    Verifica:
    1. Se stdout é um TTY (não é pipe/redirecionamento)
    2. Se variáveis de ambiente comuns de CI estão definidas

    Returns:
        True se está em ambiente CI ou não-TTY
    """
    # Não é TTY = provavelmente pipe ou CI
    if not sys.stdout.isatty():
        return True

    # Variáveis de ambiente comuns de CI
    ci_vars = ["CI", "GITLAB_CI", "GITHUB_ACTIONS", "JENKINS_URL", "TRAVIS"]
    return any(os.environ.get(var) for var in ci_vars)


class ProgressReporter:
    """Reporter de progresso com suporte a spinners e modo CI.

    Em modo interativo (TTY), exibe spinners animados.
    Em modo CI, exibe mensagens simples de texto.
    """

    def __init__(
        self,
        console: Console | None = None,
        enabled: bool = True,
        force_terminal: bool | None = None,
    ):
        """Inicializa o reporter.

        Args:
            console: Console do rich (opcional, cria um novo se não fornecido)
            enabled: Se True, exibe progresso. Se False, silencia tudo.
            force_terminal: Se True, força modo terminal mesmo em CI.
                           Se False, força modo CI mesmo em terminal.
                           Se None, auto-detecta.
        """
        self.console = console or Console(force_terminal=force_terminal)
        # Console dedicado para erros: escreve em stderr para não
        # corromper saídas parseáveis (ex: --json-output)
        self._error_console = Console(stderr=True, force_terminal=force_terminal)
        self.enabled = enabled

        # Determina se deve usar animações
        if force_terminal is True:
            self._use_animation = True
        elif force_terminal is False:
            self._use_animation = False
        else:
            self._use_animation = not is_ci_environment()

    @contextmanager
    def status(self, message: str):
        """Context manager que exibe spinner durante uma operação.

        Args:
            message: Mensagem a exibir com o spinner

        Yields:
            O objeto status do rich (ou None em modo CI)

        Example:
            with reporter.status("Processando..."):
                do_work()
        """
        if not self.enabled:
            yield None
            return

        if self._use_animation:
            with self.console.status(message, spinner="dots") as status:
                yield status
        else:
            self.console.print(f"[dim]→[/dim] {message}")
            yield None

    def step(self, message: str) -> None:
        """Exibe uma mensagem de passo/etapa.

        Args:
            message: Mensagem a exibir
        """
        if not self.enabled:
            return

        self.console.print(f"[dim]→[/dim] {message}")

    def success(self, message: str) -> None:
        """Exibe uma mensagem de sucesso.

        Args:
            message: Mensagem a exibir
        """
        if not self.enabled:
            return

        self.console.print(f"[green]✓[/green] {message}")

    def info(self, message: str) -> None:
        """Exibe uma mensagem informativa.

        Args:
            message: Mensagem a exibir
        """
        if not self.enabled:
            return

        self.console.print(f"[blue]ℹ[/blue] {message}")

    def warning(self, message: str) -> None:
        """Exibe uma mensagem de aviso.

        Args:
            message: Mensagem a exibir
        """
        if not self.enabled:
            return

        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def error(self, message: str) -> None:
        """Exibe uma mensagem de erro.

        Erros são SEMPRE exibidos (mesmo com o reporter desabilitado, como
        no modo --json-output) e vão para stderr — uma falha silenciosa
        faria um review que nem executou parecer "código aprovado".

        Args:
            message: Mensagem a exibir
        """
        self._error_console.print(f"[red]✗[/red] {message}")

    def print(self, message: str = "") -> None:
        """Imprime uma mensagem simples.

        Args:
            message: Mensagem a exibir
        """
        if not self.enabled:
            return

        self.console.print(message)

    def show_diff_files(self, files: list[DiffFile]) -> None:
        """Exibe lista de arquivos modificados com contagem de linhas.

        Args:
            files: Lista de arquivos do diff
        """
        if not self.enabled:
            return

        self.console.print()
        self.console.print(f"[bold]{t('progress.modified_files')}[/bold]")
        for file in files:
            # Conta linhas adicionadas e removidas
            added = sum(len(hunk.added_lines) for hunk in file.hunks)
            removed = sum(len(hunk.removed_lines) for hunk in file.hunks)

            # Define cor baseada no status do arquivo
            if file.is_new:
                status = "[green]+[/green]"
            elif file.is_deleted:
                status = "[red]-[/red]"
            else:
                status = "[yellow]~[/yellow]"

            # Formata contagem de linhas
            changes = f"[green]+{added}[/green], [red]-{removed}[/red]"
            self.console.print(f"  {status} {file.path} ({changes})")

    def show_diff_summary(self, files: list[DiffFile]) -> None:
        """Exibe resumo do diff (total de arquivos e linhas).

        Args:
            files: Lista de arquivos do diff
        """
        if not self.enabled:
            return

        total_added = 0
        total_removed = 0

        for file in files:
            total_added += sum(len(hunk.added_lines) for hunk in file.hunks)
            total_removed += sum(len(hunk.removed_lines) for hunk in file.hunks)

        summary = (
            f"[bold]{t('progress.files_label')}[/bold] {len(files)} | "
            f"[bold]{t('progress.lines_label')}[/bold] [green]+{total_added}[/green], "
            f"[red]-{total_removed}[/red]"
        )
        self.console.print(summary)
        self.console.print()

    def show_dependencies(self, contexts: list[ContextGraph]) -> None:
        """Exibe dependências encontradas durante o backtracking.

        Args:
            contexts: Lista de grafos de contexto
        """
        if not self.enabled:
            return

        # Coleta todos os callers e callees únicos
        all_callers: dict[str, set[str]] = {}  # arquivo -> set de funções
        all_callees: dict[str, set[str]] = {}  # arquivo -> set de funções

        for ctx in contexts:
            for caller in ctx.callers:
                if caller.file not in all_callers:
                    all_callers[caller.file] = set()
                if caller.function_name:
                    all_callers[caller.file].add(caller.function_name)

            for callee in ctx.callees:
                if callee.file not in all_callees:
                    all_callees[callee.file] = set()
                if callee.function_name:
                    all_callees[callee.file].add(callee.function_name)

        has_deps = bool(all_callers or all_callees)

        if not has_deps:
            self.console.print(f"[dim]  {t('progress.no_dependencies')}[/dim]")
            return

        if all_callers:
            caller_files = list(all_callers.keys())
            if len(caller_files) <= 3:
                self.console.print(f"  [cyan]{t('progress.callers')}[/cyan] {', '.join(caller_files)}")
            else:
                shown = ", ".join(caller_files[:3])
                more = t("progress.more", count=len(caller_files) - 3)
                self.console.print(
                    f"  [cyan]{t('progress.callers')}[/cyan] {shown} ({more})"
                )

        if all_callees:
            callee_items: list[str] = []
            for file, funcs in all_callees.items():
                if funcs:
                    for func in list(funcs)[:2]:  # Limita a 2 funções por arquivo
                        callee_items.append(f"{func}() em {file}")
                else:
                    callee_items.append(file)

            if len(callee_items) <= 3:
                self.console.print(f"  [cyan]{t('progress.callees')}[/cyan] {', '.join(callee_items)}")
            else:
                shown = ", ".join(callee_items[:3])
                more = t("progress.more", count=len(callee_items) - 3)
                self.console.print(
                    f"  [cyan]{t('progress.callees')}[/cyan] {shown} ({more})"
                )
