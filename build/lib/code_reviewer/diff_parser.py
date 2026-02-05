"""Parser de git diff."""

import re
import subprocess
from pathlib import Path
from typing import Optional

from .models import DiffFile, DiffHunk, DiffLine

# Padrões regex para parsing do diff
FILE_HEADER_PATTERN = re.compile(r"^diff --git a/(.+) b/(.+)$")
HUNK_HEADER_PATTERN = re.compile(
    r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@(?: (.+))?$"
)
NEW_FILE_PATTERN = re.compile(r"^new file mode")
DELETED_FILE_PATTERN = re.compile(r"^deleted file mode")

# Arquivos a serem ignorados na análise
IGNORED_PATTERNS = [
    r".*\.lock$",
    r".*-lock\.json$",
    r".*-lock\.yaml$",
    r"package-lock\.json$",
    r"poetry\.lock$",
    r"Pipfile\.lock$",
    r"yarn\.lock$",
    r"pnpm-lock\.yaml$",
    r".*\.min\.js$",
    r".*\.min\.css$",
    r".*\.map$",
    r".*/migrations/.*",
    r".*/node_modules/.*",
    r".*/__pycache__/.*",
    r".*\.pyc$",
    r".*/dist/.*",
    r".*/build/.*",
    r".*/\.git/.*",
]


def get_git_diff(base_branch: str, workdir: Optional[Path] = None) -> str:
    """Executa git diff e retorna o output.

    Args:
        base_branch: Branch base para comparação (ex: main, develop)
        workdir: Diretório de trabalho (default: diretório atual)

    Returns:
        Output do git diff como string

    Raises:
        subprocess.CalledProcessError: Se o comando git falhar
        FileNotFoundError: Se git não estiver instalado
    """
    cmd = ["git", "diff", f"{base_branch}...HEAD"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=workdir,
        check=True,
    )

    return result.stdout


def get_current_branch(workdir: Optional[Path] = None) -> str:
    """Retorna o nome da branch atual.

    Args:
        workdir: Diretório de trabalho

    Returns:
        Nome da branch atual
    """
    cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=workdir,
        check=True,
    )

    return result.stdout.strip()


def is_ignored_file(path: str) -> bool:
    """Verifica se um arquivo deve ser ignorado na análise.

    Args:
        path: Caminho do arquivo

    Returns:
        True se o arquivo deve ser ignorado
    """
    for pattern in IGNORED_PATTERNS:
        if re.match(pattern, path):
            return True
    return False


def parse_diff(diff_output: str) -> list[DiffFile]:
    """Parseia o output do git diff.

    Extrai arquivos modificados, hunk headers (nomes de funções)
    e linhas adicionadas/removidas.

    Args:
        diff_output: Output do comando git diff

    Returns:
        Lista de DiffFile com informações parseadas
    """
    files: list[DiffFile] = []
    current_file: Optional[DiffFile] = None
    current_hunk: Optional[DiffHunk] = None
    current_line_new = 0
    current_line_old = 0

    lines = diff_output.split("\n")

    for line in lines:
        # Novo arquivo no diff
        file_match = FILE_HEADER_PATTERN.match(line)
        if file_match:
            # Salva arquivo anterior se existir
            if current_file is not None:
                if current_hunk is not None:
                    current_file.hunks.append(current_hunk)
                if not is_ignored_file(current_file.path):
                    files.append(current_file)

            # Inicia novo arquivo
            file_path = file_match.group(2)
            current_file = DiffFile(path=file_path)
            current_hunk = None
            continue

        # Verifica se é arquivo novo ou deletado
        if current_file is not None:
            if NEW_FILE_PATTERN.match(line):
                current_file.is_new = True
                continue
            if DELETED_FILE_PATTERN.match(line):
                current_file.is_deleted = True
                continue

        # Novo hunk
        hunk_match = HUNK_HEADER_PATTERN.match(line)
        if hunk_match and current_file is not None:
            # Salva hunk anterior se existir
            if current_hunk is not None:
                current_file.hunks.append(current_hunk)

            start_old = int(hunk_match.group(1))
            start_new = int(hunk_match.group(2))
            function_name = hunk_match.group(3)

            # Limpa o nome da função (remove espaços extras)
            if function_name:
                function_name = function_name.strip()
                # Extrai apenas o nome da função se houver assinatura
                func_match = re.match(
                    r"(?:def|function|func|class|async\s+def|public|private|protected)?\s*(\w+)",
                    function_name,
                )
                if func_match:
                    function_name = func_match.group(1)

            current_hunk = DiffHunk(
                function_name=function_name if function_name else None,
                start_line_old=start_old,
                start_line_new=start_new,
            )
            current_line_new = start_new
            current_line_old = start_old
            continue

        # Linha adicionada
        if line.startswith("+") and not line.startswith("+++"):
            if current_hunk is not None:
                current_hunk.added_lines.append(
                    DiffLine(
                        line_number=current_line_new,
                        content=line[1:],  # Remove o +
                        is_addition=True,
                    )
                )
                current_line_new += 1
            continue

        # Linha removida
        if line.startswith("-") and not line.startswith("---"):
            if current_hunk is not None:
                current_hunk.removed_lines.append(
                    DiffLine(
                        line_number=current_line_old,
                        content=line[1:],  # Remove o -
                        is_addition=False,
                    )
                )
                current_line_old += 1
            continue

        # Linha de contexto (não modificada)
        if line.startswith(" "):
            current_line_new += 1
            current_line_old += 1

    # Salva último arquivo e hunk
    if current_file is not None:
        if current_hunk is not None:
            current_file.hunks.append(current_hunk)
        if not is_ignored_file(current_file.path):
            files.append(current_file)

    return files


def get_modified_functions(diff_files: list[DiffFile]) -> list[tuple[str, str]]:
    """Extrai lista de funções modificadas.

    Args:
        diff_files: Lista de arquivos do diff

    Returns:
        Lista de tuplas (arquivo, nome_funcao)
    """
    functions: list[tuple[str, str]] = []

    for diff_file in diff_files:
        for hunk in diff_file.hunks:
            if hunk.function_name:
                functions.append((diff_file.path, hunk.function_name))

    return functions
