"""Odoo MCP Server - Odoo XML-RPC client."""

from __future__ import annotations

import re
import xmlrpc.client
from typing import Any, cast

from .config import OdooConfig


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class OdooError(Exception):
    """Raised when an Odoo operation fails."""


def _sanitize_fault_message(message: str) -> str:
    """Extract a concise error message from XML-RPC faults."""
    text = str(message).strip()
    if not text:
        return "Odoo request failed"

    # Odoo faults often embed Python tracebacks; keep the last meaningful line.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("Traceback"):
            continue
        if line.startswith("File "):
            continue
        cleaned = re.sub(r"^[\w.]+:\s*", "", line)
        if cleaned:
            return cleaned[:500]

    return text[:500]


class OdooClient:
    """Client for interacting with Odoo via XML-RPC."""

    def __init__(self, config: OdooConfig):
        self.config = config
        self._uid: int | None = None
        self._common: xmlrpc.client.ServerProxy | None = None
        self._object: xmlrpc.client.ServerProxy | None = None

    def _get_common_proxy(self) -> xmlrpc.client.ServerProxy:
        """Get or create the common proxy."""
        if self._common is None:
            self._common = xmlrpc.client.ServerProxy(self.config.xmlrpc_common_url)
        return self._common

    def _get_object_proxy(self) -> xmlrpc.client.ServerProxy:
        """Get or create the object proxy."""
        if self._object is None:
            self._object = xmlrpc.client.ServerProxy(self.config.xmlrpc_object_url)
        return self._object

    def get_server_version(self) -> dict[str, Any]:
        """Return Odoo server version info."""
        try:
            common = self._get_common_proxy()
            return cast(dict[str, Any], common.version())
        except xmlrpc.client.Fault as exc:
            raise OdooError(_sanitize_fault_message(exc.faultString)) from exc
        except Exception as exc:
            raise OdooError(f"Failed to reach Odoo server: {exc}") from exc

    def authenticate(self) -> int:
        """Authenticate with Odoo and return user ID."""
        if self._uid is not None:
            return self._uid

        try:
            common = self._get_common_proxy()
            uid = common.authenticate(
                self.config.database,
                self.config.username,
                self.config.api_key,
                {},
            )
        except xmlrpc.client.Fault as exc:
            raise AuthenticationError(_sanitize_fault_message(exc.faultString)) from exc
        except Exception as exc:
            raise AuthenticationError(f"Authentication failed: {exc}") from exc

        if not uid:
            raise AuthenticationError(
                f"Failed to authenticate user '{self.config.username}' "
                f"on database '{self.config.database}'"
            )

        self._uid = cast(int, uid)
        return self._uid

    def call(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        """Call a method on an Odoo model."""
        uid = self.authenticate()
        obj = self._get_object_proxy()

        try:
            return obj.execute_kw(
                self.config.database,
                uid,
                self.config.api_key,
                model,
                method,
                args,
                kwargs,
            )
        except xmlrpc.client.Fault as exc:
            raise OdooError(
                f"Odoo error on {model}.{method}: {_sanitize_fault_message(exc.faultString)}"
            ) from exc
        except Exception as exc:
            raise OdooError(f"Odoo request failed on {model}.{method}: {exc}") from exc

    def search_read(
        self,
        model: str,
        domain: list[Any],
        fields: list[str] | None = None,
        limit: int = 0,
        offset: int = 0,
        order: str = "",
    ) -> list[dict[str, Any]]:
        """Search and read records from a model."""
        kwargs: dict[str, Any] = {}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order

        return cast(list[dict[str, Any]], self.call(model, "search_read", domain, **kwargs))

    def read(
        self, model: str, ids: list[int], fields: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Read records by IDs."""
        kwargs: dict[str, Any] = {}
        if fields:
            kwargs["fields"] = fields

        return cast(list[dict[str, Any]], self.call(model, "read", ids, **kwargs))

    def create(self, model: str, values: dict[str, Any]) -> int:
        """Create a new record."""
        return cast(int, self.call(model, "create", values))

    def write(self, model: str, ids: list[int], values: dict[str, Any]) -> bool:
        """Update existing records."""
        return cast(bool, self.call(model, "write", ids, values))

    def unlink(self, model: str, ids: list[int]) -> bool:
        """Delete records."""
        return cast(bool, self.call(model, "unlink", ids))

    def search(self, model: str, domain: list[Any], limit: int = 0) -> list[int]:
        """Search for record IDs."""
        kwargs: dict[str, Any] = {}
        if limit:
            kwargs["limit"] = limit

        return cast(list[int], self.call(model, "search", domain, **kwargs))
