"""Odoo MCP Server."""

from .config import OdooConfig
from .odoo_client import OdooClient
from .server import app, main

__all__ = ["OdooConfig", "OdooClient", "app", "main"]
