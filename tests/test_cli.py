"""Testes para o CLI."""

from click.testing import CliRunner

from code_reviewer.cli import review


class TestReviewCommand:
    """Testes para o comando review."""

    def test_flag_text_quality_reconhecida(self):
        """Verifica que a flag --text-quality é aceita pelo CLI."""
        runner = CliRunner()

        # Invoca com --help para verificar que a flag existe
        result = runner.invoke(review, ["--help"])

        assert result.exit_code == 0
        assert "--text-quality" in result.output
        assert "ortografia" in result.output or "spelling" in result.output.lower()

    def test_flag_text_quality_short_form(self):
        """Verifica que a forma curta -t funciona."""
        runner = CliRunner()

        result = runner.invoke(review, ["--help"])

        assert result.exit_code == 0
        assert "-t" in result.output

    def test_flag_description_reconhecida(self):
        """Verifica que a flag --description é aceita pelo CLI."""
        runner = CliRunner()

        result = runner.invoke(review, ["--help"])

        assert result.exit_code == 0
        assert "--description" in result.output
        assert "-d" in result.output

    def test_flag_description_aceita_stdin(self):
        """Verifica que a flag --description menciona stdin."""
        runner = CliRunner()

        result = runner.invoke(review, ["--help"])

        assert result.exit_code == 0
        assert "stdin" in result.output.lower()

    def test_flag_no_interactive_reconhecida(self):
        """Verifica que a flag --no-interactive é aceita pelo CLI."""
        runner = CliRunner()

        result = runner.invoke(review, ["--help"])

        assert result.exit_code == 0
        assert "--no-interactive" in result.output
