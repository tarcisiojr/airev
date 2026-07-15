"""Testes para o módulo de análise estática."""

import shutil

import pytest

from code_reviewer.models import Category, DiffFile, DiffHunk, DiffLine, Severity
from code_reviewer.static_analysis import (
    _get_added_lines_by_file,
    _to_relative_path,
    parse_eslint_output,
    parse_go_output,
    parse_pyflakes_output,
    parse_ruff_output,
    parse_tsc_output,
    run_static_analysis,
)


def _make_diff_file(path: str, added_lines: list[int], is_deleted: bool = False) -> DiffFile:
    """Cria um DiffFile de teste com as linhas adicionadas informadas."""
    hunk = DiffHunk(
        start_line_old=1,
        start_line_new=1,
        added_lines=[
            DiffLine(line_number=n, content="x", is_addition=True)
            for n in added_lines
        ],
    )
    return DiffFile(path=path, hunks=[hunk], is_deleted=is_deleted)


class TestGetAddedLinesByFile:
    """Testes para o mapeamento de linhas adicionadas."""

    def test_mapeia_linhas_adicionadas(self):
        diff_files = [_make_diff_file("app.py", [3, 5])]
        result = _get_added_lines_by_file(diff_files)
        assert result == {"app.py": {3, 5}}

    def test_ignora_arquivos_deletados(self):
        diff_files = [_make_diff_file("removido.py", [1], is_deleted=True)]
        assert _get_added_lines_by_file(diff_files) == {}

    def test_ignora_arquivos_sem_adicoes(self):
        diff_files = [DiffFile(path="vazio.py", hunks=[])]
        assert _get_added_lines_by_file(diff_files) == {}


class TestToRelativePath:
    """Testes para normalização de caminhos."""

    def test_converte_absoluto_para_relativo(self, tmp_path):
        absoluto = str(tmp_path / "src" / "app.py")
        assert _to_relative_path(absoluto, tmp_path) == "src/app.py"

    def test_mantem_relativo(self, tmp_path):
        assert _to_relative_path("src/app.py", tmp_path) == "src/app.py"

    def test_absoluto_fora_do_workdir(self, tmp_path):
        assert _to_relative_path("/outro/lugar/x.py", tmp_path) == "/outro/lugar/x.py"


class TestParseRuffOutput:
    """Testes do parser de saída do ruff."""

    def test_parseia_diagnostico(self, tmp_path):
        stdout = (
            '[{"code": "F821", "filename": "app.py", '
            '"location": {"row": 3}, "message": "Undefined name `foo`"}]'
        )
        diags = parse_ruff_output(stdout, tmp_path)
        assert len(diags) == 1
        assert diags[0].file == "app.py"
        assert diags[0].line == 3
        assert diags[0].rule == "F821"

    def test_ignora_regras_nao_selecionadas(self, tmp_path):
        stdout = (
            '[{"code": "E501", "filename": "app.py", '
            '"location": {"row": 1}, "message": "Line too long"}]'
        )
        assert parse_ruff_output(stdout, tmp_path) == []

    def test_json_invalido_retorna_vazio(self, tmp_path):
        assert parse_ruff_output("não é json", tmp_path) == []


class TestParsePyflakesOutput:
    """Testes do parser de saída do pyflakes."""

    def test_parseia_nome_indefinido(self, tmp_path):
        stdout = "app.py:5:12: undefined name 'valor'"
        diags = parse_pyflakes_output(stdout, tmp_path)
        assert len(diags) == 1
        assert diags[0].file == "app.py"
        assert diags[0].line == 5

    def test_ignora_mensagens_de_estilo(self, tmp_path):
        stdout = "app.py:1:1: 'os' imported but unused"
        assert parse_pyflakes_output(stdout, tmp_path) == []


