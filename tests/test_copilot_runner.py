"""Testes para o CopilotCLIRunner."""

from unittest.mock import MagicMock, patch

import pytest

from code_reviewer.runners.copilot import CopilotCLIRunner


class TestCopilotCLIRunnerAvailability:
    """Testes para verificação de disponibilidade do Copilot CLI."""

    def test_disponivel_quando_copilot_existe(self):
        """Quando comando copilot existe, deve retornar True."""
        runner = CopilotCLIRunner()

        with patch(
            "code_reviewer.runners.copilot.check_command_exists"
        ) as mock_check:
            mock_check.return_value = True

            result = runner.check_availability()

            assert result is True
            mock_check.assert_called_once_with("copilot")

    def test_indisponivel_quando_copilot_nao_existe(self):
        """Quando comando copilot não existe, deve retornar False."""
        runner = CopilotCLIRunner()

        with patch(
            "code_reviewer.runners.copilot.check_command_exists"
        ) as mock_check:
            mock_check.return_value = False

            result = runner.check_availability()

            assert result is False


class TestCopilotCLIRunnerExecution:
    """Testes para execução de prompts via Copilot CLI."""

    def test_run_executa_com_yolo_e_silent_via_stdin(self, tmp_path):
        """Deve executar copilot com flags --yolo e --silent, passando prompt via stdin."""
        runner = CopilotCLIRunner()

        with patch.object(runner, "check_availability", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="resposta do copilot",
                    stderr="",
                    returncode=0,
                )

                result = runner.run("prompt teste", tmp_path)

                # Verifica que executou com os flags corretos
                mock_run.assert_called_once()
                call_args = mock_run.call_args
                cmd = call_args[0][0]

                assert cmd[0] == "copilot"
                assert "--yolo" in cmd
                assert "--silent" in cmd

                # Verifica que prompt é passado via stdin, não como argumento
                assert "-p" not in cmd
                assert "prompt teste" not in cmd
                assert call_args[1]["input"] == "prompt teste"

                # Verifica que passou o workdir
                assert call_args[1]["cwd"] == tmp_path

                assert result == "resposta do copilot"

    def test_run_inclui_stderr_em_caso_de_erro(self, tmp_path):
        """Deve incluir stderr no output quando contém erro."""
        runner = CopilotCLIRunner()

        with patch.object(runner, "check_availability", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="output parcial",
                    stderr="Error: algo deu errado",
                    returncode=1,
                )

                result = runner.run("prompt", tmp_path)

                assert "output parcial" in result
                assert "Error: algo deu errado" in result

    def test_run_lanca_erro_quando_indisponivel(self, tmp_path):
        """Quando Copilot indisponível, deve lançar RunnerNotFoundError."""
        from code_reviewer.runners.base import RunnerNotFoundError

        runner = CopilotCLIRunner()

        with patch.object(runner, "check_availability", return_value=False):
            with pytest.raises(RunnerNotFoundError) as exc_info:
                runner.run("prompt teste", tmp_path)

            # Verifica que a mensagem contém instruções de instalação
            msg = exc_info.value.args[0].lower()
            assert "copilot" in msg
            assert "npm" in msg or "brew" in msg

    def test_run_prompt_grande_via_stdin(self, tmp_path):
        """Prompt grande deve ser passado via stdin sem erro de ARG_MAX."""
        runner = CopilotCLIRunner()
        # Prompt de ~300KB, acima do limite ARG_MAX do macOS (~256KB)
        prompt_grande = "x" * 300_000

        with patch.object(runner, "check_availability", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    stdout="resposta ok",
                    stderr="",
                    returncode=0,
                )

                result = runner.run(prompt_grande, tmp_path)

                # Verifica que prompt grande foi passado via stdin
                call_args = mock_run.call_args
                cmd = call_args[0][0]
                assert prompt_grande not in cmd
                assert call_args[1]["input"] == prompt_grande
                assert result == "resposta ok"

    def test_name_retorna_copilot(self):
        """Propriedade name deve retornar 'copilot'."""
        runner = CopilotCLIRunner()
        assert runner.name == "copilot"
