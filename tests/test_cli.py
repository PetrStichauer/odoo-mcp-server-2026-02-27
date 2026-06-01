"""Tests for CLI commands."""

from __future__ import annotations

import json
import stat
from unittest.mock import patch

from odoo_mcp_server.cli import cmd_configure, cmd_test


def test_configure_list(connection_store, sample_store, capsys):
    args = type("Args", (), {"list": True, "default": False})()
    code = cmd_configure(args)
    captured = capsys.readouterr()

    assert code == 0
    assert "production" in captured.out
    assert "staging" in captured.out
    assert "secret-key" not in captured.out


def test_configure_interactive(connection_store, monkeypatch):
    inputs = iter(["staging", "https://staging.example.com", "stagingdb", "admin"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr("getpass.getpass", lambda prompt: "new-key")

    args = type("Args", (), {"list": False, "default": True})()
    code = cmd_configure(args)

    assert code == 0
    data = json.loads(connection_store.config_path.read_text(encoding="utf-8"))
    assert data["default"] == "staging"
    assert data["connections"]["staging"]["api_key"] == "new-key"
    assert stat.S_IMODE(connection_store.config_path.stat().st_mode) == 0o600


def test_test_command_success(connection_store, sample_store):
    mock_client = type(
        "Client",
        (),
        {
            "config": type(
                "Cfg",
                (),
                {
                    "connection_name": "production",
                    "url": "https://odoo.example.com",
                    "database": "main",
                    "username": "admin",
                },
            )(),
            "authenticate": lambda self: 7,
            "get_server_version": lambda self: {"server_version": "17.0"},
        },
    )()

    args = type("Args", (), {"connection": "production"})()
    with patch("odoo_mcp_server.cli.get_odoo_client", return_value=mock_client):
        code = cmd_test(args)

    assert code == 0


def test_test_command_failure(connection_store, sample_store, capsys):
    args = type("Args", (), {"connection": "production"})()

    with patch(
        "odoo_mcp_server.cli.get_odoo_client",
        side_effect=ValueError("Connection failed"),
    ):
        code = cmd_test(args)

    assert code == 1
    assert "Connection failed" in capsys.readouterr().err
