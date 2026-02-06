"""Testes para o módulo de auto-update."""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from code_reviewer.updater.http_client import UrllibClient, get_http_client
from code_reviewer.updater.version_check import (
    CACHE_FILE,
    CACHE_TTL,
    UpdateInfo,
    _read_cache,
    _write_cache,
    check_for_update,
    clear_cache,
    compare_versions,
    get_latest_version,
)
from code_reviewer.updater.notifier import notify_update
from code_reviewer.updater.upgrade import (
    detect_installer,
    get_installed_version,
    run_upgrade,
)


class TestHttpClient:
    """Testes para http_client.py."""

    def test_get_http_client_returns_urllib_client(self):
        """Factory deve retornar UrllibClient."""
        client = get_http_client()
        assert isinstance(client, UrllibClient)

    def test_urllib_client_get_success(self):
        """UrllibClient.get deve retornar dict em sucesso."""
        client = UrllibClient()
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"version": "1.0.0"}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.get("https://example.com/api", timeout=5.0)

        assert result == {"version": "1.0.0"}

    def test_urllib_client_get_timeout(self):
        """UrllibClient.get deve retornar None em timeout."""
        client = UrllibClient()

        with patch("urllib.request.urlopen", side_effect=TimeoutError):
            result = client.get("https://example.com/api", timeout=0.001)

        assert result is None

    def test_urllib_client_get_invalid_json(self):
        """UrllibClient.get deve retornar None em JSON inválido."""
        client = UrllibClient()
        mock_response = MagicMock()
        mock_response.read.return_value = b"not json"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client.get("https://example.com/api")

        assert result is None


class TestVersionComparison:
    """Testes para comparação de versões."""

    @pytest.mark.parametrize(
        "v1,v2,expected",
        [
            ("1.0.0", "0.9.0", 1),
            ("0.9.0", "1.0.0", -1),
            ("1.0.0", "1.0.0", 0),
            ("1.2.3", "1.2.0", 1),
            ("1.2.0", "1.2.3", -1),
            ("2.0.0", "1.9.9", 1),
            ("0.1.0", "0.0.1", 1),
            ("v1.0.0", "1.0.0", 0),
            ("1.0.0-alpha", "1.0.0", 0),
            ("1.0.0+build", "1.0.0", 0),
        ],
    )
    def test_compare_versions(self, v1, v2, expected):
        """Comparação de versões semânticas."""
        assert compare_versions(v1, v2) == expected

    def test_update_info_available(self):
        """UpdateInfo.update_available deve retornar True se latest > current."""
        info = UpdateInfo(current_version="0.1.0", latest_version="0.2.0")
        assert info.update_available is True

    def test_update_info_not_available(self):
        """UpdateInfo.update_available deve retornar False se current >= latest."""
        info = UpdateInfo(current_version="0.2.0", latest_version="0.2.0")
        assert info.update_available is False


