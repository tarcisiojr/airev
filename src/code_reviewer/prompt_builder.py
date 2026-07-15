"""Prompt Builder - Monta o prompt para a IA."""

import json
from pathlib import Path
from .models import ContextGraph, DiffFile
from .i18n import get_language

# Mapeamento de código de idioma para nome legível
LANGUAGE_NAMES = {
    "pt-br": "Português Brasileiro",
    "en": "English",
}

# Passadas do modo --thorough: (nome exibido, instrução de foco).
# Cada passada roda uma chamada de IA dedicada a um grupo de categorias,
# evitando a diluição de atenção da análise em passada única.
THOROUGH_PASSES: list[tuple[str, str]] = [
    (
        "security",
        "Segurança: injeção (SQL/XSS/command/path traversal), SSRF, secrets "
        "hardcoded, autenticação/autorização, criptografia fraca, "
        "deserialização insegura, exposição de dados, open redirect/CORS/XXE, "
        "ReDoS e upload de arquivos",
    ),
    (
        "performance",
        "Performance: N+1 e queries em loop, complexidade algorítmica, "
        "trabalho redundante em loops, I/O bloqueante em código async, "
        "uso de memória sem limite e regex ineficientes",
    ),
    (
        "bugs",
        "Bugs e robustez: variáveis/nomes indefinidos, acesso a valores "
        "possivelmente nulos, race conditions, off-by-one, tratamento de "
        "erros inadequado, recursos não fechados e breaking changes em APIs",
    ),
]

# Schema JSON de exemplo para o prompt
JSON_SCHEMA_EXAMPLE = {
    "review": {
        "branch": "feature/exemplo",
        "base": "main",
        "files_analyzed": 2,
        "findings": [
            {
                "file": "path/to/file.py",
                "line": 42,
                "severity": "CRITICAL",
                "category": "security",
                "title": "Título curto do problema",
                "description": "Descrição detalhada do problema encontrado",
                "suggestion": "Sugestão de como corrigir",
                "code_snippet": "código problemático",
                "confidence": 9,
            }
        ],
        "good_practices": [
            {
                "file": "path/to/file.py",
                "line": 15,
                "description": "Excelente tratamento de exceções com logging adequado",
            }
        ],
        "summary": {"total": 1, "critical": 1, "warning": 0, "info": 0},
    }
}


def get_prompt_template() -> str:
    """Carrega o template do prompt do arquivo.

    Returns:
        Conteúdo do template como string
    """
    template_path = Path(__file__).parent / "prompts" / "review_system.md"

    if not template_path.exists():
        raise FileNotFoundError(f"Template não encontrado: {template_path}")

    return template_path.read_text(encoding="utf-8")


def format_diff_for_prompt(diff_files: list[DiffFile]) -> str:
    """Formata os arquivos do diff para inclusão no prompt.

    Inclui linhas de contexto (sem prefixo +/-) para dar visibilidade
    da estrutura do código ao redor das mudanças.

    Args:
        diff_files: Lista de arquivos parseados do diff

    Returns:
        String formatada com o diff no formato unificado
    """
    parts = []

    for diff_file in diff_files:
        parts.append(f"### {diff_file.path}")

        if diff_file.is_new:
            parts.append("(arquivo novo)")
        elif diff_file.is_deleted:
            parts.append("(arquivo removido)")

        for hunk in diff_file.hunks:
            if hunk.function_name:
                parts.append(f"\n#### Função: {hunk.function_name}")

            parts.append(f"Linhas {hunk.start_line_new}+:")

            # Combina todas as linhas e ordena por número de linha para
            # manter a ordem original do diff
            all_lines: list[tuple[int, str, str]] = []

            # Linhas removidas (prefixo -)
            for line in hunk.removed_lines:
                all_lines.append((line.line_number, "-", line.content))

            # Linhas adicionadas (prefixo +)
            for line in hunk.added_lines:
                all_lines.append((line.line_number, "+", line.content))

            # Linhas de contexto (prefixo espaço - padrão git diff)
            for line in hunk.context_lines:
                all_lines.append((line.line_number, " ", line.content))

            # Ordena por número de linha
            all_lines.sort(key=lambda x: x[0])

            # Formata cada linha com seu prefixo
            for _, prefix, content in all_lines:
                parts.append(f"{prefix}{content}")

        parts.append("")

    return "\n".join(parts)


# Limites da janela de contexto por arquivo
CONTEXT_FULL_FILE_THRESHOLD = 200  # Arquivos até este tamanho vão inteiros
CONTEXT_HEADER_LINES = 30  # Cabeçalho do arquivo (imports, globals)
CONTEXT_WINDOW = 40  # Linhas ao redor de cada hunk modificado


