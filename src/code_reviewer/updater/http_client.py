"""Abstração de cliente HTTP para permitir troca futura de implementação."""

import json
import urllib.request
import urllib.error
from typing import Protocol, Any


class HttpClient(Protocol):
    """Interface para clientes HTTP."""

    def get(self, url: str, timeout: float = 5.0) -> dict[str, Any] | None:
        """Faz GET request e retorna JSON parseado ou None em caso de erro."""
        ...


class UrllibClient:
    """Implementação usando urllib da stdlib (zero dependências)."""

    def get(self, url: str, timeout: float = 5.0) -> dict[str, Any] | None:
        """Faz GET request e retorna JSON parseado ou None em caso de erro.

        Args:
            url: URL para fazer o request
            timeout: Timeout em segundos (default: 5.0)

        Returns:
            Dict com resposta JSON ou None se falhar
        """
        try:
            request = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "airev"},
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read().decode("utf-8")
                return json.loads(data)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            # Falha silenciosa - não queremos bloquear o usuário
            return None
        except Exception:
            # Qualquer outro erro também falha silenciosamente
            return None


def get_http_client() -> HttpClient:
    """Factory function para obter cliente HTTP.

    Retorna a implementação padrão (UrllibClient).
    Pode ser estendida no futuro para suportar httpx ou outras implementações.
    """
    return UrllibClient()
