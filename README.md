# prolific-mcp

[![CI](https://github.com/prolific-oss/prolific-mcp/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/prolific-oss/prolific-mcp/actions/workflows/ci.yml)
[![Known Vulnerabilities](https://snyk.io/test/github/prolific-oss/prolific-mcp/badge.svg)](https://snyk.io/test/github/prolific-oss/prolific-mcp)

A [Model Context Protocol](https://modelcontextprotocol.io/) server bridging LLM agents to the [Prolific](https://www.prolific.com) public API. Built with [FastMCP](https://gofastmcp.com).

Listed on the [official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=prolific) — discoverable from Claude Desktop, Cursor, Claude Code, and other MCP-aware clients.

> [!WARNING]
> **`publish_study` spends real money.** Once a study is published on Prolific, participants can start it immediately and you are charged for their work. Treat any LLM-driven invocation as a real spend: review the study draft and reward before approving the tool call. There is no sandbox mode — the same endpoint is used in production.

## What it does

Exposes a small set of tools so an LLM can help a researcher design and launch a study on Prolific:

| Tool | Prolific endpoint |
|---|---|
| `get_filters` | `GET /api/v1/filters/` |
| `get_filter_sets` | `GET /api/v1/filter-sets/` |
| `create_filter_set` | `POST /api/v1/filter-sets/` |
| `get_eligibility_count` | `POST /api/v1/eligibility-count/` |
| `list_workspaces` | `GET /api/v1/workspaces/` |
| `list_projects` | `GET /api/v1/workspaces/{workspace_id}/projects/` |
| `list_studies` | `GET /api/v1/studies/` |
| `view_study` | `GET /api/v1/studies/{id}/` |
| `create_study` | `POST /api/v1/studies/` |
| `publish_study` | `POST /api/v1/studies/{id}/transition/` |
| `get_capabilities` | _(local — no Prolific endpoint; reports server version, target API URL, and registered tools)_ |

## Capability map

This server currently wraps Prolific's classic Study resource, plus the filters/eligibility/workspace/project lookups needed to build one. It does not yet expose either of Prolific's AI Task Builder resources — **Collection** or **Batch** — or most of the study lifecycle beyond publish. The table below maps what exists today across MCP, REST, and the [`prolific` CLI](https://github.com/prolific-oss/cli), by capability area.

Collection and Batch are separate resources, not aliases — Collection is static content with no dataset; Batch is dataset-driven and needs a setup/sync step first. Neither is exposed via MCP yet.

| Capability area | Resource | REST endpoint | CLI command | MCP tool | Stability |
|---|---|---|---|---|---|
| Creation/inspection | Collection | `POST /api/v1/data-collection/collections`, `GET .../collections/{id}` | `collection create` / `get <id>` / `list` | Not exposed | — |
| Creation/inspection | Batch | `POST /api/v1/data-collection/batches`, `GET .../batches/{id}`, `GET .../batches/?workspace_id=` | `aitaskbuilder batch create` / `view <id>` / `list`; datasets via `aitaskbuilder dataset create` / `upload` / `check` | Not exposed | — |
| Creation/inspection | Study | `POST /api/v1/studies/`, `GET /api/v1/studies/{id}` | `study create` / `view` / `list` | `create_study`, `view_study`, `list_studies` | stable |
| Update | Study | `PATCH /api/v1/studies/{id}/` | `study update <study_id>` | Not exposed | — |
| Update | Collection | `PATCH /api/v1/data-collection/collections/{id}/` | `collection update <collection-id>` | Not exposed | — |
| Publish | Collection (via Study) | `POST /api/v1/studies/` with `data_collection_method="AI_TASK_BUILDER_COLLECTION"` + `data_collection_id=<id>`, then `POST /api/v1/studies/{id}/transition/` (`action=PUBLISH`) | `collection publish <collection-id>` | **Already possible, undocumented**: `create_study` forwards unknown fields, so passing `data_collection_method`/`data_collection_id` and then calling `publish_study` works today with no new MCP tool needed | stable (undocumented) |
| Monitoring | Study | `GET /api/v1/studies/{id}/submissions/counts/` | `study submission-counts` | Not exposed | — |
| Monitoring | Batch | `GET /api/v1/data-collection/batches/{id}/status` | `aitaskbuilder batch check <id>` | Not exposed | — |
| Monitoring | Collection | `GET /api/v1/data-collection/collections/{id}` | `collection get <id>` | Not exposed | — |
| Pause/start/stop | Study | `POST /api/v1/studies/{id}/transition/` (`action=PAUSE\|START\|STOP\|PUBLISH`) | `study transition <id> -a PAUSE\|STOP\|START` | `publish_study` (`PUBLISH` only) | stable (partial) |
| Submissions | Study | `GET /api/v1/studies/{id}/submissions/?limit=&offset=` | `submission list` | Not exposed | — |
| Approval | Submission | `POST /api/v1/submissions/{id}/transition/`, `POST /api/v1/submissions/bulk-approve/`, `POST /api/v1/submissions/{id}/request-return/` | `submission transition -a APPROVE\|...`, `bulk-approve`, `request-return` | Not exposed | — |
| Exports | Collection | `GET`/`POST /api/v1/data-collection/collections/{id}/export`, `.../export/{exportId}` | `collection export <id>` | Not exposed | — |
| Exports | Batch | `GET`/`POST /api/v1/data-collection/batches/{id}/export`, `.../export/{exportId}` | `aitaskbuilder batch export <id>` | Not exposed | — |
| Exports | Study | `GET /api/v1/studies/{id}/demographic-export/` | `study demographic-export <id>` | Not exposed | — |
| Webhooks | Workspace (cross-resource) | `POST`/`GET`/`PATCH`/`DELETE /api/v1/hooks/subscriptions/`, `GET /api/v1/hooks/event-types/` | `hook create` / `list` / `update` / `delete` / `event-list` / `event-type` / `create-secret` | Not exposed | — |
| Financial reconciliation | Submission | `POST /api/v1/submissions/bonus-payments/`, `POST /api/v1/bulk-bonus-payments/{id}/pay/` | `bonus create` / `pay` | Not exposed | — |
| Eligibility | Study | `POST /api/v1/eligibility-count/`, `GET /api/v1/filters/`, `GET /api/v1/filter-sets/` | `filters ...`, `filtersets ...`, `eligibilitycount ...` | `get_filters`, `get_filter_sets`, `create_filter_set`, `get_eligibility_count` | stable |
| Discovery | Workspace/Project | `GET /api/v1/workspaces/`, `GET /api/v1/workspaces/{id}/projects/` | `workspace list`, `project list` | `list_workspaces`, `list_projects` | stable |
| Server introspection | — | _(local — no Prolific endpoint)_ | — | `get_capabilities` | stable |

The MCP tool and stability columns above are a point-in-time snapshot — call `get_capabilities` for the live, always-current tool list and stability for whatever server you're actually connected to.

`publish_study` is the one **partial**-coverage row today — it wraps `transition` but only the `PUBLISH` action, not `PAUSE`/`START`/`STOP`. That's a natural first extension if MCP lifecycle coverage becomes a roadmap item.

CLI commands above omit the `prolific` binary prefix (e.g. `collection create` is `prolific collection create`) — run `prolific <command> --help` for exact flags before scripting against them.

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
