"""Importing this package registers all tools on the FastMCP instance."""

from prolific_mcp.tools import (
    capabilities,
    eligibility,
    filter_sets,
    filters,
    projects,
    studies,
    workspaces,
)

__all__ = [
    "capabilities",
    "eligibility",
    "filter_sets",
    "filters",
    "projects",
    "studies",
    "workspaces",
]
