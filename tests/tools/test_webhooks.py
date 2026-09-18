import json
import uuid

import httpx
import pytest
import respx

from prolific_mcp.client import ProlificClient
from prolific_mcp.errors import ProlificAPIError
from prolific_mcp.tools.webhooks import (
    create_webhook_secret,
    create_webhook_subscription,
    delete_webhook_subscription,
    ensure_webhook_secret,
    list_webhook_event_types,
    list_webhook_events,
    list_webhook_subscriptions,
    update_webhook_subscription,
)


@pytest.mark.asyncio
@respx.mock
async def test_ensure_webhook_secret_reports_exists_true_without_leaking_value(
    installed_client: ProlificClient,
) -> None:
    respx.get("https://api.prolific.test/api/v1/hooks/secrets/").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"id": "sec_1", "value": "super-secret", "workspace_id": "ws_1"}]},
        )
    )

    result = await ensure_webhook_secret(workspace_id="ws_1")

    assert result.workspace_id == "ws_1"
    assert result.exists is True
    assert "value" not in result.model_dump()


@pytest.mark.asyncio
@respx.mock
async def test_ensure_webhook_secret_reports_exists_false(
    installed_client: ProlificClient,
) -> None:
    respx.get("https://api.prolific.test/api/v1/hooks/secrets/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    result = await ensure_webhook_secret(workspace_id="ws_1")

    assert result.exists is False


@pytest.mark.asyncio
@respx.mock
async def test_create_webhook_secret_creates_when_none_exists(
    installed_client: ProlificClient,
) -> None:
    respx.get("https://api.prolific.test/api/v1/hooks/secrets/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    respx.post("https://api.prolific.test/api/v1/hooks/secrets/").mock(
        return_value=httpx.Response(
            201, json={"id": "sec_1", "value": "brand-new-secret", "workspace_id": "ws_1"}
        )
    )

    result = await create_webhook_secret(workspace_id="ws_1")

    assert result.value == "brand-new-secret"


@pytest.mark.asyncio
@respx.mock
async def test_create_webhook_secret_refuses_to_rotate_without_confirmation(
    installed_client: ProlificClient,
) -> None:
    respx.get("https://api.prolific.test/api/v1/hooks/secrets/").mock(
        return_value=httpx.Response(
            200, json={"results": [{"id": "sec_1", "value": "existing", "workspace_id": "ws_1"}]}
        )
    )
    create_route = respx.post("https://api.prolific.test/api/v1/hooks/secrets/").mock(
        return_value=httpx.Response(
            201, json={"id": "sec_2", "value": "new", "workspace_id": "ws_1"}
        )
    )

    with pytest.raises(ValueError, match="confirm_rotation"):
        await create_webhook_secret(workspace_id="ws_1")

    assert create_route.called is False


@pytest.mark.asyncio
@respx.mock
async def test_create_webhook_secret_rotates_when_confirmed(
    installed_client: ProlificClient,
) -> None:
    respx.get("https://api.prolific.test/api/v1/hooks/secrets/").mock(
        return_value=httpx.Response(
            200, json={"results": [{"id": "sec_1", "value": "existing", "workspace_id": "ws_1"}]}
        )
    )
    respx.post("https://api.prolific.test/api/v1/hooks/secrets/").mock(
        return_value=httpx.Response(
            201, json={"id": "sec_2", "value": "rotated", "workspace_id": "ws_1"}
        )
    )

    result = await create_webhook_secret(workspace_id="ws_1", confirm_rotation=True)

    assert result.value == "rotated"


@pytest.mark.asyncio
@respx.mock
async def test_create_webhook_subscription_creates_and_confirms(
    installed_client: ProlificClient,
) -> None:
    confirm_token = uuid.uuid4().hex
    create_route = respx.post("https://api.prolific.test/api/v1/hooks/subscriptions/").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "sub_1",
                "event_type": "study.status.change",
                "target_url": "https://example.com/hook",
                "is_enabled": False,
                "workspace_id": "ws_1",
            },
            headers={"X-Hook-Secret": confirm_token},
        )
    )
    confirm_route = respx.post("https://api.prolific.test/api/v1/hooks/subscriptions/sub_1/").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "sub_1",
                "event_type": "study.status.change",
                "target_url": "https://example.com/hook",
                "is_enabled": True,
                "workspace_id": "ws_1",
            },
        )
    )

    result = await create_webhook_subscription(
        workspace_id="ws_1",
        event_type="study.status.change",
        target_url="https://example.com/hook",
    )

    assert result["is_enabled"] is True
    create_sent = json.loads(create_route.calls.last.request.content)
    assert create_sent == {
        "workspace_id": "ws_1",
        "event_type": "study.status.change",
        "target_url": "https://example.com/hook",
    }
    confirm_sent = json.loads(confirm_route.calls.last.request.content)
    assert confirm_sent == {"secret": confirm_token}


