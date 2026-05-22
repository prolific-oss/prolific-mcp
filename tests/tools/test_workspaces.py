import httpx
import pytest
import respx

from prolific_mcp.client import ProlificClient
from prolific_mcp.tools.workspaces import list_workspaces


@pytest.mark.asyncio
@respx.mock
async def test_list_workspaces_hits_endpoint(installed_client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/workspaces/").mock(
        return_value=httpx.Response(200, json={"results": [{"id": "ws_1"}]})
    )

    result = await list_workspaces.fn()

    assert route.called
    assert result == {"results": [{"id": "ws_1"}]}