class TestParseEslintOutput:
    """Testes do parser de saída do eslint."""

    def test_parseia_no_undef(self, tmp_path):
        stdout = (
            '[{"filePath": "src/app.js", "messages": ['
            '{"ruleId": "no-undef", "severity": 2, '
            '"message": "\'foo\' is not defined.", "line": 7}]}]'
        )
        diags = parse_eslint_output(stdout, tmp_path)
        assert len(diags) == 1
        assert diags[0].file == "src/app.js"
        assert diags[0].line == 7
        assert diags[0].rule == "no-undef"

    def test_ignora_regras_de_estilo(self, tmp_path):
        stdout = (
            '[{"filePath": "src/app.js", "messages": ['
            '{"ruleId": "semi", "severity": 2, '
            '"message": "Missing semicolon.", "line": 2}]}]'
        )
        assert parse_eslint_output(stdout, tmp_path) == []

    def test_ignora_warnings(self, tmp_path):
        stdout = (
            '[{"filePath": "src/app.js", "messages": ['
            '{"ruleId": "no-undef", "severity": 1, '
            '"message": "aviso", "line": 2}]}]'
        )
        assert parse_eslint_output(stdout, tmp_path) == []

    def test_inclui_erros_fatais(self, tmp_path):
        stdout = (
            '[{"filePath": "src/app.js", "messages": ['
            '{"ruleId": null, "fatal": true, "severity": 2, '
            '"message": "Parsing error: Unexpected token", "line": 9}]}]'
        )
        diags = parse_eslint_output(stdout, tmp_path)
        assert len(diags) == 1
        assert diags[0].rule == "fatal"


class TestParseTscOutput:
    """Testes do parser de saída do tsc."""

    def test_parseia_erro_de_compilacao(self, tmp_path):
        stdout = "src/app.ts(12,5): error TS2304: Cannot find name 'foo'."
        diags = parse_tsc_output(stdout, tmp_path)
        assert len(diags) == 1
        assert diags[0].file == "src/app.ts"
        assert diags[0].line == 12
        assert diags[0].rule == "TS2304"

    def test_ignora_linhas_sem_erro(self, tmp_path):
        assert parse_tsc_output("Compilação concluída\n", tmp_path) == []


class TestParseGoOutput:
    """Testes do parser de saída do go build."""

    def test_parseia_erro_de_compilacao(self, tmp_path):
        stderr = "main.go:15:2: undefined: valorInexistente"
        diags = parse_go_output(stderr, tmp_path)
        assert len(diags) == 1
        assert diags[0].file == "main.go"
        assert diags[0].line == 15

    def test_ignora_linhas_de_pacote(self, tmp_path):
        stderr = "# exemplo.com/meupacote"
        assert parse_go_output(stderr, tmp_path) == []


class TestRunStaticAnalysis:
    """Testes de integração com o linter real."""

    def test_sem_arquivos_python_retorna_vazio(self, tmp_path):
        diff_files = [_make_diff_file("app.js", [1])]
        assert run_static_analysis(diff_files, tmp_path) == []

    def test_arquivo_inexistente_retorna_vazio(self, tmp_path):
        diff_files = [_make_diff_file("nao_existe.py", [1])]
        assert run_static_analysis(diff_files, tmp_path) == []

    def test_sem_linter_disponivel_retorna_vazio(self, tmp_path, monkeypatch):
        (tmp_path / "app.py").write_text("print(variavel_indefinida)\n")
        diff_files = [_make_diff_file("app.py", [1])]

        monkeypatch.setattr(shutil, "which", lambda _: None)
        assert run_static_analysis(diff_files, tmp_path) == []

    @pytest.mark.skipif(
        not (shutil.which("ruff") or shutil.which("pyflakes")),
        reason="Nenhum linter (ruff/pyflakes) instalado",
    )
    def test_detecta_variavel_indefinida(self, tmp_path):
        # Linha 2 usa uma variável que não existe
        (tmp_path / "app.py").write_text(
            "def processar():\n    return valor_inexistente\n"
        )
        diff_files = [_make_diff_file("app.py", [2])]

        findings = run_static_analysis(diff_files, tmp_path)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.file == "app.py"
        assert finding.line == 2
        assert finding.severity == Severity.CRITICAL
        assert finding.category == Category.BUG
        assert finding.confidence == 10

    @pytest.mark.skipif(
        not (shutil.which("ruff") or shutil.which("pyflakes")),
        reason="Nenhum linter (ruff/pyflakes) instalado",
    )
    def test_ignora_problema_em_linha_nao_adicionada(self, tmp_path):
        # O problema está na linha 2, mas o diff só adicionou a linha 1
        (tmp_path / "app.py").write_text(
            "def processar():\n    return valor_inexistente\n"
        )
        diff_files = [_make_diff_file("app.py", [1])]

        assert run_static_analysis(diff_files, tmp_path) == []

    @pytest.mark.skipif(
        not (shutil.which("ruff") or shutil.which("pyflakes")),
        reason="Nenhum linter (ruff/pyflakes) instalado",
    )
    def test_codigo_valido_sem_findings(self, tmp_path):
        (tmp_path / "app.py").write_text(
            "def processar(valor):\n    return valor * 2\n"
        )
        diff_files = [_make_diff_file("app.py", [1, 2])]

        assert run_static_analysis(diff_files, tmp_path) == []