def _get_hunk_ranges_by_file(
    diff_files: list[DiffFile],
) -> dict[str, list[tuple[int, int]]]:
    """Mapeia cada arquivo para os intervalos de linha dos seus hunks.

    Args:
        diff_files: Arquivos parseados do diff

    Returns:
        Dicionário {caminho: lista de (linha inicial, linha final)}
    """
    ranges: dict[str, list[tuple[int, int]]] = {}

    for diff_file in diff_files:
        file_ranges = []
        for hunk in diff_file.hunks:
            line_numbers = [
                line.line_number
                for line in hunk.added_lines + hunk.context_lines
            ]
            if line_numbers:
                file_ranges.append((min(line_numbers), max(line_numbers)))
            else:
                file_ranges.append((hunk.start_line_new, hunk.start_line_new))

        if file_ranges:
            ranges[diff_file.path] = file_ranges

    return ranges


def _merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Mescla intervalos sobrepostos ou adjacentes.

    Args:
        ranges: Lista de intervalos (início, fim)

    Returns:
        Lista de intervalos mesclados em ordem crescente
    """
    merged: list[tuple[int, int]] = []

    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


def _extract_windowed_content(
    content: str, hunk_ranges: list[tuple[int, int]]
) -> str:
    """Extrai o conteúdo relevante do arquivo centrado nos hunks modificados.

    Arquivos pequenos vão inteiros. Para arquivos grandes, inclui o cabeçalho
    (imports/globals) e janelas ao redor de cada hunk — garantindo que a IA
    veja as definições próximas às mudanças em vez de apenas o início do
    arquivo.

    Args:
        content: Conteúdo completo do arquivo
        hunk_ranges: Intervalos de linha dos hunks modificados

    Returns:
        Conteúdo janelado com marcadores de omissão
    """
    lines = content.split("\n")
    total = len(lines)

    if total <= CONTEXT_FULL_FILE_THRESHOLD:
        return content

    # Cabeçalho (imports/globals) + janela ao redor de cada hunk
    include = [(1, min(CONTEXT_HEADER_LINES, total))]
    for start, end in hunk_ranges:
        include.append(
            (max(1, start - CONTEXT_WINDOW), min(total, end + CONTEXT_WINDOW))
        )

    parts = []
    prev_end = 0
    for start, end in _merge_ranges(include):
        if start > prev_end + 1:
            parts.append(f"... (linhas {prev_end + 1}-{start - 1} omitidas) ...")
        parts.extend(lines[start - 1 : end])
        prev_end = end

    if prev_end < total:
        parts.append(f"... (linhas {prev_end + 1}-{total} omitidas) ...")

    return "\n".join(parts)


def format_context_for_prompt(
    context_graphs: list[ContextGraph],
    diff_files: list[DiffFile] | None = None,
) -> str:
    """Formata o contexto dos arquivos para inclusão no prompt.

    Quando diff_files é fornecido, o conteúdo de arquivos grandes é janelado
    ao redor dos hunks modificados (em vez de truncar nas primeiras linhas).

    Args:
        context_graphs: Lista de grafos de contexto
        diff_files: Arquivos do diff, para centrar as janelas nos hunks

    Returns:
        String formatada com o contexto
    """
    hunk_ranges_by_file = _get_hunk_ranges_by_file(diff_files or [])

    parts = []
    seen_files: set[str] = set()

    for graph in context_graphs:
        if graph.file in seen_files:
            continue
        seen_files.add(graph.file)

        if graph.file_content:
            parts.append(f"### {graph.file}")
            parts.append("```")

            hunk_ranges = hunk_ranges_by_file.get(graph.file)
            if hunk_ranges:
                parts.append(
                    _extract_windowed_content(graph.file_content, hunk_ranges)
                )
            else:
                # Sem hunks conhecidos: mantém o truncamento simples
                content_lines = graph.file_content.split("\n")
                if len(content_lines) > CONTEXT_FULL_FILE_THRESHOLD:
                    parts.append(
                        "\n".join(content_lines[:CONTEXT_FULL_FILE_THRESHOLD])
                    )
                    parts.append(
                        f"... ({len(content_lines) - CONTEXT_FULL_FILE_THRESHOLD}"
                        " linhas omitidas)"
                    )
                else:
                    parts.append(graph.file_content)

            parts.append("```")
            parts.append("")

    return "\n".join(parts)


def format_references_for_prompt(context_graphs: list[ContextGraph]) -> str:
    """Formata as referências (backtracking) para inclusão no prompt.

    Args:
        context_graphs: Lista de grafos de contexto

    Returns:
        String formatada com as referências
    """
    parts = []

    for graph in context_graphs:
        parts.append(f"### Função: `{graph.function_name}` ({graph.file})")
        parts.append("")

        if graph.callers:
            parts.append("**Chamada por:**")
            for caller in graph.callers:
                parts.append(f"- {caller.file}:{caller.line} → `{caller.snippet}`")
            parts.append("")

        if graph.callees:
            parts.append("**Usa:**")
            for callee in graph.callees:
                name = callee.function_name or "?"
                parts.append(f"- `{name}` → {callee.file}:{callee.line}")
            parts.append("")

        if not graph.callers and not graph.callees:
            parts.append("(sem referências encontradas)")
            parts.append("")

    return "\n".join(parts)


def get_description_section(description: str | None) -> str:
    """Retorna a seção de descrição das alterações para o prompt.

    Args:
        description: Descrição fornecida pelo usuário ou None

    Returns:
        String formatada com a seção de descrição ou string vazia
    """
    if not description:
        return ""

    return f"""
