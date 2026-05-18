from typing import Any

import httpx

from prolific_mcp.config import Config, load_config
from prolific_mcp.errors import ProlificAPIError

USER_AGENT = "prolific-mcp/0.1.0"


class ProlificClient:
    def __init__(self, config: Config | None = None, client: httpx.AsyncClient | None = None):
        self._config = config or load_config()
        self._client = client or httpx.AsyncClient(
            base_url=f"{self._config.base_url}/api/v1",
            headers={
                "Authorization": f"Token {self._config.token}",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
            timeout=30.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._handle(await self._client.get(path, params=params))

    async def post(self, path: str, json: Any | None = None) -> Any:
        return self._handle(await self._client.post(path, json=json))

    async def patch(self, path: str, json: Any | None = None) -> Any:
        return self._handle(await self._client.patch(path, json=json))

    @staticmethod
    def _handle(response: httpx.Response) -> Any:
        if response.is_success:
            if not response.content:
                return None
            return response.json()
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text
        raise ProlificAPIError(response.status_code, body)


_default_client: ProlificClient | None = None


def get_client() -> ProlificClient:
    """Return the process-wide ProlificClient, creating it from env on first call."""
    global _default_client
    if _default_client is None:
        _default_client = ProlificClient()
    return _default_client


def set_client(client: ProlificClient | None) -> None:
    """Override (or reset) the process-wide ProlificClient. Used by tests."""
    global _default_client
    _default_client = client
