"""Project-related MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent, Tool

from .common import json_response, resolve_client, text_response, with_connection_schema

PROJECT_TOOLS = [
    Tool(
        name="get_project",
        description="Get project information by ID",
        inputSchema=with_connection_schema(
            {
                "project_id": {
                    "type": "integer",
                    "description": "ID of the project to retrieve",
                },
            },
            required=["project_id"],
        ),
    ),
]


async def handle_project_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle project MCP tools."""
    if name == "get_project":
        return await _get_project(arguments)
    return [TextContent(type="text", text=f"Unknown project tool: {name}")]


async def _get_project(arguments: dict[str, Any]) -> list[TextContent]:
    client = resolve_client(arguments)
    project_id = int(arguments["project_id"])

    fields = [
        "id",
        "name",
        "partner_id",
        "user_id",
        "state",
        "date_start",
        "date",
        "description",
        "task_count",
        "task_ids",
        "type_ids",
        "label_tasks",
    ]

    projects = client.read("project.project", [project_id], fields=fields)
    if not projects:
        return text_response(f"Project with ID {project_id} not found.")

    project = projects[0]
    partner = project.get("partner_id")
    project["customer"] = partner[1] if partner and len(partner) > 1 else ""
    del project["partner_id"]

    user = project.get("user_id")
    project["project_manager"] = user[1] if user and len(user) > 1 else ""
    del project["user_id"]

    return json_response(project)
