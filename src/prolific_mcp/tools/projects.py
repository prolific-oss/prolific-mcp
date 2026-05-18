from typing import Annotated, Any

from pydantic import Field

from prolific_mcp.client import get_client
from prolific_mcp.server import mcp


@mcp.tool
async def list_projects(
    workspace_id: Annotated[str, Field(description="ID of the workspace to list projects in.")],
) -> Any:
    """List the projects inside a workspace.

    Projects group related studies. Use this after `list_workspaces` to
    show the researcher where a new study could land, or to scope a
    `list_studies` call to a specific project.
    """
    return await get_client().get(f"/workspaces/{workspace_id}/projects/")
