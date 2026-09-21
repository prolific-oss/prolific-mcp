from collections.abc import Callable
from typing import Any, TypeVar

from fastmcp import FastMCP

from prolific_mcp import __version__

mcp: FastMCP = FastMCP("prolific", version=__version__)

F = TypeVar("F", bound=Callable[..., Any])


def stable_tool() -> Callable[[F], F]:
    """Register a tool as `stability: "stable"` — proven, safe to rely on."""
    return mcp.tool(meta={"stability": "stable"})


def experimental_tool() -> Callable[[F], F]:
    """Register a tool as `stability: "experimental"` — new/unproven, may change."""
    return mcp.tool(meta={"stability": "experimental"})


import prolific_mcp.tools  # noqa: E402, F401  -- side-effect: register tools
