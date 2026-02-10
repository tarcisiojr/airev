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

    Args:
        diff_files: Lista de arquivos parseados do diff

    Returns:
        String formatada com o diff
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

            for line in hunk.removed_lines:
                parts.append(f"-{line.content}")

            for line in hunk.added_lines:
                parts.append(f"+{line.content}")

        parts.append("")

    return "\n".join(parts)


def format_context_for_prompt(context_graphs: list[ContextGraph]) -> str:
    """Formata o contexto dos arquivos para inclusão no prompt.

    Args:
        context_graphs: Lista de grafos de contexto

    Returns:
        String formatada com o contexto
    """
    parts = []
    seen_files: set[str] = set()

    for graph in context_graphs:
        if graph.file in seen_files:
            continue
        seen_files.add(graph.file)

        if graph.file_content:
            parts.append(f"### {graph.file}")
            parts.append("```")
            # Limita o conteúdo para não explodir o prompt
            content_lines = graph.file_content.split("\n")
            if len(content_lines) > 200:
                parts.append("\n".join(content_lines[:200]))
                parts.append(f"... ({len(content_lines) - 200} linhas omitidas)")
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


def build_prompt(
    diff_files: list[DiffFile],
    context_graphs: list[ContextGraph],
    branch: str,
    base: str,
    text_quality: bool = False,
    description: str | None = None,
) -> str:
    """Monta o prompt completo para a IA.

    Args:
        diff_files: Arquivos do diff parseados
        context_graphs: Grafos de contexto com backtracking
        branch: Nome da branch sendo analisada
        base: Nome da branch base
        text_quality: Se True, inclui verificação de ortografia e clareza
        description: Descrição das alterações fornecida pelo usuário

    Returns:
        Prompt completo pronto para enviar à IA
    """
    template = get_prompt_template()

    # Formata cada seção
    diff_section = format_diff_for_prompt(diff_files)
    context_section = format_context_for_prompt(context_graphs)
    references_section = format_references_for_prompt(context_graphs)

    # Schema JSON formatado
    json_schema = json.dumps(JSON_SCHEMA_EXAMPLE, indent=2, ensure_ascii=False)

    # Obtém nome do idioma para o prompt
    lang_code = get_language()
    language_name = LANGUAGE_NAMES.get(lang_code, lang_code)

    # Seção de text-quality (condicional)
    text_quality_section = get_text_quality_section(language_name) if text_quality else ""

    # Seção de descrição das alterações (condicional)
    description_section = get_description_section(description)

    # Substitui placeholders
    prompt = template.replace("{diff}", diff_section)
    prompt = prompt.replace("{context}", context_section)
    prompt = prompt.replace("{references}", references_section)
    prompt = prompt.replace("{json_schema}", json_schema)
    prompt = prompt.replace("{language}", language_name)
    prompt = prompt.replace("{text_quality_section}", text_quality_section)
    prompt = prompt.replace("{description}", description_section)

    return prompt
