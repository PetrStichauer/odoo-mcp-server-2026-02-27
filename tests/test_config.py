"""Tests for connection profile configuration."""

from __future__ import annotations

import json
import stat

import pytest

from odoo_mcp_server.config import ConnectionStore, OdooConfig, is_readonly_mode


def test_resolve_profile(connection_store: ConnectionStore, sample_store):
    config = connection_store.resolve_config("production")
    assert config.url == "https://odoo.example.com"
    assert config.database == "main"
    assert config.username == "admin"
    assert config.api_key == "secret-key"
    assert config.connection_name == "production"


def test_resolve_active_from_env(
    connection_store: ConnectionStore,
    sample_store,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ODOO_CONNECTION", "staging")
    config = connection_store.resolve_config()
    assert config.connection_name == "staging"
    assert config.url == "https://staging.example.com"


def test_resolve_default_profile(connection_store: ConnectionStore, sample_store):
    config = connection_store.resolve_config()
    assert config.connection_name == "production"


def test_missing_profile_raises(connection_store: ConnectionStore, sample_store):
    with pytest.raises(ValueError, match="Connection 'missing' not found"):
        connection_store.resolve_config("missing")


def test_missing_config_raises(connection_store: ConnectionStore):
    with pytest.raises(ValueError, match="No Odoo connection configured"):
        connection_store.resolve_config()


def test_env_override(
    connection_store: ConnectionStore,
    sample_store,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("ODOO_URL", "https://env.example.com")
    monkeypatch.setenv("ODOO_DB", "envdb")
    monkeypatch.setenv("ODOO_USER", "bot")
    monkeypatch.setenv("ODOO_API_KEY", "env-key")

    config = connection_store.resolve_config("production")
    assert config.connection_name == "env"
    assert config.url == "https://env.example.com"


def test_partial_env_raises(connection_store: ConnectionStore, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ODOO_URL", "https://env.example.com")
    with pytest.raises(ValueError, match="Partial Odoo env configuration"):
        connection_store.resolve_config()


def test_add_connection_sets_secure_permissions(connection_store: ConnectionStore):
    connection_store.add_connection(
        "dev",
        "https://dev.example.com",
        "devdb",
        "admin",
        "key123",
        make_default=True,
    )

    assert connection_store.config_path.exists()
    mode = connection_store.config_path.stat().st_mode
    assert stat.S_IMODE(mode) == 0o600

    dir_mode = connection_store.config_dir.stat().st_mode
    assert stat.S_IMODE(dir_mode) == 0o700

    data = json.loads(connection_store.config_path.read_text(encoding="utf-8"))
    assert data["default"] == "dev"
    assert data["connections"]["dev"]["api_key"] == "key123"


def test_list_connections_info(connection_store: ConnectionStore, sample_store):
    info = connection_store.list_connections_info()
    assert info["source"] == "profiles"
    assert info["default"] == "production"
    assert len(info["connections"]) == 2


def test_odoo_config_from_dict():
    config = OdooConfig.from_dict(
        {
            "url": "https://odoo.example.com/",
            "database": "main",
            "username": "admin",
            "api_key": "key",
        },
        "production",
    )
    assert config.url == "https://odoo.example.com"
    assert config.connection_name == "production"


def test_is_readonly_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ODOO_READONLY", "true")
    assert is_readonly_mode() is True
    monkeypatch.setenv("ODOO_READONLY", "0")
    assert is_readonly_mode() is False
