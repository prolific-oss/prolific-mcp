from fastmcp import FastMCP

mcp: FastMCP = FastMCP("prolific")

import prolific_mcp.tools  # noqa: E402, F401  -- side-effect: register tools
