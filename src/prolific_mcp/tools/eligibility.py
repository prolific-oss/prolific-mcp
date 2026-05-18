from typing import Annotated, Any

from pydantic import Field

from prolific_mcp.client import get_client
from prolific_mcp.server import mcp


@mcp.tool
async def get_eligibility_count(
    filters: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description=(
                "List of filter objects matching the shape returned by `get_filters` "
                "(filter_id plus selected_values / selected_range). Optional — "
                "an empty list counts everyone."
            ),
        ),
    ] = None,
    workspace_id: Annotated[
        str | None,
        Field(
            description=(
                "Workspace to scope the count to. If omitted, the API falls back to "
                "the current user's default workspace."
            ),
        ),
    ] = None,
    study_type: Annotated[
        str,
        Field(
            description="One of `STUDY_TYPE_SINGLE` (default) or `STUDY_TYPE_REP_SAMPLE`.",
        ),
    ] = "STUDY_TYPE_SINGLE",
) -> Any:
    """Estimate how many Prolific participants match the given filter criteria.

    Call this before publishing a study so the researcher knows whether
    their filters yield enough eligible participants.
    """
    payload: dict[str, Any] = {"filters": filters or [], "study_type": study_type}
    if workspace_id is not None:
        payload["workspace_id"] = workspace_id
    return await get_client().post("/eligibility-count/", json=payload)
