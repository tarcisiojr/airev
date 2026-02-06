"""Testes para o módulo de auto-update."""

import json
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
    compare_versions,
    get_latest_version,
)
from code_reviewer.updater.notifier import notify_update
from code_reviewer.updater.upgrade import detect_installer, run_upgrade


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
            "os.environ", {"CODE_REVIEWER_NO_UPDATE_CHECK": "1"}
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
        fake_path = Path("/home/user/.local/pipx/venvs/code-reviewer/bin/python")
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


class TestRunUpgrade:
    """Testes para run_upgrade."""

    def test_upgrade_no_update_available(self):
        """Deve retornar False quando não há update."""
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)

        with patch(
            "code_reviewer.updater.upgrade.check_for_update", return_value=None
        ):
            result = run_upgrade(console)

            assert result is False

    def test_upgrade_success_pipx(self):
        """Deve executar pipx upgrade com sucesso."""
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
            "subprocess.run", return_value=mock_result
        ) as mock_run:
            result = run_upgrade(console)

            assert result is True
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "pipx" in cmd
            assert "upgrade" in cmd

    def test_upgrade_success_pip(self):
        """Deve executar pip install --upgrade com sucesso."""
        from rich.console import Console

        console = Console(file=StringIO(), force_terminal=True)
        update_info = UpdateInfo(current_version="0.1.0", latest_version="0.2.0")
        mock_result = MagicMock(returncode=0, stderr="")

        with patch(
            "code_reviewer.updater.upgrade.check_for_update",
            return_value=update_info,
        ), patch(
            "code_reviewer.updater.upgrade.detect_installer", return_value="pip"
        ), patch(
            "subprocess.run", return_value=mock_result
        ) as mock_run:
            result = run_upgrade(console)

            assert result is True
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "--upgrade" in cmd
            assert "code-reviewer" in cmd
