"""Importing this package registers all tools on the FastMCP instance."""

from prolific_mcp.tools import (
    capabilities,
    collections,
    eligibility,
    filter_sets,
    filters,
    projects,
    studies,
    submissions,
    webhooks,
    workspaces,
)

__all__ = [
    "capabilities",
    "collections",
    "eligibility",
    "filter_sets",
    "filters",
    "projects",
    "studies",
    "submissions",
    "webhooks",
    "workspaces",
]
