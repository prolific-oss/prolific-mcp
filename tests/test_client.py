import httpx
import pytest
import respx

from prolific_mcp import __version__
from prolific_mcp.client import ProlificClient
from prolific_mcp.config import Config
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
    assert sent.headers["user-agent"] == "prolific-mcp/0.0.1"


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
async def test_put_sends_json_body(client: ProlificClient) -> None:
    route = respx.put("https://api.prolific.test/api/v1/things/").mock(
        return_value=httpx.Response(200, json={"id": "x"})
    )

    result = await client.put("/things/", json={"name": "foo"})

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


@pytest.mark.asyncio
async def test_base_url_returns_configured_root(client: ProlificClient) -> None:
    assert client.base_url == "https://api.prolific.test"


@pytest.mark.asyncio
async def test_app_url_returns_configured_root(client: ProlificClient) -> None:
    assert client.app_url == "https://app.prolific.test"


@pytest.mark.asyncio
@respx.mock
async def test_post_with_headers_returns_body_and_headers(client: ProlificClient) -> None:
    respx.post("https://api.prolific.test/api/v1/things/").mock(
        return_value=httpx.Response(201, json={"id": "x"}, headers={"X-Custom": "abc"})
    )

    body, headers = await client.post_with_headers("/things/")

    assert body == {"id": "x"}
    assert headers["X-Custom"] == "abc"


@pytest.mark.asyncio
@respx.mock
async def test_post_with_headers_raises_on_error(client: ProlificClient) -> None:
    respx.post("https://api.prolific.test/api/v1/boom/").mock(
        return_value=httpx.Response(400, json={"detail": "bad"})
    )

    with pytest.raises(ProlificAPIError):
        await client.post_with_headers("/boom/")


@pytest.mark.asyncio
@respx.mock
async def test_post_text_returns_raw_text_not_json_decoded(client: ProlificClient) -> None:
    respx.post("https://api.prolific.test/api/v1/things.csv").mock(
        return_value=httpx.Response(200, text="a,b\n1,2\n")
    )

    result = await client.post_text("/things.csv")

    assert result == "a,b\n1,2\n"


@pytest.mark.asyncio
@respx.mock
async def test_post_text_raises_on_error(client: ProlificClient) -> None:
    respx.post("https://api.prolific.test/api/v1/boom.csv").mock(
        return_value=httpx.Response(500, text="server exploded")
    )

    with pytest.raises(ProlificAPIError) as excinfo:
        await client.post_text("/boom.csv")

    assert excinfo.value.body == "server exploded"


@pytest.mark.asyncio
@respx.mock
async def test_delete_sends_request_and_returns_none_on_204(client: ProlificClient) -> None:
    route = respx.delete("https://api.prolific.test/api/v1/things/1/").mock(
        return_value=httpx.Response(204)
    )

    result = await client.delete("/things/1/")

    assert route.called
    assert result is None


@pytest.mark.asyncio
@respx.mock
async def test_delete_raises_on_error(client: ProlificClient) -> None:
    respx.delete("https://api.prolific.test/api/v1/things/1/").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )

    with pytest.raises(ProlificAPIError):
        await client.delete("/things/1/")


@pytest.mark.parametrize(
    "method", ["get", "post", "patch", "put", "delete", "post_text", "post_with_headers"]
)
@respx.mock
async def test_default_client_sends_client_identity(config: Config, method: str) -> None:
    http_method = "POST" if method.startswith("post") else method.upper()
    route = respx.request(http_method, "https://api.prolific.test/api/v1/things/").mock(
        return_value=httpx.Response(200, json={})
    )
    prolific = ProlificClient(config=config)
    try:
        await getattr(prolific, method)("/things/")
    finally:
        await prolific.aclose()

    sent = route.calls.last.request
    assert sent.headers["x-prolific-client"] == f"mcp/{__version__}"
    assert sent.headers["user-agent"] == "prolific-mcp/0.0.1"
    assert sent.headers["authorization"] == "Token test-token-123456"


@pytest.mark.parametrize("identity", [None, "custom-client/1.2.3"])
@respx.mock
async def test_injected_client_gets_default_identity_without_overwriting_override(
    config: Config, identity: str | None
) -> None:
    route = respx.get("https://api.prolific.test/api/v1/things/").mock(
        return_value=httpx.Response(200, json={})
    )
    headers = {"x-prolific-client": identity} if identity is not None else {}
    async with httpx.AsyncClient(base_url=f"{config.base_url}/api/v1", headers=headers) as injected:
        prolific = ProlificClient(config=config, client=injected)
        await prolific.get("/things/")

    assert route.calls.last.request.headers.get("x-prolific-client") == (
        identity or f"mcp/{__version__}"
    )
