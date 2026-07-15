"""Análise Estática - Camada determinística complementar à revisão por IA.

Executa linters/compiladores locais sobre os arquivos modificados e converte
diagnósticos de erro (nomes indefinidos, erros de compilação) em findings de
alta confiança. Erros como variável não declarada são detectáveis de forma
determinística — não faz sentido depender do julgamento da IA para isso.

Arquitetura de detectores por linguagem:
- Python: ruff (preferencial) ou pyflakes
- TypeScript: tsc --noEmit (usa o tsconfig.json do projeto)
- JavaScript/TypeScript: eslint (usa a configuração do projeto)
- Go: go build (erros de compilação)

Cada arquivo do diff é roteado para o PRIMEIRO detector disponível que cobre
sua extensão. Se nenhuma ferramenta estiver instalada, a análise é pulada
silenciosamente — esta camada é complementar e nunca bloqueia o review.

Extensível: para suportar outra linguagem (ex: Java via checkstyle), crie um
novo detector herdando de `Detector` e registre-o em `DETECTOR_REGISTRY`.
"""

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .models import Category, DiffFile, Finding, Severity

# Timeout padrão para execução das ferramentas (segundos)
LINTER_TIMEOUT = 120

# Regras do ruff que indicam erro de nome/definição (crash em runtime):
# F821 = undefined name, F823 = variável local usada antes da atribuição
RUFF_RULES = "F821,F823"

# Mensagens do pyflakes equivalentes às regras acima
PYFLAKES_PATTERNS = (
    "undefined name",
    "referenced before assignment",
)

# Regras do eslint que indicam erro que quebra em runtime (não estilo).
# Só reportamos estas para não duplicar o lint de estilo do projeto.
ESLINT_CRITICAL_RULES = frozenset(
    {
        "no-undef",
        "no-const-assign",
        "no-dupe-args",
        "no-dupe-keys",
        "no-dupe-class-members",
        "no-func-assign",
        "no-import-assign",
        "no-obj-calls",
        "no-redeclare",
        "no-setter-return",
        "no-unreachable",
        "no-unsafe-negation",
        "no-use-before-define",
        "no-this-before-super",
        "constructor-super",
        "getter-return",
        "use-isnan",
        "valid-typeof",
    }
)


@dataclass
class Diagnostic:
    """Diagnóstico bruto retornado por uma ferramenta de análise."""

    file: str
    line: int
    message: str
    rule: str


def _run_command(
    command: list[str], workdir: Path
) -> Optional[subprocess.CompletedProcess]:
    """Executa um comando com timeout, retornando None em caso de falha.

    Args:
        command: Comando e argumentos
        workdir: Diretório de execução

    Returns:
        Resultado do processo ou None se a execução falhou
    """
    try:
        return subprocess.run(
            command,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=LINTER_TIMEOUT,
        )
    except (subprocess.SubprocessError, OSError):
        # Falha silenciosa - análise estática é complementar, nunca bloqueia
        return None


def _to_relative_path(file_path: str, workdir: Path) -> str:
    """Converte caminho absoluto da ferramenta para relativo ao repositório.

    Args:
        file_path: Caminho retornado pela ferramenta (absoluto ou relativo)
        workdir: Diretório raiz do repositório

    Returns:
        Caminho relativo ao workdir (igual ao formato do diff)
    """
    path = Path(file_path)
    if path.is_absolute():
        try:
            return str(path.relative_to(workdir.resolve()))
        except ValueError:
            return file_path
    return file_path


def _node_bin(tool: str, workdir: Path) -> Optional[str]:
    """Localiza um binário Node: node_modules/.bin do projeto ou PATH global.

    Args:
        tool: Nome do binário (ex: eslint, tsc)
        workdir: Diretório raiz do repositório

    Returns:
        Caminho do binário ou None se não encontrado
    """
    local_bin = workdir / "node_modules" / ".bin" / tool
    if local_bin.is_file():
        return str(local_bin)
    return shutil.which(tool)


# ============================================
# Parsers puros (testáveis sem os binários)
# ============================================


