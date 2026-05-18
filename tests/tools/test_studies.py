import json

import httpx
import pytest
import respx

from prolific_mcp.client import ProlificClient
from prolific_mcp.tools.studies import (
    CompletionCode,
    StudyDraft,
    create_study,
    list_studies,
    view_study,
)


def _draft() -> StudyDraft:
    return StudyDraft(
        name="Memory test",
        internal_name="memory-test-2026",
        description="A short memory recall task.",
        external_study_url="https://example.com/study?PROLIFIC_PID={{%PROLIFIC_PID%}}",
        prolific_id_option="url_parameters",
        completion_codes=[CompletionCode(code="ABC123", code_type="COMPLETED")],
        total_available_places=50,
        estimated_completion_time=15,
        reward=500,
    )


@pytest.mark.asyncio
@respx.mock
async def test_create_study_posts_dump(installed_client: ProlificClient) -> None:
    route = respx.post("https://api.prolific.test/api/v1/studies/").mock(
        return_value=httpx.Response(201, json={"id": "study_1", "status": "UNPUBLISHED"})
    )

    result = await create_study(study=_draft())

    assert result == {"id": "study_1", "status": "UNPUBLISHED"}
    sent = json.loads(route.calls.last.request.content)
    assert sent["name"] == "Memory test"
    assert sent["total_available_places"] == 50
    assert sent["completion_codes"][0]["code"] == "ABC123"
    assert "workspace_id" not in sent  # exclude_none drops unset optionals


@pytest.mark.asyncio
@respx.mock
async def test_list_studies_passes_filter_params(installed_client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/studies/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    await list_studies(state="ACTIVE", page=2, page_size=25, search="memory")

    sent = route.calls.last.request
    assert sent.url.params["state"] == "ACTIVE"
    assert sent.url.params["page"] == "2"
    assert sent.url.params["page_size"] == "25"
    assert sent.url.params["search"] == "memory"


@pytest.mark.asyncio
@respx.mock
async def test_list_studies_omits_unset_optionals(installed_client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/studies/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    await list_studies()

    sent = route.calls.last.request
    assert "state" not in sent.url.params
    assert "search" not in sent.url.params
    assert sent.url.params["page"] == "1"
    assert sent.url.params["page_size"] == "50"


@pytest.mark.asyncio
@respx.mock
async def test_view_study_hits_detail_endpoint(installed_client: ProlificClient) -> None:
    route = respx.get("https://api.prolific.test/api/v1/studies/study_42/").mock(
        return_value=httpx.Response(200, json={"id": "study_42", "status": "ACTIVE"})
    )

    result = await view_study(study_id="study_42")

    assert route.called
    assert result == {"id": "study_42", "status": "ACTIVE"}


@pytest.mark.asyncio
@respx.mock
async def test_publish_study_calls_transition(installed_client: ProlificClient) -> None:
    route = respx.post("https://api.prolific.test/api/v1/studies/study_1/transition/").mock(
        return_value=httpx.Response(200, json={"id": "study_1", "status": "ACTIVE"})
    )

    result = await publish_study(study_id="study_1")

    assert result == {"id": "study_1", "status": "ACTIVE"}
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"action": "PUBLISH"}
