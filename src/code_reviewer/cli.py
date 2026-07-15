"""CLI Entry Point - Comando principal do airev."""

import atexit
import sys
import time
from pathlib import Path

import click

from . import __version__
from .analytics import shutdown_analytics, track_event
from .context_builder import build_context_graph
from .description_input import get_description
from .diff_parser import get_current_branch, get_git_diff, parse_diff
from .formatters.progress import ProgressReporter
from .formatters.terminal import format_result
from .i18n import get_available_languages, set_language, t
from .models import ReviewSummary, Severity
from .prompt_builder import THOROUGH_PASSES, build_prompt
from .response_parser import parse_response
from .runners import DEFAULT_RUNNER, RunnerNotFoundError, get_runner, list_runners
from .static_analysis import run_static_analysis
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
@click.option(
    "--text-quality",
    "-t",
    is_flag=True,
    default=False,
    help="Ativa verificação de ortografia e clareza em mensagens de usuário",
)
@click.option(
    "--description",
    "-d",
    default=None,
    help="Descrição das alterações (contexto para o review). Use '-' para ler de stdin.",
)
@click.option(
    "--no-interactive",
    is_flag=True,
    default=False,
    help="Desabilita prompts interativos (modo CI)",
)
@click.option(
    "--min-confidence",
    "-c",
    type=click.IntRange(1, 10),
    default=7,
    help="Exibe apenas findings com confidence >= N (default: 7). Use 1 para ver todos.",
)
@click.option(
    "--context-lines",
    "-C",
    type=click.IntRange(0, 50),
    default=3,
    help="Linhas de contexto no diff (default: 3). Use 0 para desabilitar.",
)
@click.option(
    "--show-deps",
    "-D",
    is_flag=True,
    default=False,
    help="Exibe grafo de dependências (callers/callees) das funções modificadas",
)
@click.option(
    "--thorough",
    "-T",
    is_flag=True,
    default=False,
    help="Análise profunda: uma passada de IA por categoria (segurança, performance, bugs). Mais lento, maior cobertura.",
)
def review(
    base: str,
    runner: str,
    json_output: bool,
    workdir: Path | None,
    no_progress: bool,
    progress: bool,
    lang: str,
    text_quality: bool,
    description: str | None,
    no_interactive: bool,
    min_confidence: int,
    context_lines: int,
    show_deps: bool,
    thorough: bool,
):
    """Analisa o diff da branch atual contra a branch base.

    Exemplos:

        airev review --base main

        airev review --base develop --runner copilot

        airev review --base main --json-output

        airev review --base main --no-progress

        airev review --base main --text-quality

        airev review --base main -d "Corrige bug de autenticação"

        cat pr_description.md | airev review --base main -d -

        airev review --base main --min-confidence 5

        airev review --base main -c 1  # Ver todos os findings

        airev review --base main --context-lines 5  # Mais contexto no diff

        airev review --base main -C 0  # Sem linhas de contexto
    """
    workdir = workdir or Path.cwd()
    start_time = time.perf_counter()

    # Registra shutdown do analytics no encerramento do processo
    atexit.register(shutdown_analytics)

    # Evento de início do review com flags de configuração
    track_event("review_started", {
        "runner": runner,
        "lang": lang,
        "json_output": json_output,
        "text_quality": text_quality,
        "show_deps": show_deps,
        "no_interactive": no_interactive,
        "min_confidence": min_confidence,
        "context_lines": context_lines,
        "thorough": thorough,
        "version": __version__,
    })

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
        track_event("review_failed", {"error_type": "branch_error", "version": __version__})
        reporter.error(t("cli.error_branch", error=e))
        sys.exit(1)

    reporter.info(t("cli.analyzing", branch=current_branch, base=base))

    # Obtém o diff
    with reporter.status(t("cli.getting_diff")):
        try:
            diff_output = get_git_diff(base, workdir, context_lines=context_lines)
        except Exception as e:
            track_event("review_failed", {"error_type": "diff_error", "version": __version__})
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

    # Obtém descrição das alterações (após mostrar diff para contexto)
    change_description = get_description(
        description_flag=description,
        no_interactive=no_interactive,
        json_output=json_output,
        reporter=reporter,
    )

    # Análise estática determinística (complementar à IA)
    with reporter.status(t("cli.running_static_analysis")):
        static_findings = run_static_analysis(diff_files, workdir)

    if static_findings:
        reporter.info(t("cli.static_findings_found", count=len(static_findings)))

    # Constrói contexto (backtracking)
    with reporter.status(t("cli.building_context")):
        context_graphs = build_context_graph(diff_files, workdir)

    # Exibe dependências encontradas
    if context_graphs:
        reporter.step(t("cli.dependencies_found"))
        reporter.show_dependencies(context_graphs)
        reporter.print()

    # Obtém o runner
    try:
        ai_runner = get_runner(runner)
    except ValueError as e:
        track_event("review_failed", {"error_type": "runner_not_found", "version": __version__})
        reporter.error(t("cli.error_runner_invalid", error=e))
        sys.exit(1)

    # Verifica disponibilidade do CLI
    if not ai_runner.check_availability():
        track_event("review_failed", {"error_type": "runner_unavailable", "version": __version__})
        reporter.error(t("cli.error_runner_unavailable", runner=runner))
        reporter.print(t("cli.error_runner_help"))
        sys.exit(1)

    # Define as passadas: única (padrão) ou uma por categoria (--thorough)
    passes: list[tuple[str, str] | None] = (
        list(THOROUGH_PASSES) if thorough else [None]
    )

    result = None
    merged_findings = []
    merged_good_practices = []
    seen_findings: set = set()
    seen_practices: set = set()

    for pass_number, analysis_pass in enumerate(passes, start=1):
        pass_name, focus = analysis_pass if analysis_pass else (None, None)

        # Monta o prompt (com foco de categoria no modo --thorough)
        with reporter.status(t("cli.building_prompt")):
            prompt = build_prompt(
                diff_files,
                context_graphs,
                current_branch,
                base,
                text_quality=text_quality,
                description=change_description,
                focus=focus,
            )

        if pass_name:
            status_message = t(
                "cli.running_analysis_pass",
                focus=pass_name,
                runner=runner,
                current=pass_number,
                total=len(passes),
            )
        else:
            status_message = t("cli.running_analysis", runner=runner)

        # Executa a análise
        with reporter.status(status_message):
            try:
                response = ai_runner.run(prompt, workdir)
            except RunnerNotFoundError as e:
                track_event("review_failed", {"error_type": "runner_not_found", "version": __version__})
                reporter.error(t("cli.error_runner_not_found", error=e))
                sys.exit(1)
            except Exception as e:
                track_event("review_failed", {"error_type": "runner_error", "version": __version__})
                reporter.error(t("cli.error_execution", error=e))
                sys.exit(1)

        # Parseia a resposta
        with reporter.status(t("cli.processing_response")):
            try:
                result = parse_response(
                    response,
                    branch=current_branch,
                    base=base,
                    files_analyzed=len(diff_files),
                )
            except Exception as e:
                track_event("review_failed", {"error_type": "parse_error", "version": __version__})
                reporter.error(t("cli.error_execution", error=e))
                sys.exit(1)

        # Acumula resultados das passadas (dedupe por arquivo+linha+categoria)
        for finding in result.findings:
            key = (finding.file, finding.line, finding.category)
            if key not in seen_findings:
                seen_findings.add(key)
                merged_findings.append(finding)

        for practice in result.good_practices:
            key = (practice.file, practice.line)
            if key not in seen_practices:
                seen_practices.add(key)
                merged_good_practices.append(practice)

    # passes sempre tem ao menos 1 elemento, então result está definido
    assert result is not None
    result = result.model_copy(
        update={
            "findings": merged_findings,
            "good_practices": merged_good_practices,
        }
    )

    # Mescla findings da análise estática (dedupe por arquivo+linha+categoria)
    if static_findings:
        existing = {(f.file, f.line, f.category) for f in result.findings}
        merged_findings = result.findings + [
            f
            for f in static_findings
            if (f.file, f.line, f.category) not in existing
        ]
        result = result.model_copy(update={"findings": merged_findings})

    # Filtra findings por confidence
    filtered_findings = [
        f for f in result.findings if f.confidence >= min_confidence
    ]

    # Contabiliza findings suprimidos para dar transparência ao usuário
    suppressed = [f for f in result.findings if f.confidence < min_confidence]
    suppressed_count = len(suppressed)
    suppressed_min_confidence = (
        min(f.confidence for f in suppressed) if suppressed else 1
    )

    # Recalcula sumário com findings filtrados (inclui os da análise estática)
    critical = sum(1 for f in filtered_findings if f.severity == Severity.CRITICAL)
    warning = sum(1 for f in filtered_findings if f.severity == Severity.WARNING)
    info = sum(1 for f in filtered_findings if f.severity == Severity.INFO)

    result = result.model_copy(
        update={
            "findings": filtered_findings,
            "summary": ReviewSummary(
                total=len(filtered_findings),
                critical=critical,
                warning=warning,
                info=info,
            ),
        }
    )

    # Calcula tempo total
    elapsed = time.perf_counter() - start_time

    # Evento de review concluído com métricas
    track_event("review_completed", {
        "duration_s": round(elapsed, 2),
        "files_count": len(diff_files),
        "findings_total": result.summary.total,
        "findings_critical": result.summary.critical,
        "findings_warning": result.summary.warning,
        "findings_info": result.summary.info,
        "version": __version__,
    })

    # Output
    if json_output:
        click.echo(result.model_dump_json(indent=2))
    else:
        format_result(
            result,
            context_graphs=context_graphs if show_deps else None,
            show_deps=show_deps,
        )
        reporter.print()

        # Transparência: informa quantos findings foram ocultados pelo filtro
        if suppressed_count > 0:
            reporter.warning(
                t(
                    "cli.findings_suppressed",
                    count=suppressed_count,
                    min_confidence=min_confidence,
                    suggestion=suppressed_min_confidence,
                )
            )

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
