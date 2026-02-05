"""Testes para o terminal formatter."""

import io

from code_reviewer.formatters.terminal import (
    format_finding,
    format_header,
    format_result,
    format_severity,
    format_summary,
)
from code_reviewer.models import Category, Finding, ReviewResult, ReviewSummary, Severity


class TestFormatSeverity:
    """Testes para função format_severity."""

    def test_critical_contem_texto(self):
        result = format_severity(Severity.CRITICAL)
        assert "CRITICAL" in result

    def test_warning_contem_texto(self):
        result = format_severity(Severity.WARNING)
        assert "WARNING" in result

    def test_info_contem_texto(self):
        result = format_severity(Severity.INFO)
        assert "INFO" in result


class TestFormatFinding:
    """Testes para função format_finding."""

    def test_finding_completo(self):
        finding = Finding(
            file="test.py",
            line=42,
            severity=Severity.CRITICAL,
            category=Category.SECURITY,
            title="SQL Injection",
            description="Concatenação de SQL perigosa",
            suggestion="Use prepared statements",
            code_snippet="query = f'SELECT * FROM {table}'",
        )

        result = format_finding(finding)

        assert "test.py:42" in result
        assert "SQL Injection" in result
        assert "Concatenação de SQL perigosa" in result
        assert "Use prepared statements" in result

    def test_finding_sem_snippet(self):
        finding = Finding(
            file="app.py",
            line=10,
            severity=Severity.WARNING,
            category=Category.PERFORMANCE,
            title="N+1 Query",
            description="Query em loop",
            suggestion="",
            code_snippet="",
        )

        result = format_finding(finding)

        assert "app.py:10" in result
        assert "N+1 Query" in result


class TestFormatHeader:
    """Testes para função format_header."""

    def test_contem_branch(self):
        result = ReviewResult(
            branch="feature/test",
            base="main",
            files_analyzed=3,
            findings=[],
            summary=ReviewSummary(total=0, critical=0, warning=0, info=0),
        )

        header = format_header(result)

        assert "feature/test" in header
        assert "main" in header
        assert "3" in header


class TestFormatSummary:
    """Testes para função format_summary."""

    def test_sem_findings(self):
        result = ReviewResult(
            branch="branch",
            base="main",
            files_analyzed=1,
            findings=[],
            summary=ReviewSummary(total=0, critical=0, warning=0, info=0),
        )

        summary = format_summary(result)

        assert "Nenhum problema encontrado" in summary

    def test_com_findings(self):
        result = ReviewResult(
            branch="branch",
            base="main",
            files_analyzed=1,
            findings=[],
            summary=ReviewSummary(total=5, critical=2, warning=2, info=1),
        )

        summary = format_summary(result)

        assert "5" in summary
        assert "2" in summary  # critical e warning


class TestFormatResult:
    """Testes para função format_result."""

    def test_resultado_completo(self):
        findings = [
            Finding(
                file="a.py",
                line=10,
                severity=Severity.CRITICAL,
                category=Category.SECURITY,
                title="Bug 1",
                description="Desc 1",
                suggestion="",
                code_snippet="",
            ),
            Finding(
                file="a.py",
                line=20,
                severity=Severity.WARNING,
                category=Category.BUG,
                title="Bug 2",
                description="Desc 2",
                suggestion="",
                code_snippet="",
            ),
            Finding(
                file="b.py",
                line=5,
                severity=Severity.INFO,
                category=Category.PERFORMANCE,
                title="Bug 3",
                description="Desc 3",
                suggestion="",
                code_snippet="",
            ),
        ]

        result = ReviewResult(
            branch="feature/x",
            base="main",
            files_analyzed=2,
            findings=findings,
            summary=ReviewSummary(total=3, critical=1, warning=1, info=1),
        )

        output = io.StringIO()
        format_result(result, output)
        text = output.getvalue()

        # Verifica que contém os elementos principais
        assert "feature/x" in text
        assert "a.py" in text
        assert "b.py" in text
        assert "Bug 1" in text
        assert "Bug 2" in text
        assert "Bug 3" in text

    def test_resultado_vazio(self):
        result = ReviewResult(
            branch="clean",
            base="main",
            files_analyzed=1,
            findings=[],
            summary=ReviewSummary(total=0, critical=0, warning=0, info=0),
        )

        output = io.StringIO()
        format_result(result, output)
        text = output.getvalue()

        assert "Nenhum problema encontrado" in text

    def test_com_raw_response(self):
        result = ReviewResult(
            branch="test",
            base="main",
            files_analyzed=1,
            findings=[],
            summary=ReviewSummary(total=0, critical=0, warning=0, info=0),
            raw_response="Resposta da IA em texto livre",
        )

        output = io.StringIO()
        format_result(result, output)
        text = output.getvalue()

        assert "Resposta raw" in text
        assert "Resposta da IA em texto livre" in text