@pytest.mark.asyncio
@respx.mock
async def test_create_webhook_subscription_confirm_failure_includes_subscription_id(
    installed_client: ProlificClient,
) -> None:
    respx.post("https://api.prolific.test/api/v1/hooks/subscriptions/").mock(
        return_value=httpx.Response(
            201,
            json={"id": "sub_1", "is_enabled": False},
            headers={"X-Hook-Secret": uuid.uuid4().hex},
        )
    )
    respx.post("https://api.prolific.test/api/v1/hooks/subscriptions/sub_1/").mock(
        return_value=httpx.Response(400, json={"detail": "secret mismatch"})
    )

    with pytest.raises(ProlificAPIError, match="sub_1"):
        await create_webhook_subscription(
            workspace_id="ws_1",
            event_type="study.status.change",
            target_url="https://example.com/hook",
        )


@pytest.mark.asyncio
@respx.mock
async def test_list_webhook_subscriptions_defaults_to_enabled_true(
    installed_client: ProlificClient,
) -> None:
    route = respx.get("https://api.prolific.test/api/v1/hooks/subscriptions").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    await list_webhook_subscriptions(workspace_id="ws_1")

    sent = route.calls.last.request
    assert sent.url.params["is_enabled"] == "true"
    assert sent.url.params["workspace_id"] == "ws_1"


@pytest.mark.asyncio
@respx.mock
async def test_list_webhook_subscriptions_can_filter_disabled(
    installed_client: ProlificClient,
) -> None:
    route = respx.get("https://api.prolific.test/api/v1/hooks/subscriptions").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    await list_webhook_subscriptions(workspace_id="ws_1", enabled=False)

    assert route.calls.last.request.url.params["is_enabled"] == "false"


@pytest.mark.asyncio
@respx.mock
async def test_update_webhook_subscription_sends_only_passed_fields(
    installed_client: ProlificClient,
) -> None:
    route = respx.patch("https://api.prolific.test/api/v1/hooks/subscriptions/sub_1/").mock(
        return_value=httpx.Response(200, json={"id": "sub_1", "is_enabled": False})
    )

    await update_webhook_subscription(subscription_id="sub_1", is_enabled=False)

    sent = json.loads(route.calls.last.request.content)
    assert sent == {"is_enabled": False}


@pytest.mark.asyncio
@respx.mock
async def test_delete_webhook_subscription_calls_delete(
    installed_client: ProlificClient,
) -> None:
    route = respx.delete("https://api.prolific.test/api/v1/hooks/subscriptions/sub_1/").mock(
        return_value=httpx.Response(204)
    )

    await delete_webhook_subscription(subscription_id="sub_1")

    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_list_webhook_events_hits_subscription_events_endpoint(
    installed_client: ProlificClient,
) -> None:
    route = respx.get("https://api.prolific.test/api/v1/hooks/subscriptions/sub_1/events/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    await list_webhook_events(subscription_id="sub_1", limit=10, offset=5)

    sent = route.calls.last.request
    assert sent.url.params["limit"] == "10"
    assert sent.url.params["offset"] == "5"


@pytest.mark.asyncio
@respx.mock
async def test_list_webhook_event_types(installed_client: ProlificClient) -> None:
    respx.get("https://api.prolific.test/api/v1/hooks/event-types/").mock(
        return_value=httpx.Response(
            200, json={"results": [{"event_type": "study.status.change", "description": "..."}]}
        )
    )

    result = await list_webhook_event_types()

    assert result["results"][0]["event_type"] == "study.status.change"