def parse_ruff_output(stdout: str, workdir: Path) -> list[Diagnostic]:
    """Converte o JSON do ruff em diagnósticos.

    Args:
        stdout: Saída JSON do ruff
        workdir: Diretório raiz do repositório

    Returns:
        Lista de diagnósticos das regras selecionadas
    """
    try:
        entries = json.loads(stdout or "[]")
    except json.JSONDecodeError:
        return []

    diagnostics = []
    for entry in entries:
        code = entry.get("code") or ""
        # Ruff sempre reporta erros de sintaxe (code null) além das regras
        if code and code not in RUFF_RULES.split(","):
            continue

        diagnostics.append(
            Diagnostic(
                file=_to_relative_path(entry.get("filename", ""), workdir),
                line=int(entry.get("location", {}).get("row", 0)),
                message=entry.get("message", "Nome indefinido"),
                rule=code or "syntax-error",
            )
        )

    return diagnostics


def parse_pyflakes_output(stdout: str, workdir: Path) -> list[Diagnostic]:
    """Converte a saída texto do pyflakes em diagnósticos.

    Args:
        stdout: Saída do pyflakes (formato: caminho:linha:coluna: mensagem)
        workdir: Diretório raiz do repositório

    Returns:
        Lista de diagnósticos que casam com os padrões de nome indefinido
    """
    pattern = re.compile(r"^(.+?):(\d+):(?:\d+:?)?\s*(.+)$")
    diagnostics = []

    for output_line in stdout.splitlines():
        match = pattern.match(output_line.strip())
        if not match:
            continue

        file_path, line_number, message = match.groups()
        if not any(p in message for p in PYFLAKES_PATTERNS):
            continue

        diagnostics.append(
            Diagnostic(
                file=_to_relative_path(file_path, workdir),
                line=int(line_number),
                message=message,
                rule="pyflakes",
            )
        )

    return diagnostics


def parse_eslint_output(stdout: str, workdir: Path) -> list[Diagnostic]:
    """Converte o JSON do eslint em diagnósticos.

    Filtra apenas erros (severity 2) de regras que indicam quebra em runtime,
    evitando duplicar o lint de estilo do próprio projeto.

    Args:
        stdout: Saída JSON do eslint
        workdir: Diretório raiz do repositório

    Returns:
        Lista de diagnósticos críticos
    """
    try:
        entries = json.loads(stdout or "[]")
    except json.JSONDecodeError:
        return []

    diagnostics = []
    for entry in entries:
        file_path = _to_relative_path(entry.get("filePath", ""), workdir)
        for message in entry.get("messages", []):
            rule = message.get("ruleId") or ""
            is_fatal = message.get("fatal", False)
            if not is_fatal and (
                message.get("severity") != 2 or rule not in ESLINT_CRITICAL_RULES
            ):
                continue

            diagnostics.append(
                Diagnostic(
                    file=file_path,
                    line=int(message.get("line", 0) or 0),
                    message=message.get("message", "Erro detectado pelo eslint"),
                    rule=rule or "fatal",
                )
            )

    return diagnostics


def parse_tsc_output(stdout: str, workdir: Path) -> list[Diagnostic]:
    """Converte a saída do tsc --noEmit em diagnósticos.

    Args:
        stdout: Saída do tsc (formato: caminho(linha,coluna): error TSxxxx: msg)
        workdir: Diretório raiz do repositório

    Returns:
        Lista de diagnósticos de erro de compilação
    """
    pattern = re.compile(r"^(.+?)\((\d+),\d+\):\s*error\s+(TS\d+):\s*(.+)$")
    diagnostics = []

    for output_line in stdout.splitlines():
        match = pattern.match(output_line.strip())
        if not match:
            continue

        file_path, line_number, code, message = match.groups()
        diagnostics.append(
            Diagnostic(
                file=_to_relative_path(file_path, workdir),
                line=int(line_number),
                message=message,
                rule=code,
            )
        )

    return diagnostics


def parse_go_output(stderr: str, workdir: Path) -> list[Diagnostic]:
    """Converte a saída de erro do go build em diagnósticos.

    Args:
        stderr: Saída de erro do go build (formato: caminho:linha:coluna: msg)
        workdir: Diretório raiz do repositório

    Returns:
        Lista de diagnósticos de erro de compilação
    """
    pattern = re.compile(r"^(.+?\.go):(\d+):(?:\d+:)?\s*(.+)$")
    diagnostics = []

    for output_line in stderr.splitlines():
        match = pattern.match(output_line.strip())
        if not match:
            continue

        file_path, line_number, message = match.groups()
        diagnostics.append(
            Diagnostic(
                file=_to_relative_path(file_path, workdir),
                line=int(line_number),
                message=message,
                rule="go-build",
            )
        )

    return diagnostics


# ============================================
# Detectores por linguagem
# ============================================


