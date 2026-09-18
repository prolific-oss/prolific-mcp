import json

import httpx
import pytest
import respx
from pydantic import ValidationError

from prolific_mcp.client import ProlificClient
from prolific_mcp.errors import ProlificAPIError
from prolific_mcp.tools.collections import (
    CollectionContent,
    CollectionDraft,
    CollectionItem,
    TaskDetails,
    create_collection,
    export_collection,
    get_collection_export_status,
    list_collections,
    preview_collection,
    update_collection,
    view_collection,
)


def _task_details() -> TaskDetails:
    return TaskDetails(
        task_name="Label the image",
        task_introduction="You'll be shown a single image.",
        task_steps="1. Look at the image. 2. Pick the best label.",
    )


def _items() -> list[CollectionItem]:
    return [CollectionItem(order=0, page_items=[{"type": "instruction", "text": "Do the thing."}])]


def _draft() -> CollectionDraft:
    return CollectionDraft(
        workspace_id="ws_1",
        name="Image labelling",
        task_details=_task_details(),
        collection_items=_items(),
    )


@pytest.mark.asyncio
@respx.mock
async def test_create_collection_posts_dump(installed_client: ProlificClient) -> None:
    route = respx.post("https://api.prolific.test/api/v1/data-collection/collections").mock(
        return_value=httpx.Response(201, json={"id": "col_1", "name": "Image labelling"})
    )

    result = await create_collection(collection=_draft())

    assert result == {"id": "col_1", "name": "Image labelling"}
    sent = json.loads(route.calls.last.request.content)
    assert sent["workspace_id"] == "ws_1"
    assert sent["task_details"]["task_name"] == "Label the image"
    assert sent["collection_items"][0]["order"] == 0
    assert sent["collection_items"][0]["page_items"][0]["text"] == "Do the thing."


@pytest.mark.asyncio
@respx.mock
async def test_view_collection_hits_detail_endpoint(installed_client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/data-collection/collections/col_1").mock(
        return_value=httpx.Response(200, json={"id": "col_1"})
    )

    result = await view_collection(collection_id="col_1")

    assert route.called
    assert result == {"id": "col_1"}


@pytest.mark.asyncio
@respx.mock
async def test_list_collections_passes_query_params(installed_client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/data-collection/collections").mock(
        return_value=httpx.Response(200, json={"results": [], "meta": {"count": 0}})
    )

    await list_collections(workspace_id="ws_1", limit=50, offset=10)

    sent = route.calls.last.request
    assert sent.url.params["workspace_id"] == "ws_1"
    assert sent.url.params["limit"] == "50"
    assert sent.url.params["offset"] == "10"


@pytest.mark.asyncio
@respx.mock
async def test_update_collection_puts_full_replacement(installed_client: ProlificClient) -> None:
    route = respx.put("https://api.prolific.test/api/v1/data-collection/collections/col_1/").mock(
        return_value=httpx.Response(200, json={"id": "col_1"})
    )

    result = await update_collection(
        collection_id="col_1",
        collection=CollectionContent(
            name="Image labelling v2",
            task_details=_task_details(),
            collection_items=_items(),
        ),
    )

    assert result == {"id": "col_1"}
    sent = json.loads(route.calls.last.request.content)
    assert sent["name"] == "Image labelling v2"
    assert "workspace_id" not in sent


def test_collection_content_rejects_empty_items() -> None:
    with pytest.raises(ValidationError):
        CollectionContent(name="x", task_details=_task_details(), collection_items=[])


@pytest.mark.asyncio
@respx.mock
async def test_preview_collection_returns_app_url(installed_client: ProlificClient) -> None:
    respx.get("https://api.prolific.test/api/v1/data-collection/collections/col_1").mock(
        return_value=httpx.Response(200, json={"id": "col_1"})
    )

    result = await preview_collection(collection_id="col_1")

    assert result.collection_id == "col_1"
    assert result.preview_url == (
        "https://app.prolific.test/data-collection-tool/collections/col_1?preview=true"
    )


@pytest.mark.asyncio
@respx.mock
async def test_preview_collection_raises_when_not_found(installed_client: ProlificClient) -> None:
    respx.get("https://api.prolific.test/api/v1/data-collection/collections/missing").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )

    with pytest.raises(ProlificAPIError):
        await preview_collection(collection_id="missing")


@pytest.mark.asyncio
@respx.mock
async def test_export_collection_returns_generating_status(
    installed_client: ProlificClient,
) -> None:
    respx.post("https://api.prolific.test/api/v1/data-collection/collections/col_1/export").mock(
        return_value=httpx.Response(200, json={"status": "generating", "export_id": "exp_1"})
    )

    result = await export_collection(collection_id="col_1")

    assert result == {"status": "generating", "export_id": "exp_1"}


@pytest.mark.asyncio
@respx.mock
async def test_export_collection_returns_cached_complete_status(
    installed_client: ProlificClient,
) -> None:
    respx.post("https://api.prolific.test/api/v1/data-collection/collections/col_1/export").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "complete",
                "url": "https://example.com/export.zip",
                "expires_at": "2026-01-01T00:00:00Z",
            },
        )
    )

    result = await export_collection(collection_id="col_1")

    assert result["status"] == "complete"
    assert result["url"] == "https://example.com/export.zip"


@pytest.mark.asyncio
@respx.mock
async def test_get_collection_export_status_hits_poll_endpoint(
    installed_client: ProlificClient,
) -> None:
    route = respx.get(
        "https://api.prolific.test/api/v1/data-collection/collections/col_1/export/exp_1"
    ).mock(return_value=httpx.Response(200, json={"status": "complete", "url": "https://x/y.zip"}))

    result = await get_collection_export_status(collection_id="col_1", export_id="exp_1")

    assert route.called
    assert result["status"] == "complete"
