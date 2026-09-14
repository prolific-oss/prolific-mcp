import pytest

from prolific_mcp import __version__
from prolific_mcp.client import ProlificClient
from prolific_mcp.server import mcp
from prolific_mcp.tools.capabilities import get_capabilities

_EXISTING_TOOL_NAMES = {
    "get_filters",
    "get_filter_sets",
    "create_filter_set",
    "get_eligibility_count",
    "list_workspaces",
    "list_projects",
    "list_studies",
    "view_study",
    "create_study",
    "publish_study",
    "get_capabilities",
}


@pytest.mark.asyncio
async def test_reports_version_and_api_base_url(installed_client: ProlificClient) -> None:
    result = await get_capabilities.fn()

    assert result.server_version == __version__
    assert result.api_base_url == "https://api.prolific.test"


@pytest.mark.asyncio
async def test_lists_registered_tools_as_stable(installed_client: ProlificClient) -> None:
    result = await get_capabilities.fn()
    by_name = {tool.name: tool for tool in result.tools}

    assert _EXISTING_TOOL_NAMES <= by_name.keys()
    assert by_name["list_workspaces"].stability == "stable"
    assert by_name["get_capabilities"].stability == "stable"
    assert by_name["list_workspaces"].description


@pytest.mark.asyncio
async def test_tool_without_stability_meta_defaults_to_experimental(
    installed_client: ProlificClient,
) -> None:
    @mcp.tool
    async def _throwaway_tool() -> str:
        """Temporary tool registered only for this test."""
        return "ok"

    try:
        result = await get_capabilities.fn()
        by_name = {tool.name: tool for tool in result.tools}
        assert by_name["_throwaway_tool"].stability == "experimental"
    finally:
        mcp.remove_tool("_throwaway_tool")


@pytest.mark.asyncio
async def test_stability_reaches_the_wire_meta_directly(
    installed_client: ProlificClient,
) -> None:
    """`meta` (unlike `tags`) is passed straight through to every MCP client
    as the tool's `_meta` field on `tools/list` — this is what makes it the
    right mechanism for stability, not just something `get_capabilities`
    happens to be able to see.
    """
    tools = await mcp.get_tools()
    wire_tool = tools["list_workspaces"].to_mcp_tool()

    assert wire_tool.meta is not None
    assert wire_tool.meta["stability"] == "stable"
