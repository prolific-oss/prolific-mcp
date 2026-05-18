# prolific-mcp

[![PyPI](https://img.shields.io/pypi/v/prolific-mcp.svg)](https://pypi.org/project/prolific-mcp/)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-listed-blue)](https://registry.modelcontextprotocol.io/v0/servers?search=prolific)

A [Model Context Protocol](https://modelcontextprotocol.io/) server bridging LLM agents to the [Prolific](https://www.prolific.com) public API. Built with [FastMCP](https://gofastmcp.com).

Listed on the [official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=prolific) — discoverable from Claude Desktop, Cursor, Claude Code, and other MCP-aware clients.

## What it does

Exposes a small set of tools so an LLM can help a researcher design and launch a study on Prolific:

| Tool | Prolific endpoint |
|---|---|
| `get_filters` | `GET /api/v1/filters/` |
| `get_filter_sets` | `GET /api/v1/filter-sets/` |
| `create_filter_set` | `POST /api/v1/filter-sets/` |
| `get_eligibility_count` | `POST /api/v1/eligibility-count/` |
| `create_study` | `POST /api/v1/studies/` |
| `publish_study` | `POST /api/v1/studies/{id}/transition/` |

## Requirements

- Python 3.11+
- A Prolific API token (create one at <https://app.prolific.com>)

## Quickstart

Install and run from PyPI with [`uv`](https://docs.astral.sh/uv/):

```bash
export PROLIFIC_TOKEN=your_token_here
uvx prolific-mcp
```

Or from a checkout:

```bash
uv sync
export PROLIFIC_TOKEN=your_token_here
uv run prolific-mcp
```

The server defaults to stdio and is intended to be launched by an MCP client (Claude Desktop, Cursor, etc.).

### Local development (HTTP mode)

Stdio means the client owns the process — you can't see the server's logs in your own terminal. For local iteration, run over streamable HTTP instead:

```bash
PROLIFIC_TOKEN=your_token_here uv run prolific-mcp --http
# logs stream to your terminal; server listens on http://127.0.0.1:8765/mcp

# in another terminal, register it with Claude Code:
claude mcp add prolific --transport http http://127.0.0.1:8765/mcp
```

Override host/port with `--host` / `--port` if 8765 is taken.

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PROLIFIC_TOKEN` | yes | — | Prolific API token, sent as `Authorization: Token …` |
| `PROLIFIC_URL` | no | `https://api.prolific.com` | Base URL of the Prolific API |

## Claude Desktop configuration

```json
{
  "mcpServers": {
    "prolific": {
      "command": "uvx",
      "args": ["prolific-mcp"],
      "env": { "PROLIFIC_TOKEN": "your_token_here" }
    }
  }
}
```

## Development

```bash
uv sync
uv run pytest          # tests
uv run mypy            # type-check
uv run ruff check .    # lint
uv run ruff format .   # format
```

## Docker

```bash
docker build -t mcp/prolific .
docker run -i --rm -e PROLIFIC_TOKEN=$PROLIFIC_TOKEN mcp/prolific
```
