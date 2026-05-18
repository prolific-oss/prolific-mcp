import httpx
import pytest
import respx

from prolific_mcp.client import ProlificClient
from prolific_mcp.tools.eligibility import get_eligibility_count


@pytest.mark.asyncio
@respx.mock
async def test_get_eligibility_count_posts_filters(installed_client: ProlificClient) -> None:
    route = respx.post("https://api.prolific.test/api/v1/eligibility-count/").mock(
        return_value=httpx.Response(200, json={"count": 2034})
    )
    filters = [{"filter_id": "current_country_live", "selected_values": ["GB"]}]

    result = await get_eligibility_count(filters=filters)

    assert result == {"count": 2034}
    body = route.calls.last.request.content
    assert b'"filter_id":"current_country_live"' in body
