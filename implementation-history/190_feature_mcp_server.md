# Prompt 190 - Feature: simple MCP server

## Objective

Add a minimal Model Context Protocol (MCP) server as a backend entrypoint, exposing a demo `add` tool and a `greeting://{name}` resource. Uses the installed `mcp` 2.x SDK (`MCPServer`, which replaced the v1 `FastMCP`).

## Current State

- `mcp[cli]>=2.1.1` is already a backend dependency (`pyproject.toml`).
- No MCP server entrypoint exists yet.
- Entrypoints live in `apps/backend/entrypoints/` (`api.py`, `worker.py`, `scheduler.py`, `cli.py`).

## Implementation Steps

1. Create `apps/backend/entrypoints/mcp_server.py`:
   - `from mcp.server import MCPServer` (the v2 rename of v1 `FastMCP`).
   - `mcp = MCPServer("Demo")`.
   - `@mcp.tool()` `add(a: int, b: int) -> int`.
   - `@mcp.resource("greeting://{name}")` `greeting(name: str) -> str`.
   - `if __name__ == "__main__": mcp.run()` so the module is runnable.

## Files to Modify / Create

- Create: `apps/backend/entrypoints/mcp_server.py`
- Create: `implementation-history/190_feature_mcp_server.md`

## Testing Requirements

- `uv run python -c "import apps.backend.entrypoints.mcp_server"` imports cleanly.
- (Manual) `uv run python -m apps.backend.entrypoints.mcp_server` starts the stdio server.

## Constraints

- Keep it minimal/demo-grade; no bounded-context wiring.
- Follows repo layout: standalone entrypoint under `entrypoints/`.
- No `print()` (structlog available if logging needed later).