class TestCache:
    """Testes para cache de verificação."""

    def test_write_and_read_cache(self, tmp_path):
        """Cache deve ser escrito e lido corretamente."""
        with patch(
            "code_reviewer.updater.version_check.CACHE_DIR", tmp_path
        ), patch(
            "code_reviewer.updater.version_check.CACHE_FILE",
            tmp_path / "update-check.json",
        ):
            _write_cache("1.2.3")
            cache = _read_cache()

            assert cache is not None
            assert cache["latest_version"] == "1.2.3"
            assert "checked_at" in cache

    def test_read_expired_cache(self, tmp_path):
        """Cache expirado deve retornar None."""
        cache_file = tmp_path / "update-check.json"
        old_time = datetime.now(timezone.utc) - CACHE_TTL - timedelta(minutes=1)
        cache_data = {
            "checked_at": old_time.isoformat(),
            "latest_version": "1.0.0",
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch(
            "code_reviewer.updater.version_check.CACHE_FILE", cache_file
        ):
            cache = _read_cache()

        assert cache is None

    def test_read_corrupted_cache(self, tmp_path):
        """Cache corrompido deve retornar None."""
        cache_file = tmp_path / "update-check.json"
        cache_file.write_text("not valid json")

        with patch(
            "code_reviewer.updater.version_check.CACHE_FILE", cache_file
        ):
            cache = _read_cache()

        assert cache is None

    def test_read_nonexistent_cache(self, tmp_path):
        """Cache inexistente deve retornar None."""
        with patch(
            "code_reviewer.updater.version_check.CACHE_FILE",
            tmp_path / "nonexistent.json",
        ):
            cache = _read_cache()

        assert cache is None


class TestClearCache:
    """Testes para clear_cache."""

    def test_clear_existing_cache(self, tmp_path):
        """Deve remover arquivo de cache existente."""
        cache_file = tmp_path / "update-check.json"
        cache_file.write_text('{"test": true}')

        with patch(
            "code_reviewer.updater.version_check.CACHE_FILE", cache_file
        ):
            result = clear_cache()

        assert result is True
        assert not cache_file.exists()

    def test_clear_nonexistent_cache(self, tmp_path):
        """Deve retornar True quando cache não existe."""
        cache_file = tmp_path / "nonexistent.json"

        with patch(
            "code_reviewer.updater.version_check.CACHE_FILE", cache_file
        ):
            result = clear_cache()

        assert result is True

    def test_clear_cache_permission_error(self, tmp_path):
        """Deve retornar False quando não consegue remover."""
        cache_file = tmp_path / "update-check.json"
        cache_file.write_text('{"test": true}')

        with patch(
            "code_reviewer.updater.version_check.CACHE_FILE", cache_file
        ), patch(
            "pathlib.Path.unlink", side_effect=OSError("Permission denied")
        ):
            result = clear_cache()

        assert result is False


class TestCheckForUpdate:
    """Testes para check_for_update."""

    def test_check_with_update_available(self, tmp_path):
        """Deve retornar UpdateInfo quando há update."""
        with patch(
            "code_reviewer.updater.version_check.CACHE_DIR", tmp_path
        ), patch(
            "code_reviewer.updater.version_check.CACHE_FILE",
            tmp_path / "update-check.json",
        ), patch(
            "code_reviewer.updater.version_check.get_latest_version",
            return_value="99.0.0",
        ), patch(
            "code_reviewer.updater.version_check.__version__", "0.1.0"
        ), patch.dict(
            "os.environ", {}, clear=True
        ):
            result = check_for_update()

            assert result is not None
            assert result.latest_version == "99.0.0"
            assert result.current_version == "0.1.0"

    def test_check_no_update(self, tmp_path):
        """Deve retornar None quando não há update."""
        with patch(
            "code_reviewer.updater.version_check.CACHE_DIR", tmp_path
        ), patch(
            "code_reviewer.updater.version_check.CACHE_FILE",
            tmp_path / "update-check.json",
        ), patch(
            "code_reviewer.updater.version_check.get_latest_version",
            return_value="0.1.0",
        ), patch(
            "code_reviewer.updater.version_check.__version__", "0.1.0"
        ), patch.dict(
            "os.environ", {}, clear=True
        ):
            result = check_for_update()

            assert result is None

    def test_check_opt_out(self):
        """Deve retornar None quando opt-out está ativo."""
        with patch.dict(
            "os.environ", {"AIREV_NO_UPDATE_CHECK": "1"}
        ):
            result = check_for_update()

            assert result is None

    def test_check_pypi_failure(self, tmp_path):
        """Deve retornar None quando PyPI falha."""
        with patch(
            "code_reviewer.updater.version_check.CACHE_DIR", tmp_path
        ), patch(
            "code_reviewer.updater.version_check.CACHE_FILE",
            tmp_path / "update-check.json",
        ), patch(
            "code_reviewer.updater.version_check.get_latest_version",
            return_value=None,
        ), patch.dict(
            "os.environ", {}, clear=True
        ):
            result = check_for_update()

            assert result is None


class TestNotifier:
    """Testes para notifier.py."""

    def test_notify_update_output(self, capsys):
        """notify_update deve exibir painel com informações."""
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)
        info = UpdateInfo(current_version="0.1.0", latest_version="0.2.0")

        notify_update(info, console=console)

        # Verifica que o console foi usado (output foi gerado)
        output = console.file.getvalue()
        assert "0.2.0" in output
        assert "0.1.0" in output


