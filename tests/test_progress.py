"""Testes para o módulo de progresso com spinners."""

import io
import os
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from code_reviewer.formatters.progress import ProgressReporter, is_ci_environment


class TestIsCiEnvironment:
    """Testes para função is_ci_environment."""

    def test_retorna_true_quando_nao_tty(self):
        """Quando stdout não é TTY, deve retornar True."""
        with patch("sys.stdout.isatty", return_value=False):
            assert is_ci_environment() is True

    def test_retorna_true_quando_ci_var_definida(self):
        """Quando variável CI está definida, deve retornar True."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch.dict(os.environ, {"CI": "true"}):
                assert is_ci_environment() is True

    def test_retorna_true_quando_github_actions(self):
        """Quando GITHUB_ACTIONS está definida, deve retornar True."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
                # Limpa outras variáveis CI que podem estar presentes
                env_clean = {k: v for k, v in os.environ.items()
                            if k not in ["CI", "GITLAB_CI", "JENKINS_URL", "TRAVIS"]}
                env_clean["GITHUB_ACTIONS"] = "true"
                with patch.dict(os.environ, env_clean, clear=True):
                    assert is_ci_environment() is True

    def test_retorna_true_quando_gitlab_ci(self):
        """Quando GITLAB_CI está definida, deve retornar True."""
        with patch("sys.stdout.isatty", return_value=True):
            env_clean = {"GITLAB_CI": "true"}
            with patch.dict(os.environ, env_clean, clear=True):
                assert is_ci_environment() is True

    def test_retorna_true_quando_jenkins(self):
        """Quando JENKINS_URL está definida, deve retornar True."""
        with patch("sys.stdout.isatty", return_value=True):
            env_clean = {"JENKINS_URL": "http://jenkins.local"}
            with patch.dict(os.environ, env_clean, clear=True):
                assert is_ci_environment() is True

    def test_retorna_false_em_terminal_interativo(self):
        """Em terminal interativo sem variáveis CI, deve retornar False."""
        with patch("sys.stdout.isatty", return_value=True):
            # Remove todas as variáveis de CI
            with patch.dict(os.environ, {}, clear=True):
                assert is_ci_environment() is False


class TestProgressReporterInit:
    """Testes para inicialização do ProgressReporter."""

    def test_cria_console_se_nao_fornecido(self):
        """Deve criar Console do rich se não for fornecido."""
        reporter = ProgressReporter()
        assert reporter.console is not None
        assert isinstance(reporter.console, Console)

    def test_usa_console_fornecido(self):
        """Deve usar Console fornecido."""
        console = Console(file=io.StringIO())
        reporter = ProgressReporter(console=console)
        assert reporter.console is console

    def test_enabled_padrao_true(self):
        """Enabled deve ser True por padrão."""
        reporter = ProgressReporter()
        assert reporter.enabled is True

    def test_enabled_pode_ser_false(self):
        """Enabled pode ser configurado para False."""
        reporter = ProgressReporter(enabled=False)
        assert reporter.enabled is False

    def test_force_terminal_true_habilita_animacao(self):
        """force_terminal=True deve habilitar animações."""
        reporter = ProgressReporter(force_terminal=True)
        assert reporter._use_animation is True

    def test_force_terminal_false_desabilita_animacao(self):
        """force_terminal=False deve desabilitar animações."""
        reporter = ProgressReporter(force_terminal=False)
        assert reporter._use_animation is False


