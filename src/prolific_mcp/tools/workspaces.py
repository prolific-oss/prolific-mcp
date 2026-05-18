from typing import Any

from prolific_mcp.client import get_client
from prolific_mcp.server import mcp


@mcp.tool
async def list_workspaces() -> Any:
    """List the workspaces the current API token has access to.

    Workspaces are the top-level container in Prolific — projects and
    studies live inside one. Use this when the researcher hasn't named
    a workspace yet, or before listing projects/studies for one.
    """
    return await get_client().get("/workspaces/")
