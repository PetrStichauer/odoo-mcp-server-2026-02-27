"""Odoo MCP Server - Odoo XML-RPC client."""

import xmlrpc.client
from typing import Any, cast

from .config import OdooConfig


class OdooClient:
    """Client for interacting with Odoo via XML-RPC."""

    def __init__(self, config: OdooConfig):
        self.config = config
        self._uid: int | None = None
        self._common = None
        self._object = None

    def _get_common_proxy(self):
        """Get or create the common proxy."""
        if self._common is None:
            self._common = xmlrpc.client.ServerProxy(self.config.xmlrpc_common_url)
        return self._common

    def _get_object_proxy(self):
        """Get or create the object proxy."""
        if self._object is None:
            self._object = xmlrpc.client.ServerProxy(self.config.xmlrpc_object_url)
        return self._object

    def authenticate(self) -> int:
        """Authenticate with Odoo and return user ID."""
        if self._uid is not None:
            return self._uid

        common = self._get_common_proxy()
        uid = common.authenticate(
            self.config.database,
            self.config.username,
            self.config.api_key,
            {},
        )

        if not uid:
            raise AuthenticationError("Failed to authenticate with Odoo")

        self._uid = cast(int, uid)
        return cast(int, uid)

    def call(self, model: str, method: str, *args, **kwargs) -> Any:
        """Call a method on an Odoo model."""
        uid = self.authenticate()
        obj = self._get_object_proxy()

        return obj.execute_kw(
            self.config.database,
            uid,
            self.config.api_key,
            model,
            method,
            args,
            kwargs,
        )

    def search_read(
        self,
        model: str,
        domain: list,
        fields: list[str] | None = None,
        limit: int = 0,
        offset: int = 0,
        order: str = "",
    ) -> list[dict]:
        """Search and read records from a model."""
        kwargs = {}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order

        return self.call(model, "search_read", domain, **kwargs)

    def read(self, model: str, ids: list[int], fields: list[str] | None = None) -> list[dict]:
        """Read records by IDs."""
        kwargs = {}
        if fields:
            kwargs["fields"] = fields

        return self.call(model, "read", ids, **kwargs)

    def create(self, model: str, values: dict) -> int:
        """Create a new record."""
        return self.call(model, "create", values)

    def write(self, model: str, ids: list[int], values: dict) -> bool:
        """Update existing records."""
        return self.call(model, "write", ids, values)

    def unlink(self, model: str, ids: list[int]) -> bool:
        """Delete records."""
        return self.call(model, "unlink", ids)

    def search(self, model: str, domain: list, limit: int = 0) -> list[int]:
        """Search for record IDs."""
        kwargs = {}
        if limit:
            kwargs["limit"] = limit

        return self.call(model, "search", domain, **kwargs)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class OdooError(Exception):
    """Raised when an Odoo operation fails."""
    pass
