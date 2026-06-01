"""Tests for Odoo XML-RPC client."""

from __future__ import annotations

import xmlrpc.client
from unittest.mock import MagicMock, patch

import pytest

from odoo_mcp_server.config import OdooConfig
from odoo_mcp_server.odoo_client import (
    AuthenticationError,
    OdooClient,
    OdooError,
    _sanitize_fault_message,
)


@pytest.fixture
def config() -> OdooConfig:
    return OdooConfig(
        url="https://odoo.example.com",
        database="main",
        username="admin",
        api_key="secret",
        connection_name="production",
    )


def test_authenticate_success(config: OdooConfig):
    client = OdooClient(config)
    common = MagicMock()
    common.authenticate.return_value = 7

    with patch.object(client, "_get_common_proxy", return_value=common):
        uid = client.authenticate()

    assert uid == 7
    common.authenticate.assert_called_once_with("main", "admin", "secret", {})


def test_authenticate_failure(config: OdooConfig):
    client = OdooClient(config)
    common = MagicMock()
    common.authenticate.return_value = False

    with patch.object(client, "_get_common_proxy", return_value=common):
        with pytest.raises(AuthenticationError, match="Failed to authenticate"):
            client.authenticate()


def test_search_read(config: OdooConfig):
    client = OdooClient(config)
    common = MagicMock()
    common.authenticate.return_value = 7
    obj = MagicMock()
    obj.execute_kw.return_value = [{"id": 1, "name": "Acme"}]

    with patch.object(client, "_get_common_proxy", return_value=common):
        with patch.object(client, "_get_object_proxy", return_value=obj):
            records = client.search_read("res.partner", [("name", "ilike", "Acme")], limit=5)

    assert records == [{"id": 1, "name": "Acme"}]
    obj.execute_kw.assert_called_once()


def test_call_wraps_fault(config: OdooConfig):
    client = OdooClient(config)
    common = MagicMock()
    common.authenticate.return_value = 7
    obj = MagicMock()
    obj.execute_kw.side_effect = xmlrpc.client.Fault(1, "Access Denied\nTraceback...")

    with patch.object(client, "_get_common_proxy", return_value=common):
        with patch.object(client, "_get_object_proxy", return_value=obj):
            with pytest.raises(OdooError, match="Access Denied"):
                client.read("res.partner", [1])


def test_sanitize_fault_message():
    message = "Traceback (most recent call last):\nFile \"x.py\"\nValueError: Invalid domain"
    assert _sanitize_fault_message(message) == "Invalid domain"
