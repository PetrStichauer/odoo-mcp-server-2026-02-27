"""MCP tool definitions and handlers."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from mcp.types import TextContent, Tool

from .connection import CONNECTION_TOOLS, handle_connection_tool
from .generic import GENERIC_TOOLS, handle_generic_tool
from .partners import PARTNER_TOOLS, handle_partner_tool
from .projects import PROJECT_TOOLS, handle_project_tool
from .tasks import TASK_TOOLS, handle_task_tool

ToolHandler = Callable[[dict[str, Any]], Awaitable[list[TextContent]]]

ALL_TOOLS: list[Tool] = [
    *CONNECTION_TOOLS,
    *PARTNER_TOOLS,
    *TASK_TOOLS,
    *PROJECT_TOOLS,
    *GENERIC_TOOLS,
]

TOOL_HANDLERS: dict[str, ToolHandler] = {}


def _register(tools: list[Tool], handler: ToolHandler) -> None:
    for tool in tools:
        TOOL_HANDLERS[tool.name] = handler


_register(CONNECTION_TOOLS, handle_connection_tool)
_register(PARTNER_TOOLS, handle_partner_tool)
_register(TASK_TOOLS, handle_task_tool)
_register(PROJECT_TOOLS, handle_project_tool)
_register(GENERIC_TOOLS, handle_generic_tool)


async def dispatch_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Route a tool call to the appropriate handler."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    return await handler(name, arguments)
