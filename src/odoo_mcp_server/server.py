"""Odoo MCP Server - Main server implementation."""

import json
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import TextContent, Tool

from .config import OdooConfig
from .odoo_client import OdooClient

load_dotenv()

app = Server("odoo-mcp-server")

# Global client instance (initialized lazily)
_odoo_client: OdooClient | None = None


def get_odoo_client() -> OdooClient:
    """Get or initialize the Odoo client."""
    global _odoo_client
    if _odoo_client is None:
        odoo_config = OdooConfig.from_env()
        _odoo_client = OdooClient(odoo_config)
    return _odoo_client


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_partners",
            description="Search for customers/contacts (res.partner) in Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name or partial name to search for",
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address to search for",
                    },
                    "is_company": {
                        "type": "boolean",
                        "description": "Filter by company vs individual",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 20)",
                        "default": 20,
                    },
                },
            },
        ),
        Tool(
            name="get_partner",
            description="Get detailed information about a specific partner by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "partner_id": {
                        "type": "integer",
                        "description": "ID of the partner to retrieve",
                    },
                },
                "required": ["partner_id"],
            },
        ),
        Tool(
            name="create_task",
            description="Create a new project task in Odoo",
            inputSchema={
                "type": "object",
                "properties": {
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
                "required": ["name"],
            },
        ),
        Tool(
            name="search_tasks",
            description="Search for project tasks with filters",
            inputSchema={
                "type": "object",
                "properties": {
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
                        "description": "Filter by state: 'draft', 'open', 'pending', 'cancelled', 'done' (optional)",
                        "enum": ["draft", "open", "pending", "cancelled", "done"],
                    },
                    "priority": {
                        "type": "string",
                        "description": "Filter by priority: '0' (low), '1' (high) (optional)",
                        "enum": ["0", "1"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 20)",
                        "default": 20,
                    },
                },
            },
        ),
        Tool(
            name="get_project",
            description="Get project information by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "ID of the project to retrieve",
                    },
                },
                "required": ["project_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_partners":
            return await _search_partners(arguments)
        elif name == "get_partner":
            return await _get_partner(arguments)
        elif name == "create_task":
            return await _create_task(arguments)
        elif name == "search_tasks":
            return await _search_tasks(arguments)
        elif name == "get_project":
            return await _get_project(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _search_partners(arguments: dict[str, Any]) -> list[TextContent]:
    """Search for partners."""
    client = get_odoo_client()
    domain = []

    if name := arguments.get("name"):
        domain.append(("name", "ilike", name))

    if email := arguments.get("email"):
        domain.append(("email", "ilike", email))

    if is_company := arguments.get("is_company"):
        domain.append(("is_company", "=", is_company))

    limit = arguments.get("limit", 20)

    fields = ["id", "name", "email", "phone", "is_company", "city", "country_id"]

    partners = client.search_read("res.partner", domain, fields=fields, limit=limit)

    if not partners:
        return [TextContent(type="text", text="No partners found matching your criteria.")]

    # Format results
    results = []
    for p in partners:
        country = p.get("country_id")
        country_name = country[1] if country and len(country) > 1 else ""

        results.append({
            "id": p["id"],
            "name": p.get("name", ""),
            "email": p.get("email", ""),
            "phone": p.get("phone", ""),
            "is_company": p.get("is_company", False),
            "city": p.get("city", ""),
            "country": country_name,
        })

    return [TextContent(type="text", text=json.dumps(results, indent=2))]


async def _get_partner(arguments: dict[str, Any]) -> list[TextContent]:
    """Get partner details."""
    client = get_odoo_client()
    partner_id = arguments["partner_id"]

    fields = [
        "id", "name", "email", "phone", "mobile", "is_company",
        "street", "street2", "city", "zip", "country_id", "state_id",
        "vat", "website", "comment", "user_id", "category_id"
    ]

    partners = client.read("res.partner", [partner_id], fields=fields)

    if not partners:
        return [TextContent(type="text", text=f"Partner with ID {partner_id} not found.")]

    partner = partners[0]

    # Format country and state
    country = partner.get("country_id")
    partner["country"] = country[1] if country and len(country) > 1 else ""
    del partner["country_id"]

    state = partner.get("state_id")
    partner["state"] = state[1] if state and len(state) > 1 else ""
    del partner["state_id"]

    # Format user
    user = partner.get("user_id")
    partner["salesperson"] = user[1] if user and len(user) > 1 else ""
    del partner["user_id"]

    # Format categories
    categories = partner.get("category_id", [])
    partner["tags"] = [c[1] if isinstance(c, tuple) and len(c) > 1 else str(c) for c in categories]
    del partner["category_id"]

    return [TextContent(type="text", text=json.dumps(partner, indent=2))]


async def _create_task(arguments: dict[str, Any]) -> list[TextContent]:
    """Create a new project task."""
    client = get_odoo_client()
    values = {"name": arguments["name"]}

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

    return [TextContent(
        type="text",
        text=f"Task created successfully with ID: {task_id}"
    )]


async def _search_tasks(arguments: dict[str, Any]) -> list[TextContent]:
    """Search for tasks."""
    client = get_odoo_client()
    domain = []

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

    limit = arguments.get("limit", 20)

    fields = [
        "id", "name", "project_id", "user_ids", "partner_id",
        "state", "priority", "date_deadline", "create_date"
    ]

    tasks = client.search_read("project.task", domain, fields=fields, limit=limit)

    if not tasks:
        return [TextContent(type="text", text="No tasks found matching your criteria.")]

    # Format results
    results = []
    for t in tasks:
        project = t.get("project_id")
        partner = t.get("partner_id")
        users = t.get("user_ids", [])

        results.append({
            "id": t["id"],
            "name": t.get("name", ""),
            "project": project[1] if project and len(project) > 1 else "",
            "project_id": project[0] if project else None,
            "assigned_to": [u[1] if isinstance(u, tuple) and len(u) > 1 else str(u) for u in users],
            "customer": partner[1] if partner and len(partner) > 1 else "",
            "customer_id": partner[0] if partner else None,
            "state": t.get("state", ""),
            "priority": "high" if t.get("priority") == "1" else "low",
            "deadline": t.get("date_deadline", ""),
            "created": t.get("create_date", ""),
        })

    return [TextContent(type="text", text=json.dumps(results, indent=2))]


async def _get_project(arguments: dict[str, Any]) -> list[TextContent]:
    """Get project details."""
    client = get_odoo_client()
    project_id = arguments["project_id"]

    fields = [
        "id", "name", "partner_id", "user_id", "state",
        "date_start", "date", "description", "task_count",
        "task_ids", "type_ids", "label_tasks"
    ]

    projects = client.read("project.project", [project_id], fields=fields)

    if not projects:
        return [TextContent(type="text", text=f"Project with ID {project_id} not found.")]

    project = projects[0]

    # Format partner
    partner = project.get("partner_id")
    project["customer"] = partner[1] if partner and len(partner) > 1 else ""
    del project["partner_id"]

    # Format user
    user = project.get("user_id")
    project["project_manager"] = user[1] if user and len(user) > 1 else ""
    del project["user_id"]

    return [TextContent(type="text", text=json.dumps(project, indent=2))]


def main():
    """Main entry point."""
    from mcp.server.stdio import stdio_server
    import asyncio

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