class TestDetectInstaller:
    """Testes para detect_installer."""

    def test_detect_pipx(self):
        """Deve detectar pipx quando no path do executável."""
        fake_path = Path("/home/user/.local/pipx/venvs/airev/bin/python")
        with patch.object(sys, "executable", str(fake_path)):
            result = detect_installer()
            assert result == "pipx"

    def test_detect_pip(self):
        """Deve retornar pip como fallback."""
        fake_path = Path("/usr/bin/python3")
        with patch.object(sys, "executable", str(fake_path)):
            result = detect_installer()
            assert result == "pip"

    def test_detect_venv_pip(self):
        """Deve retornar pip para venvs normais."""
        fake_path = Path("/home/user/project/.venv/bin/python")
        with patch.object(sys, "executable", str(fake_path)):
            result = detect_installer()
            assert result == "pip"


class TestGetInstalledVersion:
    """Testes para get_installed_version."""

    def test_get_version_pipx_json(self):
        """Deve obter versão do pipx list --json."""
        pipx_json = {
            "venvs": {
                "airev": {
                    "metadata": {
                        "main_package": {
                            "package_version": "1.2.3"
                        }
                    }
                }
            }
        }
        mock_result = MagicMock(returncode=0, stdout=json.dumps(pipx_json))

        with patch("subprocess.run", return_value=mock_result):
            result = get_installed_version("pipx")

        assert result == "1.2.3"

    def test_get_version_pipx_not_installed(self):
        """Deve retornar None quando airev não está instalado no pipx."""
        pipx_json = {"venvs": {}}
        mock_result = MagicMock(returncode=0, stdout=json.dumps(pipx_json))

        with patch("subprocess.run", return_value=mock_result):
            result = get_installed_version("pipx")

        assert result is None

    def test_get_version_pip(self):
        """Deve obter versão do pip show."""
        pip_output = """Name: airev
Version: 1.0.0
Summary: Code reviewer CLI
"""
        mock_result = MagicMock(returncode=0, stdout=pip_output)

        with patch("subprocess.run", return_value=mock_result):
            result = get_installed_version("pip")

        assert result == "1.0.0"

    def test_get_version_pip_not_installed(self):
        """Deve retornar None quando pip show falha."""
        mock_result = MagicMock(returncode=1, stdout="")

        with patch("subprocess.run", return_value=mock_result):
            result = get_installed_version("pip")

        assert result is None

    def test_get_version_subprocess_error(self):
        """Deve retornar None em erro de subprocess."""
        with patch("subprocess.run", side_effect=subprocess.SubprocessError):
            result = get_installed_version("pipx")

        assert result is None


