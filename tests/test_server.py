from prolific_mcp import __version__
from prolific_mcp.server import mcp


def test_server_reports_package_version_not_fastmcp_library_version() -> None:
    """FastMCP() defaults `version` to the fastmcp library's own version if
    not passed explicitly — this pins it to prolific-mcp's actual version,
    which is also what `get_capabilities` reports, so the two stay in sync.
    """
    assert mcp.version == __version__
