"""Shared helpers for MCP tool handlers."""

from __future__ import annotations

import json
from typing import Any

from mcp.types import TextContent

from ..client_pool import get_odoo_client
from ..config import is_readonly_mode
from ..odoo_client import OdooClient

MAX_RECORD_LIMIT = 100
MAX_DOMAIN_CLAUSES = 20

CONNECTION_PROPERTY = {
    "connection": {
        "type": "string",
        "description": (
            "Optional connection profile name. Uses ODOO_CONNECTION or default profile when omitted."
        ),
    },
}


def json_response(data: Any) -> list[TextContent]:
    """Return formatted JSON as MCP text content."""
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def text_response(message: str) -> list[TextContent]:
    """Return plain text MCP content."""
    return [TextContent(type="text", text=message)]


def error_response(message: str) -> list[TextContent]:
    """Return an error message."""
    return [TextContent(type="text", text=f"Error: {message}")]


def resolve_client(arguments: dict[str, Any]) -> OdooClient:
    """Resolve Odoo client from optional connection argument."""
    connection = arguments.get("connection")
    if connection is not None and not isinstance(connection, str):
        raise ValueError("'connection' must be a string")
    return get_odoo_client(connection)


def enforce_readonly(operation: str) -> None:
    """Raise if write operations are disabled."""
    if is_readonly_mode():
        raise PermissionError(
            f"Write operation '{operation}' blocked: ODOO_READONLY is enabled. "
            "Unset ODOO_READONLY to allow writes."
        )


def cap_limit(limit: int | None, default: int = 20) -> int:
    """Clamp record limit to safe bounds."""
    value = default if limit is None else int(limit)
    if value < 1:
        raise ValueError("limit must be at least 1")
    if value > MAX_RECORD_LIMIT:
        raise ValueError(f"limit cannot exceed {MAX_RECORD_LIMIT}")
    return value


def validate_domain(domain: list[Any]) -> list[Any]:
    """Validate domain list size and basic structure."""
    if not isinstance(domain, list):
        raise ValueError("domain must be a JSON list of filter clauses")
    if len(domain) > MAX_DOMAIN_CLAUSES:
        raise ValueError(f"domain cannot exceed {MAX_DOMAIN_CLAUSES} clauses")
    return domain


def with_connection_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict:
    """Build input schema with optional connection parameter."""
    merged = {**properties, **CONNECTION_PROPERTY}
    return {
        "type": "object",
        "properties": merged,
        "required": required or [],
    }
