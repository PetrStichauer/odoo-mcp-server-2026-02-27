"""Tests for MCP tool handlers."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from odoo_mcp_server.tools.partners import _search_partners
from odoo_mcp_server.tools.tasks import _create_task, _search_tasks


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.search_read.return_value = [
        {
            "id": 1,
            "name": "Acme Corp",
            "email": "info@acme.com",
            "phone": "123",
            "is_company": True,
            "city": "Prague",
            "country_id": [56, "Czech Republic"],
        }
    ]
    client.create.return_value = 42
    return client


@pytest.mark.asyncio
async def test_search_partners_builds_domain(mock_client):
    with patch("odoo_mcp_server.tools.common.get_odoo_client", return_value=mock_client):
        result = await _search_partners(
            {
                "name": "Acme",
                "email": "acme",
                "is_company": True,
                "limit": 10,
            }
        )

    domain = mock_client.search_read.call_args[0][1]
    assert ("name", "ilike", "Acme") in domain
    assert ("email", "ilike", "acme") in domain
    assert ("is_company", "=", True) in domain
    assert mock_client.search_read.call_args[1]["limit"] == 10

    payload = json.loads(result[0].text)
    assert payload[0]["name"] == "Acme Corp"


@pytest.mark.asyncio
async def test_search_tasks_user_filter(mock_client):
    mock_client.search_read.return_value = []
    with patch("odoo_mcp_server.tools.common.get_odoo_client", return_value=mock_client):
        await _search_tasks({"user_id": 5})

    domain = mock_client.search_read.call_args[0][1]
    assert ("user_ids", "in", [5]) in domain


@pytest.mark.asyncio
async def test_create_task_blocked_in_readonly(mock_client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ODOO_READONLY", "true")
    with patch("odoo_mcp_server.tools.common.get_odoo_client", return_value=mock_client):
        with pytest.raises(PermissionError, match="ODOO_READONLY"):
            await _create_task({"name": "Test task"})


@pytest.mark.asyncio
async def test_create_task_assigns_user_ids(mock_client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ODOO_READONLY", raising=False)
    with patch("odoo_mcp_server.tools.common.get_odoo_client", return_value=mock_client):
        result = await _create_task({"name": "Test task", "user_id": 3})

    values = mock_client.create.call_args[0][1]
    assert values["user_ids"] == [(6, 0, [3])]
    assert "Task created successfully" in result[0].text