class TestRunUpgrade:
    """Testes para run_upgrade."""

    def test_upgrade_no_update_available(self):
        """Deve retornar False e limpar cache quando não há update."""
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)

        with patch(
            "code_reviewer.updater.upgrade.check_for_update", return_value=None
        ), patch(
            "code_reviewer.updater.upgrade.clear_cache", return_value=True
        ) as mock_clear:
            result = run_upgrade(console)

            assert result is False
            mock_clear.assert_called_once()

    def test_upgrade_success_pipx_version_changed(self):
        """Deve executar pipx upgrade e verificar mudança de versão."""
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)
        update_info = UpdateInfo(current_version="0.1.0", latest_version="0.2.0")
        mock_result = MagicMock(returncode=0, stderr="")

        # Simula versão mudando de 0.1.0 para 0.2.0 após upgrade
        version_calls = iter(["0.1.0", "0.2.0"])

        with patch(
            "code_reviewer.updater.upgrade.check_for_update",
            return_value=update_info,
        ), patch(
            "code_reviewer.updater.upgrade.detect_installer", return_value="pipx"
        ), patch(
            "code_reviewer.updater.upgrade.get_installed_version",
            side_effect=lambda _: next(version_calls),
        ), patch(
            "code_reviewer.updater.upgrade.clear_cache", return_value=True
        ) as mock_clear, patch(
            "subprocess.run", return_value=mock_result
        ) as mock_run:
            result = run_upgrade(console)

            assert result is True
            mock_run.assert_called_once()
            mock_clear.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "pipx" in cmd
            assert "upgrade" in cmd

    def test_upgrade_success_but_version_unchanged(self):
        """Deve retornar False quando versão não muda após upgrade."""
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)
        update_info = UpdateInfo(current_version="0.1.0", latest_version="0.2.0")
        mock_result = MagicMock(returncode=0, stderr="")

        with patch(
            "code_reviewer.updater.upgrade.check_for_update",
            return_value=update_info,
        ), patch(
            "code_reviewer.updater.upgrade.detect_installer", return_value="pipx"
        ), patch(
            "code_reviewer.updater.upgrade.get_installed_version",
            return_value="0.1.0",  # Versão não muda
        ), patch(
            "code_reviewer.updater.upgrade.clear_cache", return_value=True
        ) as mock_clear, patch(
            "subprocess.run", return_value=mock_result
        ):
            result = run_upgrade(console)

            assert result is False
            mock_clear.assert_called_once()

    def test_upgrade_success_pip_version_changed(self):
        """Deve executar pip install --upgrade e verificar mudança."""
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)
        update_info = UpdateInfo(current_version="0.1.0", latest_version="0.2.0")
        mock_result = MagicMock(returncode=0, stderr="")

        version_calls = iter(["0.1.0", "0.2.0"])

        with patch(
            "code_reviewer.updater.upgrade.check_for_update",
            return_value=update_info,
        ), patch(
            "code_reviewer.updater.upgrade.detect_installer", return_value="pip"
        ), patch(
            "code_reviewer.updater.upgrade.get_installed_version",
            side_effect=lambda _: next(version_calls),
        ), patch(
            "code_reviewer.updater.upgrade.clear_cache", return_value=True
        ), patch(
            "subprocess.run", return_value=mock_result
        ) as mock_run:
            result = run_upgrade(console)

            assert result is True
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "--upgrade" in cmd
            assert "airev" in cmd

    def test_upgrade_clears_cache_on_failure(self):
        """Deve limpar cache mesmo quando upgrade falha."""
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)
        update_info = UpdateInfo(current_version="0.1.0", latest_version="0.2.0")
        mock_result = MagicMock(returncode=1, stderr="Error")

        with patch(
            "code_reviewer.updater.upgrade.check_for_update",
            return_value=update_info,
        ), patch(
            "code_reviewer.updater.upgrade.detect_installer", return_value="pipx"
        ), patch(
            "code_reviewer.updater.upgrade.get_installed_version",
            return_value="0.1.0",
        ), patch(
            "code_reviewer.updater.upgrade.clear_cache", return_value=True
        ) as mock_clear, patch(
            "subprocess.run", return_value=mock_result
        ):
            result = run_upgrade(console)

            assert result is False
            mock_clear.assert_called_once()

    def test_upgrade_clears_cache_on_exception(self):
        """Deve limpar cache quando ocorre exceção."""
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)
        update_info = UpdateInfo(current_version="0.1.0", latest_version="0.2.0")

        with patch(
            "code_reviewer.updater.upgrade.check_for_update",
            return_value=update_info,
        ), patch(
            "code_reviewer.updater.upgrade.detect_installer", return_value="pipx"
        ), patch(
            "code_reviewer.updater.upgrade.get_installed_version",
            return_value="0.1.0",
        ), patch(
            "code_reviewer.updater.upgrade.clear_cache", return_value=True
        ) as mock_clear, patch(
            "subprocess.run", side_effect=FileNotFoundError
        ):
            result = run_upgrade(console)

            assert result is False
            mock_clear.assert_called_once()
