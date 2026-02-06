"""Verificação de versão contra PyPI com cache local."""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import __version__
from .http_client import get_http_client


# Configurações
PYPI_URL = "https://pypi.org/pypi/code-reviewer/json"
CACHE_DIR = Path.home() / ".cache" / "code-reviewer"
CACHE_FILE = CACHE_DIR / "update-check.json"
CACHE_TTL = timedelta(hours=1)
DEFAULT_TIMEOUT = 5.0


@dataclass
class UpdateInfo:
    """Informações sobre atualização disponível."""

    current_version: str
    latest_version: str

    @property
    def update_available(self) -> bool:
        """Retorna True se há atualização disponível."""
        return compare_versions(self.latest_version, self.current_version) > 0


def compare_versions(v1: str, v2: str) -> int:
    """Compara duas versões semânticas.

    Args:
        v1: Primeira versão (ex: "1.2.3")
        v2: Segunda versão (ex: "1.2.0")

    Returns:
        1 se v1 > v2, -1 se v1 < v2, 0 se iguais
    """

    def parse_version(v: str) -> tuple[int, ...]:
        """Parse versão em tupla de inteiros."""
        # Remove prefixo 'v' se existir
        v = v.lstrip("v")
        # Pega apenas a parte numérica (ignora sufixos como -alpha, .dev0)
        parts = v.split("-")[0].split("+")[0]
        try:
            return tuple(int(x) for x in parts.split("."))
        except ValueError:
            return (0, 0, 0)

    t1 = parse_version(v1)
    t2 = parse_version(v2)

    # Normaliza tamanhos
    max_len = max(len(t1), len(t2))
    t1 = t1 + (0,) * (max_len - len(t1))
    t2 = t2 + (0,) * (max_len - len(t2))

    if t1 > t2:
        return 1
    elif t1 < t2:
        return -1
    return 0


def _read_cache() -> dict | None:
    """Lê cache de verificação de versão.

    Returns:
        Dict com dados do cache ou None se inválido/expirado
    """
    if not CACHE_FILE.exists():
        return None

    try:
        data = json.loads(CACHE_FILE.read_text())
        checked_at = datetime.fromisoformat(data["checked_at"])

        # Verifica se cache expirou
        now = datetime.now(timezone.utc)
        if now - checked_at > CACHE_TTL:
            return None

        return data
    except (json.JSONDecodeError, KeyError, ValueError):
        # Cache corrompido
        return None


def _write_cache(latest_version: str) -> None:
    """Salva resultado no cache.

    Args:
        latest_version: Versão mais recente encontrada
    """
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "latest_version": latest_version,
        }
        CACHE_FILE.write_text(json.dumps(data, indent=2))
    except OSError:
        # Falha ao escrever cache - ignora silenciosamente
        pass


def get_latest_version(timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """Consulta PyPI para obter a versão mais recente.

    Args:
        timeout: Timeout para o request em segundos

    Returns:
        String com versão mais recente ou None se falhar
    """
    client = get_http_client()
    response = client.get(PYPI_URL, timeout=timeout)

    if response is None:
        return None

    try:
        return response["info"]["version"]
    except (KeyError, TypeError):
        return None


def check_for_update(timeout: float = DEFAULT_TIMEOUT) -> UpdateInfo | None:
    """Verifica se há atualização disponível.

    Usa cache local para evitar requests excessivos ao PyPI.
    Falha silenciosamente se não conseguir verificar.

    Args:
        timeout: Timeout para request ao PyPI

    Returns:
        UpdateInfo se há atualização, None se já está atualizado ou falhou
    """
    # Verifica opt-out via variável de ambiente
    if os.environ.get("CODE_REVIEWER_NO_UPDATE_CHECK", "").strip() == "1":
        return None

    current = __version__

    # Tenta usar cache primeiro
    cache = _read_cache()
    if cache:
        latest = cache["latest_version"]
    else:
        # Cache expirado ou inexistente - consulta PyPI
        latest = get_latest_version(timeout=timeout)
        if latest is None:
            return None
        _write_cache(latest)

    # Compara versões
    info = UpdateInfo(current_version=current, latest_version=latest)

    if info.update_available:
        return info

    return None
