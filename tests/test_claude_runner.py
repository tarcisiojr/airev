"""Testes para o ClaudeCLIRunner."""

from unittest.mock import MagicMock, patch

import pytest

from code_reviewer.runners import get_runner, list_runners
from code_reviewer.runners.base import RunnerExecutionError, RunnerNotFoundError
from code_reviewer.runners.claude import ClaudeCLIRunner


class TestClaudeCLIRunnerRegistry:
    """Testes de registro do runner claude."""

    def test_claude_esta_registrado(self):
        assert "claude" in list_runners()

    def test_get_runner_retorna_instancia(self):
        runner = get_runner("claude")
        assert isinstance(runner, ClaudeCLIRunner)
        assert runner.name == "claude"


class TestClaudeCLIRunnerAvailability:
    """Testes para verificação de disponibilidade do Claude Code CLI."""

    def test_disponivel_quando_claude_existe(self):
        runner = ClaudeCLIRunner()

        with patch(
            "code_reviewer.runners.claude.check_command_exists"
        ) as mock_check:
            mock_check.return_value = True

            assert runner.check_availability() is True
            mock_check.assert_called_once_with("claude")

    def test_indisponivel_quando_claude_nao_existe(self):
        runner = ClaudeCLIRunner()

        with patch(
            "code_reviewer.runners.claude.check_command_exists"
        ) as mock_check:
            mock_check.return_value = False

            assert runner.check_availability() is False


class TestClaudeCLIRunnerExecution:
    """Testes para execução de prompts via Claude Code CLI."""

    def test_run_executa_em_modo_print_via_stdin(self, tmp_path):
        """Deve executar claude com -p, passando o prompt via stdin."""
        runner = ClaudeCLIRunner()

        with patch.object(runner, "check_availability", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout='{"findings": []}',
                    stderr="",
                    returncode=0,
                )

                result = runner.run("prompt teste", tmp_path)

                mock_run.assert_called_once()
                call_args = mock_run.call_args
                assert call_args.args[0] == ["claude", "-p"]
                assert call_args.kwargs["input"] == "prompt teste"
                assert call_args.kwargs["cwd"] == tmp_path
                assert result == '{"findings": []}'

    def test_run_lanca_erro_quando_indisponivel(self, tmp_path):
        runner = ClaudeCLIRunner()

        with patch.object(runner, "check_availability", return_value=False):
            with pytest.raises(RunnerNotFoundError, match="Claude Code CLI"):
                runner.run("prompt", tmp_path)

    def test_run_com_exit_code_diferente_de_zero_levanta_erro(self, tmp_path):
        """Falha do CLI deve virar exceção, nunca resposta vazia da IA."""
        runner = ClaudeCLIRunner()

        with patch.object(runner, "check_availability", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="",
                    stderr="Invalid API key",
                    returncode=1,
                )

                with pytest.raises(RunnerExecutionError, match="Invalid API key"):
                    runner.run("prompt", tmp_path)
