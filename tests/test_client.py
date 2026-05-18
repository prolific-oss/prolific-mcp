import httpx
import pytest
import respx

from prolific_mcp.client import ProlificClient
from prolific_mcp.errors import ProlificAPIError


@pytest.mark.asyncio
@respx.mock
async def test_get_sends_auth_header_and_returns_json(client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/things/").mock(
        return_value=httpx.Response(200, json={"results": [1, 2, 3]})
    )

    result = await client.get("/things/")

    assert result == {"results": [1, 2, 3]}
    assert route.called
    sent = route.calls.last.request
    assert sent.headers["authorization"] == "Token test-token-123456"
    assert sent.headers["user-agent"] == "prolific-mcp/0.1.0"


@pytest.mark.asyncio
@respx.mock
async def test_post_sends_json_body(client: ProlificClient) -> None:
    route = respx.post("https://api.prolific.test/api/v1/things/").mock(
        return_value=httpx.Response(201, json={"id": "x"})
    )

    result = await client.post("/things/", json={"name": "foo"})

    assert result == {"id": "x"}
    assert route.calls.last.request.content == b'{"name":"foo"}'


@pytest.mark.asyncio
@respx.mock
async def test_get_with_query_params(client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/things/").mock(
        return_value=httpx.Response(200, json=[])
    )

    await client.get("/things/", params={"workspace_id": "ws1"})

    assert route.calls.last.request.url.query == b"workspace_id=ws1"


@pytest.mark.asyncio
@respx.mock
async def test_non_2xx_raises_with_status_and_body(client: ProlificClient) -> None:
    respx.get("https://api.prolific.test/api/v1/boom/").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )

    with pytest.raises(ProlificAPIError) as excinfo:
        await client.get("/boom/")

    assert excinfo.value.status_code == 404
    assert excinfo.value.body == {"detail": "not found"}


@pytest.mark.asyncio
@respx.mock
async def test_non_json_error_falls_back_to_text(client: ProlificClient) -> None:
    respx.get("https://api.prolific.test/api/v1/boom/").mock(
        return_value=httpx.Response(500, text="server exploded")
    )

    with pytest.raises(ProlificAPIError) as excinfo:
        await client.get("/boom/")

    assert excinfo.value.status_code == 500
    assert excinfo.value.body == "server exploded"


@pytest.mark.asyncio
@respx.mock
async def test_empty_2xx_response_returns_none(client: ProlificClient) -> None:
    respx.post("https://api.prolific.test/api/v1/things/").mock(return_value=httpx.Response(204))

    assert await client.post("/things/") is None
