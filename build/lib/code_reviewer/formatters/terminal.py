"""Terminal Formatter - Renderização colorida dos resultados."""

from collections import defaultdict
from typing import TextIO
import sys

from ..models import Finding, ReviewResult, Severity


# Códigos ANSI para cores
class Colors:
    """Códigos de cores ANSI."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


def _supports_color() -> bool:
    """Verifica se o terminal suporta cores."""
    # Desabilita cores se não for TTY
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def _colorize(text: str, *codes: str) -> str:
    """Aplica códigos de cor ao texto.

    Args:
        text: Texto a colorir
        codes: Códigos ANSI a aplicar

    Returns:
        Texto com códigos ANSI (ou texto puro se cores desabilitadas)
    """
    if not _supports_color():
        return text
    return "".join(codes) + text + Colors.RESET


def format_severity(severity: Severity) -> str:
    """Formata a severidade com cor.

    Args:
        severity: Severidade do finding

    Returns:
        String formatada com cor
    """
    if severity == Severity.CRITICAL:
        return _colorize(f"[{severity.value}]", Colors.BOLD, Colors.RED)
    elif severity == Severity.WARNING:
        return _colorize(f"[{severity.value}]", Colors.BOLD, Colors.YELLOW)
    else:
        return _colorize(f"[{severity.value}]", Colors.BOLD, Colors.BLUE)


def format_finding(finding: Finding) -> str:
    """Formata um finding para exibição.

    Args:
        finding: Finding a formatar

    Returns:
        String formatada multi-linha
    """
    lines = []

    # Header: [SEVERITY] arquivo:linha - Título
    severity_str = format_severity(finding.severity)
    location = _colorize(f"{finding.file}:{finding.line}", Colors.CYAN)
    title = _colorize(finding.title, Colors.BOLD)

    lines.append(f"  {severity_str} {location} - {title}")

    # Descrição
    if finding.description:
        lines.append(f"  │ {finding.description}")

    # Code snippet
    if finding.code_snippet:
        snippet_lines = finding.code_snippet.strip().split("\n")
        for snippet_line in snippet_lines[:5]:  # Limita a 5 linhas
            lines.append(f"  │ {_colorize(snippet_line, Colors.DIM)}")

    # Sugestão
    if finding.suggestion:
        lines.append("  │")
        lines.append(f"  │ {_colorize('Sugestão:', Colors.GREEN)} {finding.suggestion}")

    lines.append("")

    return "\n".join(lines)


def format_file_header(file_path: str) -> str:
    """Formata o header de um arquivo.

    Args:
        file_path: Caminho do arquivo

    Returns:
        Header formatado
    """
    return _colorize(f"\n{file_path}", Colors.BOLD, Colors.MAGENTA)


def format_header(result: ReviewResult) -> str:
    """Formata o header da análise.

    Args:
        result: Resultado da análise

    Returns:
        Header formatado
    """
    line = "═" * 50
    return f"""
{_colorize(line, Colors.DIM)}
{_colorize("  CODE REVIEW", Colors.BOLD)} — {_colorize(result.branch, Colors.CYAN)}
  Comparado com: {_colorize(result.base, Colors.CYAN)}  │  {result.files_analyzed} arquivo(s)
{_colorize(line, Colors.DIM)}
"""


def format_summary(result: ReviewResult) -> str:
    """Formata o resumo da análise.

    Args:
        result: Resultado da análise

    Returns:
        Resumo formatado
    """
    line = "═" * 50

    if result.summary.total == 0:
        return f"""
{_colorize(line, Colors.DIM)}
  {_colorize("✓ Nenhum problema encontrado. Código aprovado!", Colors.GREEN)}
{_colorize(line, Colors.DIM)}
"""

    critical = _colorize(str(result.summary.critical), Colors.RED) if result.summary.critical else "0"
    warning = _colorize(str(result.summary.warning), Colors.YELLOW) if result.summary.warning else "0"
    info = _colorize(str(result.summary.info), Colors.BLUE) if result.summary.info else "0"

    return f"""
{_colorize(line, Colors.DIM)}
  {_colorize("RESUMO:", Colors.BOLD)} {result.summary.total} finding(s)
  {critical} critical, {warning} warning, {info} info
{_colorize(line, Colors.DIM)}
"""


def format_result(result: ReviewResult, output: TextIO = sys.stdout) -> None:
    """Formata e imprime o resultado completo.

    Args:
        result: Resultado da análise
        output: Stream de saída (default: stdout)
    """
    # Header
    output.write(format_header(result))

    # Agrupa findings por arquivo
    by_file: dict[str, list[Finding]] = defaultdict(list)
    for finding in result.findings:
        by_file[finding.file].append(finding)

    # Imprime findings agrupados
    for file_path, findings in sorted(by_file.items()):
        output.write(format_file_header(file_path))
        output.write("\n")

        # Ordena por linha
        for finding in sorted(findings, key=lambda f: f.line):
            output.write(format_finding(finding))

    # Se tinha arquivos analisados mas sem findings
    if result.files_analyzed > 0 and not result.findings:
        output.write("\n")

    # Resumo
    output.write(format_summary(result))

    # Raw response se houver
    if result.raw_response:
        output.write("\n")
        output.write(_colorize("Resposta raw da IA:", Colors.DIM))
        output.write("\n")
        output.write(result.raw_response[:500])
        if len(result.raw_response) > 500:
            output.write("\n...")
        output.write("\n")
