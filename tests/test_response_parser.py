"""Testes para o response_parser."""

import json

from code_reviewer.models import Category, Severity
from code_reviewer.response_parser import (
    extract_json_by_braces,
    extract_json_from_markdown,
    normalize_category,
    normalize_severity,
    parse_finding,
    parse_response,
)


class TestExtractJsonFromMarkdown:
    """Testes para função extract_json_from_markdown."""

    def test_extrai_json_de_bloco_markdown(self):
        text = """
Aqui está a análise:

```json
{"key": "value"}
```

Fim da análise.
"""
        result = extract_json_from_markdown(text)
        assert result == '{"key": "value"}'

    def test_extrai_json_sem_tipo(self):
        text = """
```
{"key": "value"}
```
"""
        result = extract_json_from_markdown(text)
        assert result == '{"key": "value"}'

    def test_retorna_none_sem_bloco(self):
        text = "Texto simples sem bloco JSON"
        result = extract_json_from_markdown(text)
        assert result is None


class TestExtractJsonByBraces:
    """Testes para função extract_json_by_braces."""

    def test_extrai_json_simples(self):
        text = 'Prefixo {"key": "value"} sufixo'
        result = extract_json_by_braces(text)
        assert result == '{"key": "value"}'

    def test_extrai_json_aninhado(self):
        text = '{"outer": {"inner": 123}}'
        result = extract_json_by_braces(text)
        assert result == '{"outer": {"inner": 123}}'

    def test_ignora_chaves_em_strings(self):
        text = '{"text": "{ não conta }"}'
        result = extract_json_by_braces(text)
        data = json.loads(result)
        assert data["text"] == "{ não conta }"

    def test_retorna_none_sem_json(self):
        text = "Texto sem JSON"
        result = extract_json_by_braces(text)
        assert result is None


class TestNormalizeSeverity:
    """Testes para função normalize_severity."""

    def test_critical_direto(self):
        assert normalize_severity("CRITICAL") == Severity.CRITICAL

    def test_high_para_critical(self):
        assert normalize_severity("HIGH") == Severity.CRITICAL

    def test_warning_direto(self):
        assert normalize_severity("WARNING") == Severity.WARNING

    def test_medium_para_warning(self):
        assert normalize_severity("MEDIUM") == Severity.WARNING

    def test_info_direto(self):
        assert normalize_severity("INFO") == Severity.INFO

    def test_low_para_info(self):
        assert normalize_severity("LOW") == Severity.INFO

    def test_desconhecido_para_info(self):
        assert normalize_severity("UNKNOWN") == Severity.INFO

    def test_case_insensitive(self):
        assert normalize_severity("critical") == Severity.CRITICAL
        assert normalize_severity("CrItIcAl") == Severity.CRITICAL


class TestNormalizeCategory:
    """Testes para função normalize_category."""

    def test_security(self):
        assert normalize_category("security") == Category.SECURITY
        assert normalize_category("vulnerability") == Category.SECURITY

    def test_performance(self):
        assert normalize_category("performance") == Category.PERFORMANCE
        assert normalize_category("perf") == Category.PERFORMANCE

    def test_bug(self):
        assert normalize_category("bug") == Category.BUG
        assert normalize_category("error") == Category.BUG

    def test_resource_leak(self):
        assert normalize_category("resource-leak") == Category.RESOURCE_LEAK
        assert normalize_category("memory") == Category.RESOURCE_LEAK

    def test_desconhecido_para_bug(self):
        assert normalize_category("unknown") == Category.BUG


class TestParseFinding:
    """Testes para função parse_finding."""

    def test_finding_completo(self):
        data = {
            "file": "test.py",
            "line": 42,
            "severity": "CRITICAL",
            "category": "security",
            "title": "SQL Injection",
            "description": "Concatenação de SQL",
            "suggestion": "Use prepared statements",
            "code_snippet": "query = f'SELECT * FROM {table}'",
        }

        finding = parse_finding(data)

        assert finding is not None
        assert finding.file == "test.py"
        assert finding.line == 42
        assert finding.severity == Severity.CRITICAL
        assert finding.category == Category.SECURITY
        assert finding.title == "SQL Injection"

    def test_finding_com_campos_faltando(self):
        data = {
            "file": "test.py",
            "line": 10,
            "severity": "WARNING",
            "category": "bug",
            "title": "Problema",
        }

        finding = parse_finding(data)

        assert finding is not None
        assert finding.description == ""
        assert finding.suggestion == ""

    def test_finding_com_valores_invalidos(self):
        data = {
            "file": "test.py",
            "line": "not a number",  # inválido
        }

        # Deve tratar graciosamente
        result = parse_finding(data)
        # Pode retornar None ou converter o valor
        assert result is None or result.file == "test.py"


class TestParseResponse:
    """Testes para função parse_response."""

    def test_json_valido_direto(self):
        response = json.dumps(
            {
                "review": {
                    "findings": [
                        {
                            "file": "test.py",
                            "line": 10,
                            "severity": "WARNING",
                            "category": "performance",
                            "title": "N+1 Query",
                            "description": "Query em loop",
                            "suggestion": "Use batch",
                            "code_snippet": "for x in xs: db.get(x)",
                        }
                    ]
                }
            }
        )

        result = parse_response(response, "feature/test", "main", 1)

        assert len(result.findings) == 1
        assert result.findings[0].title == "N+1 Query"
        assert result.summary.warning == 1
        assert result.raw_response is None

    def test_json_em_markdown(self):
        response = """
Aqui está minha análise:

```json
{
  "findings": [
    {
      "file": "app.py",
      "line": 5,
      "severity": "INFO",
      "category": "bug",
      "title": "Comentário desnecessário",
      "description": "Descrição aqui"
    }
  ]
}
```

Espero que ajude!
"""
        result = parse_response(response, "feature/x", "main", 1)

        assert len(result.findings) == 1
        assert result.findings[0].severity == Severity.INFO

    def test_json_parcial_em_texto(self):
        response = 'Olha o resultado: {"findings": []} - é isso!'

        result = parse_response(response, "branch", "main", 0)

        assert len(result.findings) == 0

    def test_texto_sem_json_fallback(self):
        response = "Não encontrei nenhum problema no código."

        result = parse_response(response, "branch", "main", 1)

        assert len(result.findings) == 1
        assert result.findings[0].title == "Resposta não estruturada"
        assert result.raw_response == response

    def test_calcula_summary_corretamente(self):
        response = json.dumps(
            {
                "findings": [
                    {"file": "a.py", "line": 1, "severity": "CRITICAL", "category": "security", "title": "1"},
                    {"file": "b.py", "line": 2, "severity": "CRITICAL", "category": "security", "title": "2"},
                    {"file": "c.py", "line": 3, "severity": "WARNING", "category": "bug", "title": "3"},
                    {"file": "d.py", "line": 4, "severity": "INFO", "category": "bug", "title": "4"},
                ]
            }
        )

        result = parse_response(response, "branch", "main", 4)

        assert result.summary.total == 4
        assert result.summary.critical == 2
        assert result.summary.warning == 1
        assert result.summary.info == 1
