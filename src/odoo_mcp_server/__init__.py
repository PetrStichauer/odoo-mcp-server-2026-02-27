"""Odoo MCP Server."""

from .cli import main
from .client_pool import get_odoo_client
from .config import ConnectionStore, OdooConfig
from .odoo_client import AuthenticationError, OdooClient, OdooError
from .server import app, run_server

__all__ = [
    "AuthenticationError",
    "ConnectionStore",
    "OdooClient",
    "OdooConfig",
    "OdooError",
    "app",
    "get_odoo_client",
    "main",
    "run_server",
]

__version__ = "0.2.0"
