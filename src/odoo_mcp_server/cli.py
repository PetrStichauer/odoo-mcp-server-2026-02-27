"""CLI for Odoo MCP Server."""

from __future__ import annotations

import argparse
import getpass
import sys

from .client_pool import get_odoo_client
from .config import ConnectionStore
from .server import run_server


def _prompt(label: str, *, secret: bool = False, default: str = "") -> str:
    if secret:
        value = getpass.getpass(f"{label}: ")
    else:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        if not value and default:
            return default
    return value.strip()


def cmd_configure(args: argparse.Namespace) -> int:
    """Interactive connection profile setup."""
    store = ConnectionStore()

    if args.list:
        names = store.list_connection_names()
        default = store.get_default_name()
        if not names:
            print("No connection profiles configured.")
            print(f"Config file: {store.config_path}")
            return 0

        print(f"Config file: {store.config_path}")
        print(f"Default: {default or '(not set)'}")
        for name in names:
            marker = " (default)" if name == default else ""
            print(f"  - {name}{marker}")
        return 0

    print("Configure an Odoo connection profile.")
    print("Press Enter to keep the current default name suggestion.\n")

    name = _prompt("Connection name", default="production")
    if not name:
        print("Connection name is required.", file=sys.stderr)
        return 1

    url = _prompt("Odoo URL (https://...)")
    database = _prompt("Database name")
    username = _prompt("Username")
    api_key = _prompt("API key", secret=True)

    if not all([url, database, username, api_key]):
        print("All fields are required.", file=sys.stderr)
        return 1

    make_default = args.default or not store.get_default_name()
    store.add_connection(
        name,
        url,
        database,
        username,
        api_key,
        make_default=make_default,
    )

    print(f"\nSaved connection '{name}' to {store.config_path}")
    if make_default:
        print(f"Set '{name}' as default connection.")
    print("\nStart the MCP server with:")
    print(f"  ODOO_CONNECTION={name} odoo-mcp-server")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Test authentication for a connection."""
    try:
        client = get_odoo_client(args.connection)
        uid = client.authenticate()
        version = client.get_server_version()
    except Exception as exc:
        print(f"Connection failed: {exc}", file=sys.stderr)
        return 1

    print("Connection successful.")
    print(f"  Connection: {client.config.connection_name}")
    print(f"  URL:        {client.config.url}")
    print(f"  Database:   {client.config.database}")
    print(f"  Username:   {client.config.username}")
    print(f"  UID:        {uid}")
    print(f"  Version:    {version}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="odoo-mcp-server",
        description="Odoo MCP Server — expose Odoo ERP as AI tools",
    )
    subparsers = parser.add_subparsers(dest="command")

    configure = subparsers.add_parser("configure", help="Add or list connection profiles")
    configure.add_argument(
        "--list",
        action="store_true",
        help="List configured connection names (no secrets)",
    )
    configure.add_argument(
        "--default",
        action="store_true",
        help="Set the new/edited profile as default",
    )
    configure.set_defaults(func=cmd_configure)

    test = subparsers.add_parser("test", help="Test Odoo authentication")
    test.add_argument(
        "--connection",
        help="Connection profile name (uses ODOO_CONNECTION or default when omitted)",
    )
    test.set_defaults(func=cmd_test)

    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        run_server()
        return

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