class Detector:
    """Interface base de um detector de análise estática."""

    name: str = ""
    extensions: tuple[str, ...] = ()

    def matches(self, file_path: str) -> bool:
        """Verifica se o detector cobre a extensão do arquivo."""
        return file_path.endswith(self.extensions)

    def is_available(self, workdir: Path) -> bool:
        """Verifica se a ferramenta está instalada e configurada."""
        raise NotImplementedError

    def run(self, files: list[str], workdir: Path) -> list[Diagnostic]:
        """Executa a ferramenta e retorna os diagnósticos."""
        raise NotImplementedError


class RuffDetector(Detector):
    """Detector Python via ruff (nomes indefinidos)."""

    name = "ruff"
    extensions = (".py",)

    def is_available(self, workdir: Path) -> bool:
        return shutil.which("ruff") is not None

    def run(self, files: list[str], workdir: Path) -> list[Diagnostic]:
        result = _run_command(
            [
                "ruff",
                "check",
                "--select",
                RUFF_RULES,
                "--output-format",
                "json",
                "--no-cache",
                *files,
            ],
            workdir,
        )
        if result is None:
            return []
        return parse_ruff_output(result.stdout, workdir)


class PyflakesDetector(Detector):
    """Detector Python via pyflakes (fallback do ruff)."""

    name = "pyflakes"
    extensions = (".py",)

    def is_available(self, workdir: Path) -> bool:
        return shutil.which("pyflakes") is not None

    def run(self, files: list[str], workdir: Path) -> list[Diagnostic]:
        result = _run_command(["pyflakes", *files], workdir)
        if result is None:
            return []
        return parse_pyflakes_output(result.stdout, workdir)


class TscDetector(Detector):
    """Detector TypeScript via tsc --noEmit (usa o tsconfig do projeto)."""

    name = "tsc"
    extensions = (".ts", ".tsx")

    def is_available(self, workdir: Path) -> bool:
        has_config = (workdir / "tsconfig.json").is_file()
        return has_config and _node_bin("tsc", workdir) is not None

    def run(self, files: list[str], workdir: Path) -> list[Diagnostic]:
        tsc = _node_bin("tsc", workdir)
        if tsc is None:
            return []

        # tsc analisa o projeto inteiro (tsconfig); filtramos para os
        # arquivos do diff depois
        result = _run_command([tsc, "--noEmit", "--pretty", "false"], workdir)
        if result is None:
            return []

        target_files = set(files)
        return [
            d
            for d in parse_tsc_output(result.stdout, workdir)
            if d.file in target_files
        ]


class EslintDetector(Detector):
    """Detector JavaScript/TypeScript via eslint (usa a config do projeto)."""

    name = "eslint"
    extensions = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx")

    def is_available(self, workdir: Path) -> bool:
        if _node_bin("eslint", workdir) is None:
            return False
        return self._has_config(workdir)

    def _has_config(self, workdir: Path) -> bool:
        """Verifica se o projeto tem configuração de eslint."""
        config_patterns = ("eslint.config.*", ".eslintrc", ".eslintrc.*")
        for config_pattern in config_patterns:
            if any(workdir.glob(config_pattern)):
                return True

        package_json = workdir / "package.json"
        if package_json.is_file():
            try:
                package = json.loads(package_json.read_text(encoding="utf-8"))
                return "eslintConfig" in package
            except (json.JSONDecodeError, OSError):
                return False

        return False

    def run(self, files: list[str], workdir: Path) -> list[Diagnostic]:
        eslint = _node_bin("eslint", workdir)
        if eslint is None:
            return []

        result = _run_command([eslint, "--format", "json", *files], workdir)
        # Exit code 0 = sem erros, 1 = erros de lint; >1 = falha de execução
        if result is None or result.returncode > 1:
            return []

        return parse_eslint_output(result.stdout, workdir)


class GoBuildDetector(Detector):
    """Detector Go via go build (erros de compilação)."""

    name = "go-build"
    extensions = (".go",)

    def is_available(self, workdir: Path) -> bool:
        has_module = (workdir / "go.mod").is_file()
        return has_module and shutil.which("go") is not None

    def run(self, files: list[str], workdir: Path) -> list[Diagnostic]:
        # go build compila o módulo inteiro; filtramos para os arquivos
        # do diff depois
        result = _run_command(["go", "build", "./..."], workdir)
        if result is None:
            return []

        target_files = set(files)
        return [
            d
            for d in parse_go_output(result.stderr, workdir)
            if d.file in target_files
        ]


