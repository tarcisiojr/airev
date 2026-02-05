"""CLI Entry Point - Comando principal do code-reviewer."""

import sys
from pathlib import Path

import click

from . import __version__
from .context_builder import build_context_graph
from .diff_parser import get_current_branch, get_git_diff, parse_diff
from .formatters.terminal import format_result
from .prompt_builder import build_prompt
from .response_parser import parse_response
from .runners import DEFAULT_RUNNER, RunnerNotFoundError, get_runner, list_runners


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
def review(base: str, runner: str, json_output: bool, workdir: Path | None):
    """Analisa o diff da branch atual contra a branch base.

    Exemplos:

        code-reviewer review --base main

        code-reviewer review --base develop --runner copilot

        code-reviewer review --base main --json-output
    """
    workdir = workdir or Path.cwd()

    # Obtém o nome da branch atual
    try:
        current_branch = get_current_branch(workdir)
    except Exception as e:
        click.echo(f"Erro ao obter branch atual: {e}", err=True)
        sys.exit(1)

    click.echo(f"Analisando: {current_branch} → {base}", err=True)

    # Obtém o diff
    try:
        diff_output = get_git_diff(base, workdir)
    except Exception as e:
        click.echo(f"Erro ao obter diff: {e}", err=True)
        click.echo(
            f"Verifique se a branch '{base}' existe e se você está em um repositório git.",
            err=True,
        )
        sys.exit(1)

    if not diff_output.strip():
        click.echo("Nenhuma mudança encontrada no diff.", err=True)
        sys.exit(0)

    # Parseia o diff
    diff_files = parse_diff(diff_output)

    if not diff_files:
        click.echo("Nenhum arquivo relevante para analisar.", err=True)
        sys.exit(0)

    click.echo(f"Arquivos para análise: {len(diff_files)}", err=True)

    # Constrói contexto (backtracking)
    click.echo("Construindo contexto...", err=True)
    context_graphs = build_context_graph(diff_files, workdir)

    # Monta o prompt
    click.echo("Montando prompt...", err=True)
    prompt = build_prompt(diff_files, context_graphs, current_branch, base)

    # Obtém o runner
    try:
        ai_runner = get_runner(runner)
    except ValueError as e:
        click.echo(f"Erro: {e}", err=True)
        sys.exit(1)

    # Verifica disponibilidade do CLI
    if not ai_runner.check_availability():
        click.echo(f"Runner '{runner}' não está disponível.", err=True)
        click.echo("Verifique se o CLI está instalado e configurado.", err=True)
        sys.exit(1)

    # Executa a análise
    click.echo(f"Executando análise com {runner}...", err=True)

    try:
        response = ai_runner.run(prompt, workdir)
    except RunnerNotFoundError as e:
        click.echo(f"Erro: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Erro na execução: {e}", err=True)
        sys.exit(1)

    # Parseia a resposta
    result = parse_response(
        response,
        branch=current_branch,
        base=base,
        files_analyzed=len(diff_files),
    )

    # Output
    if json_output:
        click.echo(result.model_dump_json(indent=2))
    else:
        format_result(result)


@main.command()
def runners():
    """Lista os runners de IA disponíveis."""
    click.echo("Runners disponíveis:")
    for name in list_runners():
        runner = get_runner(name)
        available = "✓" if runner.check_availability() else "✗"
        click.echo(f"  {available} {name}")


if __name__ == "__main__":
    main()
