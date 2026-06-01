"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from odoo_mcp_server.client_pool import reset_client_pool, set_connection_store
from odoo_mcp_server.config import ConnectionStore


@pytest.fixture
def connections_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config_path = tmp_path / "connections.json"
    monkeypatch.setenv("ODOO_MCP_CONFIG", str(config_path))
    monkeypatch.delenv("ODOO_URL", raising=False)
    monkeypatch.delenv("ODOO_DB", raising=False)
    monkeypatch.delenv("ODOO_USER", raising=False)
    monkeypatch.delenv("ODOO_API_KEY", raising=False)
    monkeypatch.delenv("ODOO_CONNECTION", raising=False)
    return config_path


@pytest.fixture
def connection_store(connections_file: Path) -> ConnectionStore:
    store = ConnectionStore(connections_file)
    set_connection_store(store)
    yield store
    reset_client_pool()


@pytest.fixture
def sample_store(connections_file: Path) -> Path:
    payload = {
        "default": "production",
        "connections": {
            "production": {
                "url": "https://odoo.example.com",
                "database": "main",
                "username": "admin",
                "api_key": "secret-key",
            },
            "staging": {
                "url": "https://staging.example.com",
                "database": "staging",
                "username": "admin",
                "api_key": "staging-key",
            },
        },
    }
    connections_file.write_text(json.dumps(payload), encoding="utf-8")
    return connections_file
