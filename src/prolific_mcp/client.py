from typing import Any

import httpx

from prolific_mcp.config import Config, load_config
from prolific_mcp.errors import ProlificAPIError

USER_AGENT = "prolific-mcp/0.0.1"


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

    @property
    def base_url(self) -> str:
        """Root Prolific API URL this client targets, e.g. https://api.prolific.com."""
        return self._config.base_url

    @property
    def app_url(self) -> str:
        """Root Prolific web app URL, e.g. https://app.prolific.com (for preview links)."""
        return self._config.app_url

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._handle(await self._client.get(path, params=params))

    async def post(self, path: str, json: Any | None = None) -> Any:
        return self._handle(await self._client.post(path, json=json))

    async def post_with_headers(
        self, path: str, json: Any | None = None
    ) -> tuple[Any, httpx.Headers]:
        """Like `post`, but also returns the response headers.

        Needed for endpoints that carry data outside the JSON body — e.g. the
        webhook subscription confirm handshake's one-time secret, delivered
        via the `X-Hook-Secret` response header rather than the body.
        """
        response = await self._client.post(path, json=json)
        return self._handle(response), response.headers

    async def post_text(self, path: str, json: Any | None = None) -> str:
        """Like `post`, but for endpoints whose successful response is plain
        text (e.g. CSV), not JSON — `_handle` would fail decoding it as JSON."""
        response = await self._client.post(path, json=json)
        self._raise_for_error(response)
        return response.text

    async def patch(self, path: str, json: Any | None = None) -> Any:
        return self._handle(await self._client.patch(path, json=json))

    async def put(self, path: str, json: Any | None = None) -> Any:
        return self._handle(await self._client.put(path, json=json))

    async def delete(self, path: str) -> Any:
        return self._handle(await self._client.delete(path))

    @staticmethod
    def _raise_for_error(response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text
        raise ProlificAPIError(response.status_code, body)

    @classmethod
    def _handle(cls, response: httpx.Response) -> Any:
        cls._raise_for_error(response)
        if not response.content:
            return None
        return response.json()


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
