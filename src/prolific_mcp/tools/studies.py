from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from prolific_mcp.client import get_client
from prolific_mcp.server import mcp


class CompletionCode(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: str = Field(description="Code participants enter to mark a completion outcome.")
    code_type: str = Field(
        description=(
            "Outcome this code represents, e.g. COMPLETED, FAILED_ATTENTION_CHECK, "
            "INCOMPATIBLE_DEVICE, NO_CONSENT, OTHER."
        )
    )
    actions: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional list of action objects (e.g. AUTOMATICALLY_APPROVE).",
    )


class StudyDraft(BaseModel):
    """Payload for `POST /api/v1/studies/`. Unknown fields are forwarded as-is."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Public title participants see.")
    internal_name: str | None = Field(
        default=None,
        description="Optional reference name only the research team sees.",
    )
    description: str = Field(description="Description shown to participants on the listing.")
    external_study_url: str = Field(description="URL where the study runs (e.g. Qualtrics link).")
    prolific_id_option: str = Field(
        description=(
            "How participants supply their Prolific ID. One of: "
            "`url_parameters`, `question`, `not_required`."
        ),
    )
    completion_codes: list[CompletionCode] = Field(
        description="Codes that participants paste back to mark completion outcomes."
    )
    total_available_places: int = Field(ge=1, description="How many participants you want.")
    estimated_completion_time: int = Field(ge=1, description="Expected duration in minutes.")
    reward: int = Field(
        ge=0,
        description="Reward per participant in the study currency, in pence/cents.",
    )
    device_compatibility: list[str] = Field(
        default_factory=list,
        description="Allowed devices: `desktop`, `tablet`, `mobile`.",
    )
    peripheral_requirements: list[str] = Field(
        default_factory=list,
        description="Hardware/software requirements, e.g. `audio`, `microphone`, `camera`.",
    )
    filters: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Eligibility filters, shaped like entries from `get_filters`.",
    )
    workspace_id: str | None = Field(default=None, description="Workspace owning the study.")
    project: str | None = Field(default=None, description="Project ID within the workspace.")


@mcp.tool
async def list_studies(
    state: Annotated[
        str | None,
        Field(
            description=(
                "Filter by status, e.g. `UNPUBLISHED`, `ACTIVE`, `COMPLETED`, `PAUSED`. "
                "Omit to return studies in every state."
            ),
        ),
    ] = None,
    page: Annotated[int, Field(ge=1, description="1-based page number.")] = 1,
    page_size: Annotated[int, Field(ge=1, le=200, description="Studies per page.")] = 50,
    search: Annotated[
        str | None,
        Field(description="Free-text search over study name / internal_name."),
    ] = None,
) -> Any:
    """List studies the current API token can see.

    Default ordering is most-recently-created first. Pair with `view_study`
    to drill into a specific entry.
    """
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if state is not None:
        params["state"] = state
    if search is not None:
        params["search"] = search
    return await get_client().get("/studies/", params=params)


@mcp.tool
async def view_study(
    study_id: Annotated[str, Field(description="ID of the study to fetch.")],
) -> Any:
    """Fetch the full record for a single study.

    Use this after `list_studies` when the researcher wants details that
    don't appear in the list view (filters, completion codes, reward
    breakdown, current status).
    """
    return await get_client().get(f"/studies/{study_id}/")


@mcp.tool
async def create_study(study: StudyDraft) -> Any:
    """Create a draft (unpublished) study on Prolific.

    The returned study has status `UNPUBLISHED`; call `publish_study`
    with its `id` once the researcher is ready to launch.
    """
    return await get_client().post("/studies/", json=study.model_dump(exclude_none=True))


@mcp.tool
async def publish_study(
    study_id: Annotated[str, Field(description="ID of the study to publish.")],
) -> Any:
    """Publish a draft study so it becomes visible to participants.

    Wraps `POST /studies/{id}/transition/` with `action=PUBLISH`.

    Ask for approval each time.
    """
    return await get_client().post(
        f"/studies/{study_id}/transition/",
        json={"action": "PUBLISH"},
    )
