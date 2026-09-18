import json

import httpx
import pytest
import respx

from prolific_mcp.client import ProlificClient
from prolific_mcp.tools.submissions import (
    bulk_approve_submissions,
    get_submission_counts,
    list_submissions,
)


@pytest.mark.asyncio
@respx.mock
async def test_list_submissions_passes_query_params(installed_client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/studies/study_1/submissions/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    await list_submissions(study_id="study_1", limit=10, offset=5)

    sent = route.calls.last.request
    assert sent.url.params["limit"] == "10"
    assert sent.url.params["offset"] == "5"


@pytest.mark.asyncio
@respx.mock
async def test_get_submission_counts_hits_counts_endpoint(
    installed_client: ProlificClient,
) -> None:
    route = respx.get("https://api.prolific.test/api/v1/studies/study_1/submissions/counts/").mock(
        return_value=httpx.Response(200, json={"ACTIVE": 3, "APPROVED": 7, "TOTAL": 10})
    )

    result = await get_submission_counts(study_id="study_1")

    assert route.called
    assert result == {"ACTIVE": 3, "APPROVED": 7, "TOTAL": 10}


@pytest.mark.asyncio
@respx.mock
async def test_bulk_approve_by_submission_ids(installed_client: ProlificClient) -> None:
    route = respx.post("https://api.prolific.test/api/v1/submissions/bulk-approve/").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    result = await bulk_approve_submissions(submission_ids=["sub_1", "sub_2"])

    assert result == {"message": "queued"}
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"submission_ids": ["sub_1", "sub_2"]}


@pytest.mark.asyncio
@respx.mock
async def test_bulk_approve_by_study_and_participant_ids(
    installed_client: ProlificClient,
) -> None:
    route = respx.post("https://api.prolific.test/api/v1/submissions/bulk-approve/").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    await bulk_approve_submissions(study_id="study_1", participant_ids=["p1", "p2"])

    sent = json.loads(route.calls.last.request.content)
    assert sent == {"study_id": "study_1", "participant_ids": ["p1", "p2"]}


@pytest.mark.asyncio
@respx.mock
async def test_bulk_approve_rejects_both_submission_and_participant_ids(
    installed_client: ProlificClient,
) -> None:
    route = respx.post("https://api.prolific.test/api/v1/submissions/bulk-approve/").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    with pytest.raises(ValueError, match="not both"):
        await bulk_approve_submissions(
            submission_ids=["sub_1"], study_id="study_1", participant_ids=["p1"]
        )

    assert route.called is False


@pytest.mark.asyncio
@respx.mock
async def test_bulk_approve_rejects_participant_ids_without_study_id(
    installed_client: ProlificClient,
) -> None:
    route = respx.post("https://api.prolific.test/api/v1/submissions/bulk-approve/").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    with pytest.raises(ValueError, match="study_id is required"):
        await bulk_approve_submissions(participant_ids=["p1"])

    assert route.called is False


@pytest.mark.asyncio
@respx.mock
async def test_bulk_approve_rejects_no_ids_at_all(installed_client: ProlificClient) -> None:
    route = respx.post("https://api.prolific.test/api/v1/submissions/bulk-approve/").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    with pytest.raises(ValueError, match="Provide either"):
        await bulk_approve_submissions()

    assert route.called is False
