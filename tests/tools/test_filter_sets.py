import httpx
import pytest
import respx

from prolific_mcp.client import ProlificClient
from prolific_mcp.tools.filter_sets import create_filter_set, get_filter_sets


@pytest.mark.asyncio
@respx.mock
async def test_get_filter_sets_passes_query_params(installed_client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/filter-sets/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    await get_filter_sets(workspace_id="ws_1", limit=50, offset=10)

    sent = route.calls.last.request
    assert sent.url.params["workspace_id"] == "ws_1"
    assert sent.url.params["limit"] == "50"
    assert sent.url.params["offset"] == "10"


@pytest.mark.asyncio
@respx.mock
async def test_create_filter_set_posts_payload(installed_client: ProlificClient) -> None:
    route = respx.post("https://api.prolific.test/api/v1/filter-sets/").mock(
        return_value=httpx.Response(201, json={"id": "fs_1"})
    )
    filters = [{"filter_id": "age", "selected_range": {"lower": 25, "upper": 40}}]

    result = await create_filter_set(
        workspace_id="ws_1",
        name="UK adults 25-40",
        filters=filters,
    )

    assert result == {"id": "fs_1"}
    body = route.calls.last.request.content
    assert b'"workspace_id":"ws_1"' in body
    assert b'"name":"UK adults 25-40"' in body
    assert b'"filter_id":"age"' in body
