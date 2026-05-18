"""Prolific MCP server."""

try:
    from prolific_mcp._version import __version__
except ImportError:
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
