"""Response Parser - Parseia e valida respostas da IA."""

import json
import re
from typing import Any, Optional

from .models import Category, Finding, ReviewResult, ReviewSummary, Severity


def extract_json_from_markdown(text: str) -> Optional[str]:
    """Extrai JSON de bloco markdown ```json ... ```.

    Args:
        text: Texto que pode conter bloco JSON em markdown

    Returns:
        Conteúdo JSON extraído ou None se não encontrado
    """
    pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return None


def extract_json_by_braces(text: str) -> Optional[str]:
    """Tenta extrair JSON encontrando { ... } balanceado.

    Args:
        text: Texto que pode conter JSON

    Returns:
        Conteúdo JSON extraído ou None se não encontrado
    """
    # Encontra a primeira { e tenta balancear
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i, char in enumerate(text[start:], start):
        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == '"' and not escape:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None


def normalize_severity(value: str) -> Severity:
    """Normaliza valor de severidade para o enum.

    Args:
        value: Valor de severidade (pode estar em formato diferente)

    Returns:
        Enum Severity correspondente
    """
    value_upper = value.upper().strip()

    mapping = {
        "CRITICAL": Severity.CRITICAL,
        "HIGH": Severity.CRITICAL,
        "SEVERE": Severity.CRITICAL,
        "ERROR": Severity.CRITICAL,
        "WARNING": Severity.WARNING,
        "MEDIUM": Severity.WARNING,
        "WARN": Severity.WARNING,
        "INFO": Severity.INFO,
        "LOW": Severity.INFO,
        "NOTE": Severity.INFO,
        "SUGGESTION": Severity.INFO,
    }

    return mapping.get(value_upper, Severity.INFO)


def normalize_category(value: str) -> Category:
    """Normaliza valor de categoria para o enum.

    Args:
        value: Valor de categoria

    Returns:
        Enum Category correspondente
    """
    value_lower = value.lower().strip().replace("_", "-").replace(" ", "-")

    mapping = {
        "security": Category.SECURITY,
        "sec": Category.SECURITY,
        "vulnerability": Category.SECURITY,
        "performance": Category.PERFORMANCE,
        "perf": Category.PERFORMANCE,
        "optimization": Category.PERFORMANCE,
        "bug": Category.BUG,
        "error": Category.BUG,
        "defect": Category.BUG,
        "resource-leak": Category.RESOURCE_LEAK,
        "resource_leak": Category.RESOURCE_LEAK,
        "leak": Category.RESOURCE_LEAK,
        "memory": Category.RESOURCE_LEAK,
    }

    return mapping.get(value_lower, Category.BUG)


def parse_finding(data: dict[str, Any]) -> Optional[Finding]:
    """Parseia um finding do JSON.

    Args:
        data: Dicionário com dados do finding

    Returns:
        Finding parseado ou None se dados inválidos
    """
    try:
        return Finding(
            file=str(data.get("file", "unknown")),
            line=int(data.get("line", 0)),
            severity=normalize_severity(str(data.get("severity", "INFO"))),
            category=normalize_category(str(data.get("category", "bug"))),
            title=str(data.get("title", "Sem título")),
            description=str(data.get("description", "")),
            suggestion=str(data.get("suggestion", "")),
            code_snippet=str(data.get("code_snippet", "")),
        )
    except (ValueError, TypeError):
        return None


def parse_response(
    response: str,
    branch: str,
    base: str,
    files_analyzed: int,
) -> ReviewResult:
    """Parseia a resposta da IA em um ReviewResult.

    Tenta várias estratégias em sequência:
    1. JSON direto
    2. JSON em bloco markdown
    3. JSON por balanceamento de chaves
    4. Fallback para texto raw

    Args:
        response: Resposta da IA como string
        branch: Nome da branch analisada
        base: Nome da branch base
        files_analyzed: Quantidade de arquivos analisados

    Returns:
        ReviewResult com os findings parseados
    """
    json_str = None
    data = None

    # Estratégia 1: JSON direto
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        pass

    # Estratégia 2: JSON em markdown
    if data is None:
        json_str = extract_json_from_markdown(response)
        if json_str:
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                pass

    # Estratégia 3: JSON por balanceamento de chaves
    if data is None:
        json_str = extract_json_by_braces(response)
        if json_str:
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                pass

    # Se encontrou JSON, processa
    if data is not None:
        return _parse_json_response(data, branch, base, files_analyzed)

    # Fallback: retorna texto raw como INFO
    return ReviewResult(
        branch=branch,
        base=base,
        files_analyzed=files_analyzed,
        findings=[
            Finding(
                file="response",
                line=0,
                severity=Severity.INFO,
                category=Category.BUG,
                title="Resposta não estruturada",
                description="A IA retornou texto não formatado como JSON",
                suggestion="Verifique a resposta raw para detalhes",
                code_snippet="",
            )
        ],
        summary=ReviewSummary(total=1, critical=0, warning=0, info=1),
        raw_response=response,
    )


def _parse_json_response(
    data: dict[str, Any],
    branch: str,
    base: str,
    files_analyzed: int,
) -> ReviewResult:
    """Parseia resposta JSON validada.

    Args:
        data: Dados JSON parseados
        branch: Nome da branch
        base: Nome da branch base
        files_analyzed: Quantidade de arquivos

    Returns:
        ReviewResult com dados extraídos
    """
    findings: list[Finding] = []

    # A resposta pode ter estrutura { "review": { ... } } ou direta
    review_data = data.get("review", data)

    # Extrai findings
    findings_data = review_data.get("findings", [])
    if isinstance(findings_data, list):
        for item in findings_data:
            if isinstance(item, dict):
                finding = parse_finding(item)
                if finding:
                    findings.append(finding)

    # Calcula sumário
    critical = sum(1 for f in findings if f.severity == Severity.CRITICAL)
    warning = sum(1 for f in findings if f.severity == Severity.WARNING)
    info = sum(1 for f in findings if f.severity == Severity.INFO)

    return ReviewResult(
        branch=branch,
        base=base,
        files_analyzed=files_analyzed,
        findings=findings,
        summary=ReviewSummary(
            total=len(findings),
            critical=critical,
            warning=warning,
            info=info,
        ),
    )
