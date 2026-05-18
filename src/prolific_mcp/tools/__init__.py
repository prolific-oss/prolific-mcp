"""Importing this package registers all tools on the FastMCP instance."""

from prolific_mcp.tools import (
    eligibility,
    filter_sets,
    filters,
    projects,
    studies,
    workspaces,
)

__all__ = [
    "eligibility",
    "filter_sets",
    "filters",
    "projects",
    "studies",
    "workspaces",
]
