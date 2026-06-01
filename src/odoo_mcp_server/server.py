"""Odoo MCP Server - Main server implementation."""

from __future__ import annotations

import asyncio
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import TextContent

from .tools import ALL_TOOLS, dispatch_tool

load_dotenv()

app = Server("odoo-mcp-server")


@app.list_tools()
async def list_tools():
    """List available tools."""
    return ALL_TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        return await dispatch_tool(name, arguments)
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


def run_server() -> None:
    """Run the MCP server over stdio."""

    async def run() -> None:
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )

    asyncio.run(run())


def main() -> None:
    """Main entry point for the MCP server."""
    run_server()


if __name__ == "__main__":
    main()
