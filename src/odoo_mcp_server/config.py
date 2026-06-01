"""Odoo MCP Server - Configuration and connection profiles."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "odoo-mcp-server"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "connections.json"
ENV_CONNECTION_NAME = "env"

REQUIRED_FIELDS = ("url", "database", "username", "api_key")
ENV_FIELD_MAP = {
    "url": "ODOO_URL",
    "database": "ODOO_DB",
    "username": "ODOO_USER",
    "api_key": "ODOO_API_KEY",
}


@dataclass(frozen=True)
class OdooConfig:
    """Odoo connection configuration."""

    url: str
    database: str
    username: str
    api_key: str
    connection_name: str = ENV_CONNECTION_NAME

    @classmethod
    def from_dict(cls, data: dict[str, str], connection_name: str) -> OdooConfig:
        """Build config from a profile dictionary."""
        missing = [field for field in REQUIRED_FIELDS if not data.get(field)]
        if missing:
            raise ValueError(
                f"Connection '{connection_name}' is missing fields: {', '.join(missing)}"
            )

        return cls(
            url=str(data["url"]).rstrip("/"),
            database=str(data["database"]),
            username=str(data["username"]),
            api_key=str(data["api_key"]),
            connection_name=connection_name,
        )

    @property
    def xmlrpc_common_url(self) -> str:
        """Get XML-RPC common endpoint URL."""
        return f"{self.url}/xmlrpc/2/common"

    @property
    def xmlrpc_object_url(self) -> str:
        """Get XML-RPC object endpoint URL."""
        return f"{self.url}/xmlrpc/2/object"

    def public_summary(self) -> dict[str, str]:
        """Return non-secret connection metadata."""
        return {
            "name": self.connection_name,
            "url": self.url,
            "database": self.database,
            "username": self.username,
        }


class ConnectionStore:
    """Load and manage named Odoo connection profiles."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = Path(
            config_path or os.getenv("ODOO_MCP_CONFIG", str(DEFAULT_CONFIG_FILE))
        )

    @property
    def config_dir(self) -> Path:
        return self.config_path.parent

    def ensure_config_dir(self) -> None:
        """Create config directory with secure permissions."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.config_dir, 0o700)

    def load_raw(self) -> dict[str, Any]:
        """Load raw JSON from the profiles file."""
        if not self.config_path.exists():
            return {"default": "", "connections": {}}

        with self.config_path.open(encoding="utf-8") as handle:
            data = json.load(handle)

        if "connections" not in data or not isinstance(data["connections"], dict):
            raise ValueError(
                f"Invalid config file {self.config_path}: expected 'connections' object"
            )

        return data

    def save_raw(self, data: dict[str, Any]) -> None:
        """Write profiles file with secure permissions."""
        self.ensure_config_dir()
        temp_path = self.config_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.chmod(temp_path, 0o600)
        temp_path.replace(self.config_path)

    def list_connection_names(self) -> list[str]:
        """Return sorted profile names (no credentials)."""
        data = self.load_raw()
        return sorted(data.get("connections", {}).keys())

    def get_default_name(self) -> str | None:
        """Return default connection name from file, if set."""
        data = self.load_raw()
        default = data.get("default")
        return str(default) if default else None

    def get_active_connection_name(self) -> str | None:
        """Resolve active connection from env or file default."""
        if os.getenv("ODOO_CONNECTION"):
            return os.getenv("ODOO_CONNECTION")
        return self.get_default_name()

    def add_connection(
        self,
        name: str,
        url: str,
        database: str,
        username: str,
        api_key: str,
        *,
        make_default: bool = False,
    ) -> None:
        """Add or update a named connection profile."""
        data = self.load_raw()
        connections = data.setdefault("connections", {})
        connections[name] = {
            "url": url.rstrip("/"),
            "database": database,
            "username": username,
            "api_key": api_key,
        }
        if make_default or not data.get("default"):
            data["default"] = name
        self.save_raw(data)

    def resolve_config(self, connection_name: str | None = None) -> OdooConfig:
        """Resolve OdooConfig for a connection name or active default."""
        env_config = self._config_from_env()
        if env_config is not None:
            return env_config

        name = connection_name or self.get_active_connection_name()
        if not name:
            raise ValueError(
                "No Odoo connection configured. Options:\n"
                "  1. Run: odoo-mcp-server configure\n"
                "  2. Set ODOO_URL, ODOO_DB, ODOO_USER, ODOO_API_KEY environment variables\n"
                "  3. Set ODOO_CONNECTION to a profile name in connections.json"
            )

        data = self.load_raw()
        connections = data.get("connections", {})
        if name not in connections:
            available = ", ".join(sorted(connections.keys())) or "(none)"
            raise ValueError(
                f"Connection '{name}' not found. Available profiles: {available}. "
                "Run 'odoo-mcp-server configure' to add one."
            )

        return OdooConfig.from_dict(connections[name], name)

    def _config_from_env(self) -> OdooConfig | None:
        """Build config from env vars if all are set."""
        values = {field: os.getenv(env_name, "") for field, env_name in ENV_FIELD_MAP.items()}
        if not any(values.values()):
            return None

        if not all(values.values()):
            missing = [ENV_FIELD_MAP[field] for field, value in values.items() if not value]
            raise ValueError(
                f"Partial Odoo env configuration. Missing: {', '.join(missing)}. "
                "Set all ODOO_URL, ODOO_DB, ODOO_USER, ODOO_API_KEY or use connection profiles."
            )

        return OdooConfig.from_dict(values, ENV_CONNECTION_NAME)

    def list_connections_info(self) -> dict[str, Any]:
        """Return connection metadata for MCP list_connections tool."""
        env_config = self._config_from_env()
        if env_config is not None:
            return {
                "source": "environment",
                "active": ENV_CONNECTION_NAME,
                "default": ENV_CONNECTION_NAME,
                "connections": [
                    {
                        "name": ENV_CONNECTION_NAME,
                        "url": env_config.url,
                        "database": env_config.database,
                        "username": env_config.username,
                    }
                ],
            }

        data = self.load_raw()
        connections = data.get("connections", {})
        default = data.get("default")
        active = self.get_active_connection_name()

        return {
            "source": "profiles",
            "active": active,
            "default": default,
            "config_path": str(self.config_path),
            "connections": [
                {
                    "name": name,
                    "url": profile.get("url", ""),
                    "database": profile.get("database", ""),
                    "username": profile.get("username", ""),
                    "is_default": name == default,
                }
                for name, profile in sorted(connections.items())
            ],
        }


def is_readonly_mode() -> bool:
    """Return True when write operations should be blocked."""
    return os.getenv("ODOO_READONLY", "").lower() in {"1", "true", "yes", "on"}


def get_config_path() -> Path:
    """Return resolved config file path."""
    return Path(os.getenv("ODOO_MCP_CONFIG", str(DEFAULT_CONFIG_FILE)))
