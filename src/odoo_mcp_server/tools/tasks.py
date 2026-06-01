"""Task-related MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent, Tool

from .common import (
    cap_limit,
    enforce_readonly,
    json_response,
    resolve_client,
    text_response,
    with_connection_schema,
)

TASK_TOOLS = [
    Tool(
        name="create_task",
        description="Create a new project task in Odoo",
        inputSchema=with_connection_schema(
            {
                "name": {
                    "type": "string",
                    "description": "Name/title of the task",
                },
                "project_id": {
                    "type": "integer",
                    "description": "ID of the project (optional)",
                },
                "user_id": {
                    "type": "integer",
                    "description": "ID of the assigned user (optional)",
                },
                "partner_id": {
                    "type": "integer",
                    "description": "ID of the related customer (optional)",
                },
                "description": {
                    "type": "string",
                    "description": "Task description (optional)",
                },
                "priority": {
                    "type": "string",
                    "description": "Priority: '0' (low), '1' (high) (optional)",
                    "enum": ["0", "1"],
                },
                "deadline": {
                    "type": "string",
                    "description": "Deadline date in format YYYY-MM-DD (optional)",
                },
            },
            required=["name"],
        ),
    ),
    Tool(
        name="search_tasks",
        description="Search for project tasks with filters",
        inputSchema=with_connection_schema(
            {
                "name": {
                    "type": "string",
                    "description": "Task name to search for (optional)",
                },
                "project_id": {
                    "type": "integer",
                    "description": "Filter by project ID (optional)",
                },
                "user_id": {
                    "type": "integer",
                    "description": "Filter by assigned user ID (optional)",
                },
                "state": {
                    "type": "string",
                    "description": (
                        "Filter by state: 'draft', 'open', 'pending', 'cancelled', 'done' (optional)"
                    ),
                    "enum": ["draft", "open", "pending", "cancelled", "done"],
                },
                "priority": {
                    "type": "string",
                    "description": "Filter by priority: '0' (low), '1' (high) (optional)",
                    "enum": ["0", "1"],
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 20, max: 100)",
                    "default": 20,
                },
            }
        ),
    ),
]


async def handle_task_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle task MCP tools."""
    if name == "create_task":
        return await _create_task(arguments)
    if name == "search_tasks":
        return await _search_tasks(arguments)
    return [TextContent(type="text", text=f"Unknown task tool: {name}")]


async def _create_task(arguments: dict[str, Any]) -> list[TextContent]:
    enforce_readonly("create_task")
    client = resolve_client(arguments)
    values: dict[str, Any] = {"name": arguments["name"]}

    if project_id := arguments.get("project_id"):
        values["project_id"] = project_id

    if user_id := arguments.get("user_id"):
        values["user_ids"] = [(6, 0, [user_id])]

    if partner_id := arguments.get("partner_id"):
        values["partner_id"] = partner_id

    if description := arguments.get("description"):
        values["description"] = description

    if priority := arguments.get("priority"):
        values["priority"] = priority

    if deadline := arguments.get("deadline"):
        values["date_deadline"] = deadline

    task_id = client.create("project.task", values)
    return text_response(f"Task created successfully with ID: {task_id}")


async def _search_tasks(arguments: dict[str, Any]) -> list[TextContent]:
    client = resolve_client(arguments)
    domain: list[Any] = []

    if name := arguments.get("name"):
        domain.append(("name", "ilike", name))

    if project_id := arguments.get("project_id"):
        domain.append(("project_id", "=", project_id))

    if user_id := arguments.get("user_id"):
        domain.append(("user_ids", "in", [user_id]))

    if state := arguments.get("state"):
        domain.append(("state", "=", state))

    if priority := arguments.get("priority"):
        domain.append(("priority", "=", priority))

    limit = cap_limit(arguments.get("limit"), default=20)
    fields = [
        "id",
        "name",
        "project_id",
        "user_ids",
        "partner_id",
        "state",
        "priority",
        "date_deadline",
        "create_date",
    ]

    tasks = client.search_read("project.task", domain, fields=fields, limit=limit)
    if not tasks:
        return text_response("No tasks found matching your criteria.")

    results = []
    for task in tasks:
        project = task.get("project_id")
        partner = task.get("partner_id")
        users = task.get("user_ids", [])

        results.append(
            {
                "id": task["id"],
                "name": task.get("name", ""),
                "project": project[1] if project and len(project) > 1 else "",
                "project_id": project[0] if project else None,
                "assigned_to": [
                    user[1] if isinstance(user, tuple) and len(user) > 1 else str(user)
                    for user in users
                ],
                "customer": partner[1] if partner and len(partner) > 1 else "",
                "customer_id": partner[0] if partner else None,
                "state": task.get("state", ""),
                "priority": "high" if task.get("priority") == "1" else "low",
                "deadline": task.get("date_deadline", ""),
                "created": task.get("create_date", ""),
            }
        )

    return json_response(results)
