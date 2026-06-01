"""Partner-related MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent, Tool

from .common import (
    cap_limit,
    json_response,
    resolve_client,
    text_response,
    with_connection_schema,
)

PARTNER_TOOLS = [
    Tool(
        name="search_partners",
        description="Search for customers/contacts (res.partner) in Odoo",
        inputSchema=with_connection_schema(
            {
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
                    "description": "Maximum number of results (default: 20, max: 100)",
                    "default": 20,
                },
            }
        ),
    ),
    Tool(
        name="get_partner",
        description="Get detailed information about a specific partner by ID",
        inputSchema=with_connection_schema(
            {
                "partner_id": {
                    "type": "integer",
                    "description": "ID of the partner to retrieve",
                },
            },
            required=["partner_id"],
        ),
    ),
]


async def handle_partner_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle partner MCP tools."""
    if name == "search_partners":
        return await _search_partners(arguments)
    if name == "get_partner":
        return await _get_partner(arguments)
    return [TextContent(type="text", text=f"Unknown partner tool: {name}")]


async def _search_partners(arguments: dict[str, Any]) -> list[TextContent]:
    client = resolve_client(arguments)
    domain: list[Any] = []

    if name := arguments.get("name"):
        domain.append(("name", "ilike", name))

    if email := arguments.get("email"):
        domain.append(("email", "ilike", email))

    if "is_company" in arguments and arguments["is_company"] is not None:
        domain.append(("is_company", "=", arguments["is_company"]))

    limit = cap_limit(arguments.get("limit"), default=20)
    fields = ["id", "name", "email", "phone", "is_company", "city", "country_id"]
    partners = client.search_read("res.partner", domain, fields=fields, limit=limit)

    if not partners:
        return text_response("No partners found matching your criteria.")

    results = []
    for partner in partners:
        country = partner.get("country_id")
        country_name = country[1] if country and len(country) > 1 else ""
        results.append(
            {
                "id": partner["id"],
                "name": partner.get("name", ""),
                "email": partner.get("email", ""),
                "phone": partner.get("phone", ""),
                "is_company": partner.get("is_company", False),
                "city": partner.get("city", ""),
                "country": country_name,
            }
        )

    return json_response(results)


async def _get_partner(arguments: dict[str, Any]) -> list[TextContent]:
    client = resolve_client(arguments)
    partner_id = int(arguments["partner_id"])

    fields = [
        "id",
        "name",
        "email",
        "phone",
        "mobile",
        "is_company",
        "street",
        "street2",
        "city",
        "zip",
        "country_id",
        "state_id",
        "vat",
        "website",
        "comment",
        "user_id",
        "category_id",
    ]

    partners = client.read("res.partner", [partner_id], fields=fields)
    if not partners:
        return text_response(f"Partner with ID {partner_id} not found.")

    partner = partners[0]
    country = partner.get("country_id")
    partner["country"] = country[1] if country and len(country) > 1 else ""
    del partner["country_id"]

    state = partner.get("state_id")
    partner["state"] = state[1] if state and len(state) > 1 else ""
    del partner["state_id"]

    user = partner.get("user_id")
    partner["salesperson"] = user[1] if user and len(user) > 1 else ""
    del partner["user_id"]

    categories = partner.get("category_id", [])
    partner["tags"] = [
        category[1] if isinstance(category, tuple) and len(category) > 1 else str(category)
        for category in categories
    ]
    del partner["category_id"]

    return json_response(partner)
