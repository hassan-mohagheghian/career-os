"""MCP server entrypoint.

Minimal Model Context Protocol server (mcp 2.x SDK). Exposes a demo `add`
tool and a `greeting://{name}` resource. Run with:

    uv run python -m apps.backend.entrypoints.mcp_server

The server uses stdio transport by default.
"""

from mcp.server import MCPServer

mcp = MCPServer("Demo")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


@mcp.resource("greeting://{name}")
def greeting(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run()
