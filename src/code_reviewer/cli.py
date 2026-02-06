"""CLI Entry Point - Comando principal do airev."""

import sys
import time
from pathlib import Path

import click

from . import __version__
from .context_builder import build_context_graph
from .diff_parser import get_current_branch, get_git_diff, parse_diff
from .formatters.progress import ProgressReporter
from .formatters.terminal import format_result
from .i18n import get_available_languages, set_language, t
from .prompt_builder import build_prompt
from .response_parser import parse_response
from .runners import DEFAULT_RUNNER, RunnerNotFoundError, get_runner, list_runners
from .updater import check_for_update, notify_update, run_upgrade


@click.group()
@click.version_option(version=__version__)
def main():
    """Code Reviewer - Revisão de código com IA.

    Ferramenta CLI que analisa diffs de código usando
    IA para identificar problemas de segurança, performance e bugs.
    """
    pass


@main.command()
@click.option(
    "--base",
    "-b",
    required=True,
    help="Branch base para comparação (ex: main, develop)",
)
@click.option(
    "--runner",
    "-r",
    default=DEFAULT_RUNNER,
    help=f"Runner de IA a usar ({', '.join(list_runners())}). Default: {DEFAULT_RUNNER}",
)
@click.option(
    "--json-output",
    "-j",
    is_flag=True,
    default=False,
    help="Retorna resultado em JSON ao invés de formatação terminal",
)
@click.option(
    "--workdir",
    "-w",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Diretório do repositório (default: diretório atual)",
)
@click.option(
    "--no-progress",
    is_flag=True,
    default=False,
    help="Desabilita animações e spinners (modo CI)",
)
@click.option(
    "--progress",
    is_flag=True,
    default=False,
    help="Força animações mesmo em ambiente CI",
)
@click.option(
    "--lang",
    "-l",
    default="pt-br",
    type=click.Choice(get_available_languages()),
    help="Idioma das mensagens (default: pt-br)",
)
def review(
    base: str,
    runner: str,
    json_output: bool,
    workdir: Path | None,
    no_progress: bool,
    progress: bool,
    lang: str,
):
    """Analisa o diff da branch atual contra a branch base.

    Exemplos:

        airev review --base main

        airev review --base develop --runner copilot

        airev review --base main --json-output

        airev review --base main --no-progress
    """
    workdir = workdir or Path.cwd()
    start_time = time.perf_counter()

    # Configura o idioma
    set_language(lang)

    # Configura o reporter de progresso
    # --no-progress tem prioridade sobre --progress
    if no_progress:
        force_terminal = False
    elif progress:
        force_terminal = True
    else:
        force_terminal = None  # Auto-detecta

    # Desabilita progresso se output é JSON
    reporter = ProgressReporter(
        enabled=not json_output,
        force_terminal=force_terminal,
    )

    # Verifica atualizações (apenas em modo interativo)
    if not json_output:
        try:
            update_info = check_for_update()
            if update_info:
                notify_update(update_info)
        except Exception:
            # Falha silenciosa - não bloqueia execução
            pass

    # Obtém o nome da branch atual
    try:
        current_branch = get_current_branch(workdir)
    except Exception as e:
        reporter.error(t("cli.error_branch", error=e))
        sys.exit(1)

    reporter.info(t("cli.analyzing", branch=current_branch, base=base))

    # Obtém o diff
    with reporter.status(t("cli.getting_diff")):
        try:
            diff_output = get_git_diff(base, workdir)
        except Exception as e:
            reporter.error(t("cli.error_diff", error=e))
            reporter.print(t("cli.error_diff_help", base=base))
            sys.exit(1)

    if not diff_output.strip():
        reporter.warning(t("cli.no_changes"))
        sys.exit(0)

    # Parseia o diff
    with reporter.status(t("cli.analyzing_diff")):
        diff_files = parse_diff(diff_output)

    if not diff_files:
        reporter.warning(t("cli.no_files"))
        sys.exit(0)

    # Exibe arquivos modificados
    reporter.show_diff_files(diff_files)
    reporter.show_diff_summary(diff_files)

    # Constrói contexto (backtracking)
    with reporter.status(t("cli.building_context")):
        context_graphs = build_context_graph(diff_files, workdir)

    # Exibe dependências encontradas
    if context_graphs:
        reporter.step(t("cli.dependencies_found"))
        reporter.show_dependencies(context_graphs)
        reporter.print()

    # Monta o prompt
    with reporter.status(t("cli.building_prompt")):
        prompt = build_prompt(diff_files, context_graphs, current_branch, base)

    # Obtém o runner
    try:
        ai_runner = get_runner(runner)
    except ValueError as e:
        reporter.error(t("cli.error_runner_invalid", error=e))
        sys.exit(1)

    # Verifica disponibilidade do CLI
    if not ai_runner.check_availability():
        reporter.error(t("cli.error_runner_unavailable", runner=runner))
        reporter.print(t("cli.error_runner_help"))
        sys.exit(1)

    # Executa a análise
    with reporter.status(t("cli.running_analysis", runner=runner)):
        try:
            response = ai_runner.run(prompt, workdir)
        except RunnerNotFoundError as e:
            reporter.error(t("cli.error_runner_not_found", error=e))
            sys.exit(1)
        except Exception as e:
            reporter.error(t("cli.error_execution", error=e))
            sys.exit(1)

    # Parseia a resposta
    with reporter.status(t("cli.processing_response")):
        result = parse_response(
            response,
            branch=current_branch,
            base=base,
            files_analyzed=len(diff_files),
        )

    # Calcula tempo total
    elapsed = time.perf_counter() - start_time

    # Output
    if json_output:
        click.echo(result.model_dump_json(indent=2))
    else:
        format_result(result)
        reporter.print()
        reporter.success(t("cli.analysis_complete", elapsed=elapsed))


@main.command()
def runners():
    """Lista os runners de IA disponíveis."""
    click.echo("Runners disponíveis:")
    for name in list_runners():
        runner = get_runner(name)
        available = "✓" if runner.check_availability() else "✗"
        click.echo(f"  {available} {name}")


@main.command()
def upgrade():
    """Atualiza o airev para a versão mais recente."""
    from rich.console import Console

    console = Console()
    success = run_upgrade(console)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
