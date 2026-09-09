from typing import Any, Literal

from pydantic import BaseModel, Field

from prolific_mcp import __version__
from prolific_mcp.client import get_client
from prolific_mcp.server import mcp

Stability = Literal["stable", "experimental"]

_KNOWN_STABILITY_VALUES: tuple[Stability, ...] = ("stable", "experimental")
_DEFAULT_STABILITY: Stability = "experimental"


def _stability(meta: dict[str, Any] | None) -> Stability:
    """Map a tool's `meta["stability"]` to a stability label.

    Tools opt in to `stable` via `@mcp.tool(meta={"stability": "stable"})`.
    `meta` (not `tags`) is the documented FastMCP extension point for
    custom, client-visible metadata — it's passed through to every MCP
    client as the tool's `_meta` field on `tools/list`, unlike tags, which
    are only conditionally surfaced under a nested `_meta._fastmcp.tags`
    key. Anything without a recognized `stability` value defaults to
    `experimental` so a new tool never silently looks production-ready
    before anyone has said so.
    """
    value = (meta or {}).get("stability")
    for candidate in _KNOWN_STABILITY_VALUES:
        if value == candidate:
            return candidate
    return _DEFAULT_STABILITY


class ToolCapability(BaseModel):
    name: str = Field(description="Registered MCP tool name.")
    description: str | None = Field(default=None, description="Tool docstring shown to clients.")
    stability: Stability = Field(description="`stable` or `experimental`.")


class ServerCapabilities(BaseModel):
    server_version: str = Field(description="prolific-mcp package version.")
    api_base_url: str = Field(description="Prolific API root this server targets (`PROLIFIC_URL`).")
    tools: list[ToolCapability] = Field(description="Every currently enabled tool on this server.")


@mcp.tool(meta={"stability": "stable"})
async def get_capabilities() -> ServerCapabilities:
    """Report this server's version, target Prolific API, and registered tools.

    Call this first when you need to know what this MCP server can do
    right now — e.g. to check whether a tool exists before calling it, or
    to confirm which Prolific environment (`PROLIFIC_URL`) it's wired up to.
    """
    tools = await mcp.get_tools()
    capabilities = sorted(
        (
            ToolCapability(
                name=tool.name,
                description=tool.description,
                stability=_stability(tool.meta),
            )
            for tool in tools.values()
            if tool.enabled
        ),
        key=lambda tool: tool.name,
    )
    return ServerCapabilities(
        server_version=__version__,
        api_base_url=get_client().base_url,
        tools=capabilities,
    )
