# prolific-mcp

[![CI](https://github.com/prolific-oss/prolific-mcp/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/prolific-oss/prolific-mcp/actions/workflows/ci.yml)
[![Security](https://github.com/prolific-oss/prolific-mcp/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/prolific-oss/prolific-mcp/actions/workflows/security.yml)

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

Stdio gives the client ownership of the process, which hides server logs. For local iteration, run over streamable HTTP instead so logs stream to your terminal:

```bash
PROLIFIC_TOKEN=your_token_here uv run prolific-mcp --http
# server listens on http://127.0.0.1:8765/mcp

# register it with Claude Code in another terminal:
claude mcp add prolific --transport http http://127.0.0.1:8765/mcp
```

Override host/port with `--host` / `--port` if `8765` is in use.

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PROLIFIC_TOKEN` | yes | — | Prolific API token, sent as `Authorization: Token …` |
| `PROLIFIC_URL` | no | `https://api.prolific.com` | Base URL of the Prolific API |

## Use with MCP clients

### Claude Desktop

Each [GitHub Release](https://github.com/prolific-oss/prolific-mcp/releases) attaches a `.mcpb` bundle per platform (`darwin-arm64`, `darwin-x86_64`, `linux-x86_64`, `windows-x86_64`). Download the file for your platform and open it — Claude Desktop will show an install dialog and prompt for your `PROLIFIC_TOKEN`.

To configure manually instead, add the server to your Claude Desktop config:

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

### Claude Code

```bash
claude mcp add prolific \
  -e PROLIFIC_TOKEN=your_token_here \
  -- uvx prolific-mcp
```

To pin a specific version, replace `uvx prolific-mcp` with `uvx prolific-mcp==<version>`.

### Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.prolific]
command = "uvx"
args = ["prolific-mcp"]
env = { PROLIFIC_TOKEN = "your_token_here" }
```

Restart Codex (or start a new session) to pick it up.

### Cursor and other MCP-aware clients

Most clients accept the same `command` / `args` / `env` shape shown in the Claude Desktop JSON above.

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
