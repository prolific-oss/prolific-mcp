import httpx
import pytest
import respx

from prolific_mcp.client import ProlificClient
from prolific_mcp.tools.filters import get_filters


@pytest.mark.asyncio
@respx.mock
async def test_get_filters_calls_filters_endpoint(installed_client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/filters/").mock(
        return_value=httpx.Response(200, json=[{"filter_id": "age"}])
    )

    result = await get_filters()

    assert route.called
    assert result == [{"filter_id": "age"}]
