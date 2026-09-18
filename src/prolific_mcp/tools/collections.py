from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from prolific_mcp.client import get_client
from prolific_mcp.server import mcp


class TaskDetails(BaseModel):
    """Static task copy shown to participants working a collection."""

    model_config = ConfigDict(extra="allow")

    task_name: str = Field(description="Short name for the task shown to participants.")
    task_introduction: str = Field(
        description="Introductory copy shown to participants before the task steps."
    )
    task_steps: str = Field(description="Step-by-step instructions participants follow.")


class CollectionItem(BaseModel):
    """One page within a collection: its position and content blocks.

    The internal shape of each `page_items` entry isn't published by the
    API, so entries are passed through as opaque dicts rather than
    validated field-by-field.
    """

    model_config = ConfigDict(extra="allow")

    order: int = Field(ge=0, description="Position of this page within the collection.")
    page_items: list[dict[str, Any]] = Field(
        description="Content blocks/instructions shown on this page."
    )


class CollectionContent(BaseModel):
    """Fields shared by create and full-replacement update payloads."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Name of the collection.")
    task_details: TaskDetails = Field(description="Static task copy shown to participants.")
    collection_items: list[CollectionItem] = Field(
        min_length=1,
        description="Non-empty, ordered list of pages that make up the collection.",
    )


class CollectionDraft(CollectionContent):
    """Payload for `POST /api/v1/data-collection/collections`."""

    workspace_id: str = Field(description="Workspace that will own the collection.")


@mcp.tool(meta={"stability": "experimental"})
async def create_collection(collection: CollectionDraft) -> Any:
    """Create an AI Task Builder collection.

    Collections hold static task content (introduction, steps, and one or
    more pages of instructions) with no attached dataset. Unlike studies,
    there's no separate publish step or draft/live status here — the
    record this returns already reflects everything `view_collection`
    would show.
    """
    return await get_client().post(
        "/data-collection/collections",
        json=collection.model_dump(exclude_none=True),
    )


@mcp.tool(meta={"stability": "experimental"})
async def view_collection(
    collection_id: Annotated[str, Field(description="ID of the collection to fetch.")],
) -> Any:
    """Fetch the full record for a single collection.

    Collections have no separate status field — they're static content,
    fully present as soon as they're created. Use `list_collections` first
    if you don't already have an ID.
    """
    return await get_client().get(f"/data-collection/collections/{collection_id}")


class CollectionPreview(BaseModel):
    collection_id: str = Field(description="ID of the previewed collection.")
    preview_url: str = Field(
        description="Browser URL showing the collection as participants would see it."
    )


@mcp.tool(meta={"stability": "experimental"})
async def preview_collection(
    collection_id: Annotated[str, Field(description="ID of the collection to preview.")],
) -> CollectionPreview:
    """Get a browser preview URL for a collection, before publishing it.

    Confirms the collection exists (raises if not), then returns a link
    showing it as participants would see it — there's no API endpoint for
    this, it's a deterministic URL, matching what `prolific collection
    preview` opens locally in the CLI.
    """
    await get_client().get(f"/data-collection/collections/{collection_id}")
    preview_url = (
        f"{get_client().app_url}/data-collection-tool/collections/{collection_id}?preview=true"
    )
    return CollectionPreview(collection_id=collection_id, preview_url=preview_url)


@mcp.tool(meta={"stability": "experimental"})
async def list_collections(
    workspace_id: Annotated[str, Field(description="Workspace to list collections in.")],
    limit: Annotated[int, Field(ge=1, le=500, description="Page size.")] = 200,
    offset: Annotated[int, Field(ge=0, description="Pagination offset.")] = 0,
) -> Any:
    """List AI Task Builder collections in a workspace.

    Pair with `view_collection` to drill into a specific entry, or
    `update_collection` to replace one in full.
    """
    return await get_client().get(
        "/data-collection/collections",
        params={"workspace_id": workspace_id, "limit": limit, "offset": offset},
    )


@mcp.tool(meta={"stability": "experimental"})
async def update_collection(
    collection_id: Annotated[str, Field(description="ID of the collection to replace.")],
    collection: CollectionContent,
) -> Any:
    """Replace a collection's content in full.

    This is a full replacement (`PUT`), not a partial update — `name`,
    `task_details`, and every entry in `collection_items` must be supplied
    on every call, including content you want to keep unchanged. Anything
    omitted is removed. Call `view_collection` first, edit the result, and
    pass the whole thing back rather than building a payload from scratch.
    `workspace_id` cannot be changed here.
    """
    return await get_client().put(
        f"/data-collection/collections/{collection_id}/",
        json=collection.model_dump(exclude_none=True),
    )