## DESCRIÇÃO DAS ALTERAÇÕES

O desenvolvedor forneceu a seguinte descrição sobre as mudanças:

{description}

Use esta informação para contextualizar sua análise. A descrição indica a intenção
do desenvolvedor e pode ajudar a identificar se o código implementa corretamente
o que foi proposto.
"""


def get_text_quality_section(language_name: str) -> str:
    """Retorna a seção de instruções para verificação de qualidade de texto.

    Args:
        language_name: Nome do idioma para verificação

    Returns:
        String com instruções de verificação de texto
    """
    return f"""
## QUALIDADE DE TEXTO

Verifique ortografia e clareza semântica em mensagens voltadas ao usuário,
no idioma **{language_name}**.

### O que verificar:

**Padrões de código:**
- `raise *Error("...")` e `raise *Exception("...")`
- `print("...")` e `console.log("...")`
- Parâmetros nomeados: `message=`, `label=`, `title=`, `description=`, `text=`
- Funções de UI: `flash("...")`, `toast("...")`, `alert("...")`

**Arquivos de i18n:**
- Arquivos em `locales/**/*`
- Arquivos em `i18n/**/*`
- Arquivos `messages.*` e `strings.*`

### O que ignorar:

- Identificadores: snake_case, camelCase, PascalCase
- Termos técnicos: HTTP, JSON, API, SQL, URL, etc.
- Nomes próprios e termos de domínio específico
- Chaves de configuração e variáveis de ambiente

### Formato dos findings:

- Categoria: `text-quality`
- Severidade: sempre `INFO`
- Inclua a correção sugerida no campo `suggestion`
"""


def get_focus_section(focus: str | None) -> str:
    """Retorna a seção de foco para uma passada do modo --thorough.

    Args:
        focus: Instrução de foco da passada ou None (análise completa)

    Returns:
        String formatada com a seção de foco ou string vazia
    """
    if not focus:
        return ""

    return f"""
## FOCO DESTA PASSADA

Esta é uma análise focada EXCLUSIVAMENTE em: **{focus}**.

- Analise o diff inteiro apenas sob esta perspectiva, verificando item a item a checklist correspondente
- NÃO reporte problemas de outras categorias — eles são cobertos em passadas separadas
- Aprofunde: releia cada linha adicionada perguntando "o que pode dar errado nesta dimensão?"
"""


def build_prompt(
    diff_files: list[DiffFile],
    context_graphs: list[ContextGraph],
    branch: str,
    base: str,
    text_quality: bool = False,
    description: str | None = None,
    focus: str | None = None,
) -> str:
    """Monta o prompt completo para a IA.

    Args:
        diff_files: Arquivos do diff parseados
        context_graphs: Grafos de contexto com backtracking
        branch: Nome da branch sendo analisada
        base: Nome da branch base
        text_quality: Se True, inclui verificação de ortografia e clareza
        description: Descrição das alterações fornecida pelo usuário
        focus: Instrução de foco para passadas do modo --thorough

    Returns:
        Prompt completo pronto para enviar à IA
    """
    template = get_prompt_template()

    # Formata cada seção
    diff_section = format_diff_for_prompt(diff_files)
    context_section = format_context_for_prompt(context_graphs, diff_files)
    references_section = format_references_for_prompt(context_graphs)

    # Schema JSON formatado
    json_schema = json.dumps(JSON_SCHEMA_EXAMPLE, indent=2, ensure_ascii=False)

    # Obtém nome do idioma para o prompt
    lang_code = get_language()
    language_name = LANGUAGE_NAMES.get(lang_code, lang_code)

    # Seção de text-quality (condicional)
    text_quality_section = (
        get_text_quality_section(language_name) if text_quality else ""
    )

    # Seção de descrição das alterações (condicional)
    description_section = get_description_section(description)

    # Seção de foco da passada (condicional, modo --thorough)
    focus_section = get_focus_section(focus)

    # Substitui placeholders
    prompt = template.replace("{diff}", diff_section)
    prompt = prompt.replace("{context}", context_section)
    prompt = prompt.replace("{references}", references_section)
    prompt = prompt.replace("{json_schema}", json_schema)
    prompt = prompt.replace("{language}", language_name)
    prompt = prompt.replace("{text_quality_section}", text_quality_section)
    prompt = prompt.replace("{description}", description_section)
    prompt = prompt.replace("{focus_section}", focus_section)

    return prompt
