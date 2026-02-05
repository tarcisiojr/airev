"""Context Builder - Backtracking de callers/callees."""

import re
import subprocess
from pathlib import Path
from typing import Optional

from .models import ContextGraph, DiffFile, FunctionRef

# Diretórios excluídos do backtracking
EXCLUDED_DIRS = [
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".tox",
    ".eggs",
    "*.egg-info",
    "vendor",
    "third_party",
]

# Limites para controlar tamanho do contexto
MAX_REFS_PER_SYMBOL = 5
MAX_CONTEXT_LINES = 10


def _build_grep_exclude_args() -> list[str]:
    """Constrói argumentos de exclusão para o grep."""
    args = []
    for dir_pattern in EXCLUDED_DIRS:
        args.extend(["--exclude-dir", dir_pattern])
    return args


def _is_comment_line(line: str) -> bool:
    """Verifica se uma linha é um comentário."""
    stripped = line.strip()
    return (
        stripped.startswith("#")
        or stripped.startswith("//")
        or stripped.startswith("/*")
        or stripped.startswith("*")
        or stripped.startswith("'''")
        or stripped.startswith('"""')
    )


def find_callers(
    function_name: str,
    workdir: Optional[Path] = None,
) -> list[FunctionRef]:
    """Encontra chamadas a uma função no projeto via grep.

    Args:
        function_name: Nome da função a buscar
        workdir: Diretório raiz do projeto

    Returns:
        Lista de referências (FunctionRef) onde a função é chamada
    """
    if not function_name:
        return []

    # Busca por function_name( para pegar chamadas
    pattern = f"{function_name}\\("

    cmd = [
        "grep",
        "-rn",
        "-E",
        pattern,
        ".",
    ] + _build_grep_exclude_args()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=workdir,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return []
    except FileNotFoundError:
        return []

    refs: list[FunctionRef] = []
    seen_locations: set[tuple[str, int]] = set()

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue

        # Formato: ./path/to/file.py:123:conteudo
        match = re.match(r"^\.?/?(.+?):(\d+):(.+)$", line)
        if not match:
            continue

        file_path = match.group(1)
        line_num = int(match.group(2))
        content = match.group(3)

        # Evita duplicatas
        if (file_path, line_num) in seen_locations:
            continue
        seen_locations.add((file_path, line_num))

        # Ignora comentários
        if _is_comment_line(content):
            continue

        # Ignora definições da própria função
        if re.search(r"\bdef\s+" + function_name + r"\b", content):
            continue
        if re.search(r"\bfunction\s+" + function_name + r"\b", content):
            continue

        refs.append(
            FunctionRef(
                file=file_path,
                line=line_num,
                snippet=content.strip(),
            )
        )

        # Limita quantidade de referências
        if len(refs) >= MAX_REFS_PER_SYMBOL:
            break

    return refs


def find_callees(
    added_lines: list[str],
    workdir: Optional[Path] = None,
) -> list[FunctionRef]:
    """Identifica novos símbolos usados nas linhas adicionadas e busca definições.

    Args:
        added_lines: Linhas adicionadas no diff
        workdir: Diretório raiz do projeto

    Returns:
        Lista de referências às definições dos símbolos usados
    """
    # Extrai possíveis chamadas de função das linhas adicionadas
    symbol_pattern = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
    symbols: set[str] = set()

    for line in added_lines:
        matches = symbol_pattern.findall(line)
        for match in matches:
            # Ignora palavras-chave e funções builtin comuns
            if match not in {
                "if",
                "for",
                "while",
                "with",
                "except",
                "print",
                "len",
                "str",
                "int",
                "float",
                "list",
                "dict",
                "set",
                "tuple",
                "range",
                "enumerate",
                "zip",
                "map",
                "filter",
                "sorted",
                "reversed",
                "isinstance",
                "type",
                "hasattr",
                "getattr",
                "setattr",
            }:
                symbols.add(match)

    refs: list[FunctionRef] = []

    for symbol in symbols:
        # Busca definição: def symbol ou class symbol
        pattern = f"(def|class|function|func)\\s+{symbol}\\b"

        cmd = [
            "grep",
            "-rn",
            "-E",
            pattern,
            ".",
        ] + _build_grep_exclude_args()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            match = re.match(r"^\.?/?(.+?):(\d+):(.+)$", line)
            if not match:
                continue

            file_path = match.group(1)
            line_num = int(match.group(2))
            content = match.group(3)

            refs.append(
                FunctionRef(
                    file=file_path,
                    line=line_num,
                    snippet=content.strip(),
                    function_name=symbol,
                )
            )
            break  # Apenas primeira definição por símbolo

        if len(refs) >= MAX_REFS_PER_SYMBOL:
            break

    return refs


def read_file_content(file_path: str, workdir: Optional[Path] = None) -> Optional[str]:
    """Lê o conteúdo completo de um arquivo.

    Args:
        file_path: Caminho relativo do arquivo
        workdir: Diretório raiz do projeto

    Returns:
        Conteúdo do arquivo ou None se não existir
    """
    full_path = Path(workdir or ".") / file_path

    try:
        return full_path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return None


def get_context_around_line(
    file_path: str,
    line_number: int,
    workdir: Optional[Path] = None,
) -> str:
    """Obtém contexto ao redor de uma linha específica.

    Args:
        file_path: Caminho do arquivo
        line_number: Número da linha central
        workdir: Diretório raiz

    Returns:
        Snippet com linhas ao redor
    """
    content = read_file_content(file_path, workdir)
    if not content:
        return ""

    lines = content.split("\n")
    start = max(0, line_number - MAX_CONTEXT_LINES // 2 - 1)
    end = min(len(lines), line_number + MAX_CONTEXT_LINES // 2)

    return "\n".join(lines[start:end])


def build_context_graph(
    diff_files: list[DiffFile],
    workdir: Optional[Path] = None,
) -> list[ContextGraph]:
    """Constrói o grafo de contexto para todas as funções modificadas.

    Args:
        diff_files: Arquivos parseados do diff
        workdir: Diretório raiz do projeto

    Returns:
        Lista de ContextGraph para cada função modificada
    """
    graphs: list[ContextGraph] = []
    seen_functions: set[tuple[str, str]] = set()

    for diff_file in diff_files:
        # Lê conteúdo completo do arquivo
        file_content = read_file_content(diff_file.path, workdir)

        for hunk in diff_file.hunks:
            function_name = hunk.function_name
            if not function_name:
                continue

            # Evita duplicatas
            key = (diff_file.path, function_name)
            if key in seen_functions:
                continue
            seen_functions.add(key)

            # Encontra callers
            callers = find_callers(function_name, workdir)

            # Extrai linhas adicionadas para buscar callees
            added_content = [line.content for line in hunk.added_lines]
            callees = find_callees(added_content, workdir)

            graphs.append(
                ContextGraph(
                    function_name=function_name,
                    file=diff_file.path,
                    callers=callers,
                    callees=callees,
                    file_content=file_content,
                )
            )

    return graphs
