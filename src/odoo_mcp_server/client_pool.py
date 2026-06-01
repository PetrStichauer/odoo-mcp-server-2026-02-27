"""Odoo client pool keyed by connection name."""

from __future__ import annotations

from .config import ConnectionStore
from .odoo_client import OdooClient

_store = ConnectionStore()
_clients: dict[str, OdooClient] = {}


def get_connection_store() -> ConnectionStore:
    """Return the shared connection store."""
    return _store


def get_odoo_client(connection_name: str | None = None) -> OdooClient:
    """Get or initialize an Odoo client for the given connection."""
    config = _store.resolve_config(connection_name)
    key = config.connection_name

    if key not in _clients:
        _clients[key] = OdooClient(config)

    return _clients[key]


def reset_client_pool() -> None:
    """Clear cached clients (used in tests)."""
    _clients.clear()


def set_connection_store(store: ConnectionStore) -> None:
    """Replace the shared connection store (used in tests)."""
    global _store
    _store = store
    reset_client_pool()