class TestProgressReporterStatus:
    """Testes para método status() do ProgressReporter."""

    def test_status_nao_faz_nada_quando_disabled(self):
        """Quando disabled, status() não deve fazer nada."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=True)
        reporter = ProgressReporter(console=console, enabled=False)

        with reporter.status("Testando..."):
            pass

        assert output.getvalue() == ""

    def test_status_exibe_mensagem_em_modo_ci(self):
        """Em modo CI (sem animação), deve exibir mensagem simples."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, force_terminal=False)

        with reporter.status("Processando..."):
            pass

        assert "Processando..." in output.getvalue()

    def test_status_retorna_none_em_modo_ci(self):
        """Em modo CI, status() deve retornar None."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, force_terminal=False)

        with reporter.status("Testando...") as status:
            assert status is None


class TestProgressReporterStep:
    """Testes para método step() do ProgressReporter."""

    def test_step_exibe_mensagem(self):
        """step() deve exibir mensagem com prefixo."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        reporter.step("Etapa 1")

        assert "Etapa 1" in output.getvalue()

    def test_step_nao_faz_nada_quando_disabled(self):
        """Quando disabled, step() não deve fazer nada."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, enabled=False)

        reporter.step("Etapa 1")

        assert output.getvalue() == ""


class TestProgressReporterSuccess:
    """Testes para método success() do ProgressReporter."""

    def test_success_exibe_mensagem_com_check(self):
        """success() deve exibir mensagem com símbolo de sucesso."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        reporter.success("Concluído")

        result = output.getvalue()
        assert "Concluído" in result
        assert "✓" in result

    def test_success_nao_faz_nada_quando_disabled(self):
        """Quando disabled, success() não deve fazer nada."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, enabled=False)

        reporter.success("Concluído")

        assert output.getvalue() == ""


class TestProgressReporterInfo:
    """Testes para método info() do ProgressReporter."""

    def test_info_exibe_mensagem(self):
        """info() deve exibir mensagem informativa."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        reporter.info("Informação")

        result = output.getvalue()
        assert "Informação" in result
        assert "ℹ" in result

    def test_info_nao_faz_nada_quando_disabled(self):
        """Quando disabled, info() não deve fazer nada."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, enabled=False)

        reporter.info("Informação")

        assert output.getvalue() == ""


class TestProgressReporterWarning:
    """Testes para método warning() do ProgressReporter."""

    def test_warning_exibe_mensagem(self):
        """warning() deve exibir mensagem de aviso."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        reporter.warning("Atenção")

        result = output.getvalue()
        assert "Atenção" in result
        assert "⚠" in result

    def test_warning_nao_faz_nada_quando_disabled(self):
        """Quando disabled, warning() não deve fazer nada."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, enabled=False)

        reporter.warning("Atenção")

        assert output.getvalue() == ""


class TestProgressReporterError:
    """Testes para método error() do ProgressReporter."""

    def test_error_exibe_mensagem_em_stderr(self, capsys):
        """error() deve exibir mensagem de erro em stderr."""
        reporter = ProgressReporter(force_terminal=False)

        reporter.error("Falhou")

        captured = capsys.readouterr()
        assert "Falhou" in captured.err
        assert "✗" in captured.err

    def test_error_exibido_mesmo_quando_disabled(self, capsys):
        """Erros aparecem mesmo com reporter desabilitado (--json-output).

        Uma falha silenciosa faria um review que nem executou parecer
        'código aprovado'.
        """
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, enabled=False)

        reporter.error("Falhou")

        # Nada no console padrão (stdout permanece parseável)...
        assert output.getvalue() == ""
        # ...mas o erro aparece em stderr
        captured = capsys.readouterr()
        assert "Falhou" in captured.err


class TestProgressReporterPrint:
    """Testes para método print() do ProgressReporter."""

    def test_print_exibe_mensagem(self):
        """print() deve exibir mensagem simples."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        reporter.print("Mensagem")

        assert "Mensagem" in output.getvalue()

    def test_print_aceita_mensagem_vazia(self):
        """print() deve aceitar mensagem vazia."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        reporter.print()  # Não deve lançar exceção

    def test_print_nao_faz_nada_quando_disabled(self):
        """Quando disabled, print() não deve fazer nada."""
        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, enabled=False)

        reporter.print("Mensagem")

        assert output.getvalue() == ""


class TestProgressReporterShowDiffFiles:
    """Testes para método show_diff_files() do ProgressReporter."""

    def test_exibe_arquivos_com_contagem_linhas(self):
        """Deve exibir cada arquivo com contagem de linhas adicionadas/removidas."""
        from code_reviewer.models import DiffFile, DiffHunk, DiffLine

        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        files = [
            DiffFile(
                path="src/main.py",
                hunks=[
                    DiffHunk(
                        start_line_old=1,
                        start_line_new=1,
                        added_lines=[
                            DiffLine(line_number=10, content="novo", is_addition=True),
                            DiffLine(line_number=11, content="código", is_addition=True),
                        ],
                        removed_lines=[
                            DiffLine(line_number=5, content="antigo", is_addition=False),
                        ],
                    )
                ],
            ),
        ]

        reporter.show_diff_files(files)

        result = output.getvalue()
        assert "src/main.py" in result
        assert "+2" in result
        assert "-1" in result

    def test_exibe_arquivo_novo_com_indicador(self):
        """Arquivos novos devem ter indicador +."""
        from code_reviewer.models import DiffFile

        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        files = [DiffFile(path="novo_arquivo.py", is_new=True, hunks=[])]

        reporter.show_diff_files(files)

        result = output.getvalue()
        assert "novo_arquivo.py" in result

    def test_exibe_arquivo_deletado_com_indicador(self):
        """Arquivos deletados devem ter indicador -."""
        from code_reviewer.models import DiffFile

        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        files = [DiffFile(path="removido.py", is_deleted=True, hunks=[])]

        reporter.show_diff_files(files)

        result = output.getvalue()
        assert "removido.py" in result

    def test_nao_faz_nada_quando_disabled(self):
        """Quando disabled, não deve fazer nada."""
        from code_reviewer.models import DiffFile

        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, enabled=False)

        files = [DiffFile(path="teste.py", hunks=[])]

        reporter.show_diff_files(files)

        assert output.getvalue() == ""


class TestProgressReporterShowDiffSummary:
    """Testes para método show_diff_summary() do ProgressReporter."""

    def test_exibe_resumo_com_totais(self):
        """Deve exibir resumo com total de arquivos e linhas."""
        from code_reviewer.models import DiffFile, DiffHunk, DiffLine

        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        files = [
            DiffFile(
                path="a.py",
                hunks=[
                    DiffHunk(
                        start_line_old=1,
                        start_line_new=1,
                        added_lines=[
                            DiffLine(line_number=1, content="a", is_addition=True),
                            DiffLine(line_number=2, content="b", is_addition=True),
                        ],
                        removed_lines=[],
                    )
                ],
            ),
            DiffFile(
                path="b.py",
                hunks=[
                    DiffHunk(
                        start_line_old=1,
                        start_line_new=1,
                        added_lines=[
                            DiffLine(line_number=1, content="c", is_addition=True),
                        ],
                        removed_lines=[
                            DiffLine(line_number=1, content="d", is_addition=False),
                            DiffLine(line_number=2, content="e", is_addition=False),
                        ],
                    )
                ],
            ),
        ]

        reporter.show_diff_summary(files)

        result = output.getvalue()
        assert "2" in result  # 2 arquivos
        assert "+3" in result  # 3 linhas adicionadas
        assert "-2" in result  # 2 linhas removidas

    def test_nao_faz_nada_quando_disabled(self):
        """Quando disabled, não deve fazer nada."""
        from code_reviewer.models import DiffFile

        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, enabled=False)

        reporter.show_diff_summary([DiffFile(path="x.py", hunks=[])])

        assert output.getvalue() == ""


class TestProgressReporterShowDependencies:
    """Testes para método show_dependencies() do ProgressReporter."""

    def test_exibe_callers_encontrados(self):
        """Deve exibir arquivos que chamam as funções modificadas."""
        from code_reviewer.models import ContextGraph, FunctionRef

        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        contexts = [
            ContextGraph(
                function_name="process",
                file="main.py",
                callers=[
                    FunctionRef(
                        file="checkout.py",
                        line=10,
                        snippet="process()",
                        function_name="do_checkout",
                    ),
                    FunctionRef(
                        file="api.py",
                        line=20,
                        snippet="process()",
                        function_name="handle_request",
                    ),
                ],
                callees=[],
            )
        ]

        reporter.show_dependencies(contexts)

        result = output.getvalue()
        assert "Callers" in result
        assert "checkout.py" in result
        assert "api.py" in result

    def test_exibe_callees_encontrados(self):
        """Deve exibir funções chamadas pelo código modificado."""
        from code_reviewer.models import ContextGraph, FunctionRef

        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        contexts = [
            ContextGraph(
                function_name="process",
                file="main.py",
                callers=[],
                callees=[
                    FunctionRef(
                        file="utils.py",
                        line=5,
                        snippet="validate()",
                        function_name="validate",
                    )
                ],
            )
        ]

        reporter.show_dependencies(contexts)

        result = output.getvalue()
        assert "Callees" in result
        assert "validate()" in result
        assert "utils.py" in result

    def test_exibe_mensagem_sem_dependencias(self):
        """Quando não há dependências, deve exibir mensagem apropriada."""
        from code_reviewer.models import ContextGraph

        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console)

        contexts = [
            ContextGraph(
                function_name="isolated",
                file="isolated.py",
                callers=[],
                callees=[],
            )
        ]

        reporter.show_dependencies(contexts)

        result = output.getvalue()
        assert "Sem dependências encontradas" in result

    def test_nao_faz_nada_quando_disabled(self):
        """Quando disabled, não deve fazer nada."""
        from code_reviewer.models import ContextGraph

        output = io.StringIO()
        console = Console(file=output, force_terminal=False)
        reporter = ProgressReporter(console=console, enabled=False)

        contexts = [
            ContextGraph(
                function_name="fn",
                file="f.py",
                callers=[],
                callees=[],
            )
        ]

        reporter.show_dependencies(contexts)

        assert output.getvalue() == ""
