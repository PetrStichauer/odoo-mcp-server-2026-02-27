"""Odoo MCP Server - Configuration module."""

import os
from dataclasses import dataclass


@dataclass
class OdooConfig:
    """Odoo connection configuration."""

    url: str
    database: str
    username: str
    api_key: str

    @classmethod
    def from_env(cls) -> "OdooConfig":
        """Load configuration from environment variables."""
        url = os.getenv("ODOO_URL", "")
        database = os.getenv("ODOO_DB", "")
        username = os.getenv("ODOO_USER", "")
        api_key = os.getenv("ODOO_API_KEY", "")

        if not all([url, database, username, api_key]):
            missing = []
            if not url:
                missing.append("ODOO_URL")
            if not database:
                missing.append("ODOO_DB")
            if not username:
                missing.append("ODOO_USER")
            if not api_key:
                missing.append("ODOO_API_KEY")
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return cls(
            url=url.rstrip("/"),
            database=database,
            username=username,
            api_key=api_key,
        )

    @property
    def xmlrpc_common_url(self) -> str:
        """Get XML-RPC common endpoint URL."""
        return f"{self.url}/xmlrpc/2/common"

    @property
    def xmlrpc_object_url(self) -> str:
        """Get XML-RPC object endpoint URL."""
        return f"{self.url}/xmlrpc/2/object"
