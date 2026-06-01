"""Connection-related MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent, Tool

from ..client_pool import get_connection_store, get_odoo_client
from .common import json_response, with_connection_schema

CONNECTION_TOOLS = [
    Tool(
        name="list_connections",
        description="List configured Odoo connection profiles (no credentials returned)",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="test_connection",
        description="Test authentication against an Odoo connection and return version info",
        inputSchema=with_connection_schema({}),
    ),
]


async def handle_connection_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle connection MCP tools."""
    if name == "list_connections":
        store = get_connection_store()
        return json_response(store.list_connections_info())

    if name == "test_connection":
        client = get_odoo_client(arguments.get("connection"))
        uid = client.authenticate()
        version = client.get_server_version()
        return json_response(
            {
                "status": "ok",
                "connection": client.config.connection_name,
                "url": client.config.url,
                "database": client.config.database,
                "username": client.config.username,
                "uid": uid,
                "server_version": version,
            }
        )

    return [TextContent(type="text", text=f"Unknown connection tool: {name}")]
