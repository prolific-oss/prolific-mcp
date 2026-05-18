from typing import Annotated, Any

from pydantic import Field

from prolific_mcp.client import get_client
from prolific_mcp.server import mcp


@mcp.tool
async def get_filter_sets(
    workspace_id: Annotated[str, Field(description="ID of the workspace to scope to.")],
    limit: Annotated[int, Field(ge=1, le=500, description="Page size.")] = 200,
    offset: Annotated[int, Field(ge=0, description="Pagination offset.")] = 0,
) -> Any:
    """List reusable filter sets within a workspace.

    Filter sets bundle a set of participant filters under a name so the
    researcher can reuse the same eligibility criteria across studies.
    """
    return await get_client().get(
        "/filter-sets/",
        params={"workspace_id": workspace_id, "limit": limit, "offset": offset},
    )


@mcp.tool
async def create_filter_set(
    workspace_id: Annotated[str, Field(description="Workspace that will own the filter set.")],
    name: Annotated[str, Field(description="Human-readable name shown in the dashboard.")],
    filters: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description=(
                "List of filter objects, each shaped like the entries returned by "
                "`get_filters` (typically `filter_id` plus `selected_values` or "
                "`selected_range`). Optional — omit or pass an empty list for an "
                "unfiltered set."
            ),
        ),
    ] = None,
) -> Any:
    """Create a reusable filter set in a workspace from a list of filters."""
    return await get_client().post(
        "/filter-sets/",
        json={"workspace_id": workspace_id, "name": name, "filters": filters or []},
    )
