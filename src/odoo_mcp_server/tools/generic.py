"""Generic read MCP tools for arbitrary Odoo models."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent, Tool

from .common import (
    cap_limit,
    json_response,
    resolve_client,
    text_response,
    validate_domain,
    with_connection_schema,
)

GENERIC_TOOLS = [
    Tool(
        name="search_records",
        description=(
            "Search and read records from any Odoo model using search_read. "
            "Domain must be a JSON list of filter clauses."
        ),
        inputSchema=with_connection_schema(
            {
                "model": {
                    "type": "string",
                    "description": "Odoo model technical name (e.g. res.partner)",
                },
                "domain": {
                    "type": "array",
                    "description": "Odoo domain filter as JSON list (default: [])",
                    "items": {},
                    "default": [],
                },
                "fields": {
                    "type": "array",
                    "description": "Field names to return (optional)",
                    "items": {"type": "string"},
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum records to return (default: 20, max: 100)",
                    "default": 20,
                },
                "order": {
                    "type": "string",
                    "description": "Sort order, e.g. 'name asc' (optional)",
                },
            },
            required=["model"],
        ),
    ),
    Tool(
        name="read_record",
        description="Read a single Odoo record by ID",
        inputSchema=with_connection_schema(
            {
                "model": {
                    "type": "string",
                    "description": "Odoo model technical name",
                },
                "record_id": {
                    "type": "integer",
                    "description": "Record ID to read",
                },
                "fields": {
                    "type": "array",
                    "description": "Field names to return (optional)",
                    "items": {"type": "string"},
                },
            },
            required=["model", "record_id"],
        ),
    ),
    Tool(
        name="list_models",
        description="List available Odoo models (non-transient, capped)",
        inputSchema=with_connection_schema(
            {
                "name_filter": {
                    "type": "string",
                    "description": "Optional filter on model technical or human name",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum models to return (default: 50, max: 100)",
                    "default": 50,
                },
            }
        ),
    ),
]


async def handle_generic_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle generic MCP tools."""
    if name == "search_records":
        return await _search_records(arguments)
    if name == "read_record":
        return await _read_record(arguments)
    if name == "list_models":
        return await _list_models(arguments)
    return [TextContent(type="text", text=f"Unknown generic tool: {name}")]


async def _search_records(arguments: dict[str, Any]) -> list[TextContent]:
    client = resolve_client(arguments)
    model = str(arguments["model"]).strip()
    if not model:
        raise ValueError("model is required")

    domain = validate_domain(arguments.get("domain") or [])
    fields = arguments.get("fields")
    if fields is not None and not isinstance(fields, list):
        raise ValueError("fields must be a list of strings")

    limit = cap_limit(arguments.get("limit"), default=20)
    order = arguments.get("order") or ""

    records = client.search_read(
        model,
        domain,
        fields=fields,
        limit=limit,
        order=str(order) if order else "",
    )

    if not records:
        return text_response(f"No records found in {model} matching the domain.")

    return json_response(records)


async def _read_record(arguments: dict[str, Any]) -> list[TextContent]:
    client = resolve_client(arguments)
    model = str(arguments["model"]).strip()
    record_id = int(arguments["record_id"])
    fields = arguments.get("fields")
    if fields is not None and not isinstance(fields, list):
        raise ValueError("fields must be a list of strings")

    records = client.read(model, [record_id], fields=fields)
    if not records:
        return text_response(f"Record {record_id} not found in {model}.")

    return json_response(records[0])


async def _list_models(arguments: dict[str, Any]) -> list[TextContent]:
    client = resolve_client(arguments)
    domain: list[Any] = [("transient", "=", False)]

    if name_filter := arguments.get("name_filter"):
        domain = [
            ("transient", "=", False),
            "|",
            ("model", "ilike", name_filter),
            ("name", "ilike", name_filter),
        ]

    limit = cap_limit(arguments.get("limit"), default=50)
    models = client.search_read(
        "ir.model",
        domain,
        fields=["model", "name"],
        limit=limit,
        order="model asc",
    )

    return json_response(models)
