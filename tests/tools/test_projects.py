import httpx
import pytest
import respx

from prolific_mcp.client import ProlificClient
from prolific_mcp.tools.projects import list_projects


@pytest.mark.asyncio
@respx.mock
async def test_list_projects_uses_workspace_path(installed_client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/workspaces/ws_1/projects/").mock(
        return_value=httpx.Response(200, json={"results": [{"id": "proj_1"}]})
    )

    result = await list_projects(workspace_id="ws_1")

    assert route.called
    assert result == {"results": [{"id": "proj_1"}]}
