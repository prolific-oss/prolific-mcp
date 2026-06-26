from collections.abc import AsyncIterator

import httpx
import pytest

from prolific_mcp import client as client_module
from prolific_mcp.client import ProlificClient
from prolific_mcp.config import Config

TEST_BASE_URL = "https://api.prolific.test"


def _build_client(config: Config) -> ProlificClient:
    httpx_client = httpx.AsyncClient(
        base_url=f"{config.base_url}/api/v1",
        headers={
            "Authorization": f"Token {config.token}",
            "Content-Type": "application/json",
            "User-Agent": "prolific-mcp/0.0.1",
        },
    )
    return ProlificClient(config=config, client=httpx_client)


@pytest.fixture
def config() -> Config:
    return Config(token="test-token-123456", base_url=TEST_BASE_URL)


@pytest.fixture
async def client(config: Config) -> AsyncIterator[ProlificClient]:
    prolific = _build_client(config)
    try:
        yield prolific
    finally:
        await prolific.aclose()


@pytest.fixture
async def installed_client(config: Config) -> AsyncIterator[ProlificClient]:
    """Build a ProlificClient and install it as the process-wide default for tools."""
    prolific = _build_client(config)
    client_module.set_client(prolific)
    try:
        yield prolific
    finally:
        client_module.set_client(None)
        await prolific.aclose()