# Ordem importa: o primeiro detector disponível que cobre a extensão
# do arquivo é o escolhido (ex: .ts vai para tsc; eslint é fallback)
DETECTOR_REGISTRY: tuple[Detector, ...] = (
    RuffDetector(),
    PyflakesDetector(),
    TscDetector(),
    EslintDetector(),
    GoBuildDetector(),
)


# ============================================
# Orquestração
# ============================================


def _get_added_lines_by_file(diff_files: list[DiffFile]) -> dict[str, set[int]]:
    """Mapeia cada arquivo para o conjunto de linhas adicionadas no diff.

    Args:
        diff_files: Arquivos parseados do diff

    Returns:
        Dicionário {caminho do arquivo: números das linhas adicionadas}
    """
    lines_by_file: dict[str, set[int]] = {}

    for diff_file in diff_files:
        if diff_file.is_deleted:
            continue

        added_lines: set[int] = set()
        for hunk in diff_file.hunks:
            for line in hunk.added_lines:
                added_lines.add(line.line_number)

        if added_lines:
            lines_by_file[diff_file.path] = added_lines

    return lines_by_file


def _route_files_to_detectors(
    files: list[str], workdir: Path
) -> dict[Detector, list[str]]:
    """Atribui cada arquivo ao primeiro detector disponível que o cobre.

    Args:
        files: Caminhos relativos dos arquivos modificados
        workdir: Diretório raiz do repositório

    Returns:
        Dicionário {detector: arquivos atribuídos}
    """
    availability: dict[str, bool] = {}
    routing: dict[Detector, list[str]] = {}

    for file_path in files:
        for detector in DETECTOR_REGISTRY:
            if not detector.matches(file_path):
                continue

            # Cacheia a checagem de disponibilidade por detector
            if detector.name not in availability:
                availability[detector.name] = detector.is_available(workdir)

            if availability[detector.name]:
                routing.setdefault(detector, []).append(file_path)
                break

    return routing


def _build_finding(diagnostic: Diagnostic, detector_name: str) -> Finding:
    """Cria um Finding a partir de um diagnóstico do detector.

    Args:
        diagnostic: Diagnóstico da ferramenta
        detector_name: Nome do detector que gerou o diagnóstico

    Returns:
        Finding com severidade CRITICAL e confidence 10
    """
    return Finding(
        file=diagnostic.file,
        line=diagnostic.line,
        severity=Severity.CRITICAL,
        category=Category.BUG,
        title=f"Erro detectado por análise estática ({diagnostic.rule})",
        description=(
            f"{diagnostic.message}. Detectado deterministicamente pela "
            f"ferramenta {detector_name} — erros deste tipo causam falha "
            "em compilação ou crash em tempo de execução."
        ),
        suggestion=(
            "Verifique se o nome está declarado, importado ou se há um typo. "
            "Se algo foi renomeado, atualize todos os usos."
        ),
        confidence=10,
    )


def run_static_analysis(
    diff_files: list[DiffFile],
    workdir: Optional[Path] = None,
) -> list[Finding]:
    """Roda análise estática nos arquivos modificados do diff.

    Roteia cada arquivo para o detector adequado à sua linguagem (ruff/
    pyflakes para Python, tsc/eslint para JS/TS, go build para Go). Se
    nenhuma ferramenta estiver instalada, retorna lista vazia sem erro.

    Apenas diagnósticos em linhas ADICIONADAS no diff são reportados,
    evitando ruído de problemas pré-existentes no código.

    Args:
        diff_files: Arquivos parseados do diff
        workdir: Diretório do repositório (default: diretório atual)

    Returns:
        Lista de findings determinísticos (confidence 10)
    """
    workdir = workdir or Path.cwd()

    added_lines_by_file = _get_added_lines_by_file(diff_files)

    # Seleciona apenas arquivos que existem no working tree
    existing_files = [
        path for path in added_lines_by_file if (workdir / path).is_file()
    ]

    if not existing_files:
        return []

    findings: list[Finding] = []
    seen: set[tuple[str, int, str]] = set()

    for detector, files in _route_files_to_detectors(existing_files, workdir).items():
        for diagnostic in detector.run(files, workdir):
            # Reporta apenas diagnósticos em linhas adicionadas pelo diff
            if diagnostic.line not in added_lines_by_file.get(diagnostic.file, set()):
                continue

            # Dedupe entre detectores (ex: tsc e eslint no mesmo arquivo)
            key = (diagnostic.file, diagnostic.line, diagnostic.rule)
            if key in seen:
                continue
            seen.add(key)

            findings.append(_build_finding(diagnostic, detector.name))

    return findings
