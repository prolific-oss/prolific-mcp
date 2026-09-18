from typing import Annotated, Any

from pydantic import Field

from prolific_mcp.client import get_client
from prolific_mcp.server import experimental_tool


@experimental_tool()
async def list_submissions(
    study_id: Annotated[str, Field(description="ID of the study to list submissions for.")],
    limit: Annotated[int, Field(ge=1, le=500, description="Page size.")] = 200,
    offset: Annotated[int, Field(ge=0, description="Pagination offset.")] = 0,
) -> Any:
    """List submissions for a study — one record per participant attempt.

    Pair with `get_submission_counts` for a status breakdown, or
    `bulk_approve_submissions` to approve a batch of them.
    """
    return await get_client().get(
        f"/studies/{study_id}/submissions/",
        params={"limit": limit, "offset": offset},
    )


@experimental_tool()
async def get_submission_counts(
    study_id: Annotated[str, Field(description="ID of the study to get submission counts for.")],
) -> Any:
    """Get submission counts grouped by status for a study.

    Returns a flat object keyed by status (e.g. `ACTIVE`, `APPROVED`,
    `AWAITING REVIEW`, `REJECTED`, `RETURNED`, `TOTAL`) — a quick summary
    without paging through `list_submissions`.
    """
    return await get_client().get(f"/studies/{study_id}/submissions/counts/")


@experimental_tool()
async def bulk_approve_submissions(
    submission_ids: Annotated[
        list[str] | None,
        Field(
            description="Submission IDs to approve. Not combinable with study_id/participant_ids."
        ),
    ] = None,
    study_id: Annotated[
        str | None,
        Field(description="Study the participant_ids belong to. Required with participant_ids."),
    ] = None,
    participant_ids: Annotated[
        list[str] | None,
        Field(description="Participant IDs to approve within study_id. Requires study_id."),
    ] = None,
) -> Any:
    """Bulk-approve submissions, by submission ID or by study + participant ID.

    Provide either `submission_ids` alone, or `study_id` together with
    `participant_ids` — never a mix. This only approves; there is no
    equivalent tool for rejecting or requesting a return, by design (per
    Marcus's own ask on DCT-368: automate clearly-safe approvals, never
    rejection).

    Fire-and-forget: the response is a generic acknowledgement that the
    request was queued, not per-submission results — call
    `list_submissions` or `get_submission_counts` afterward to confirm.
    Idempotent — the API deduplicates identical requests (same caller,
    same IDs) for 5 minutes, so retrying on a timeout is safe.
    """
    has_submission_ids = bool(submission_ids)
    has_participant_ids = bool(participant_ids)

    if has_submission_ids and (has_participant_ids or study_id is not None):
        raise ValueError(
            "Provide either submission_ids, or study_id with participant_ids, not both."
        )
    if has_participant_ids and study_id is None:
        raise ValueError("study_id is required when using participant_ids.")
    if not has_submission_ids and not has_participant_ids:
        raise ValueError("Provide either submission_ids, or study_id with participant_ids.")

    payload: dict[str, Any] = {}
    if has_submission_ids:
        payload["submission_ids"] = submission_ids
    else:
        payload["study_id"] = study_id
        payload["participant_ids"] = participant_ids

    return await get_client().post("/submissions/bulk-approve/", json=payload)
