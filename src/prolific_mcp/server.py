from fastmcp import FastMCP

from prolific_mcp import __version__

mcp: FastMCP = FastMCP("prolific", version=__version__)

import prolific_mcp.tools  # noqa: E402, F401  -- side-effect: register tools
