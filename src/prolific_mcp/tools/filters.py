from typing import Any

from prolific_mcp.client import get_client
from prolific_mcp.server import mcp


@mcp.tool
async def get_filters() -> Any:
    """List every participant filter the current API token can use.

    Use this first to discover what demographic, behavioural, or custom
    requirements the researcher can apply when designing a study.
    """
    return await get_client().get("/filters/")
