# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-06-01

### Added

- Named connection profiles (`~/.config/odoo-mcp-server/connections.json`)
- CLI: `odoo-mcp-server configure`, `configure --list`, `test`
- MCP tools: `list_connections`, `test_connection`, `search_records`, `read_record`, `list_models`
- Optional `connection` parameter on all tools
- `ODOO_READONLY` mode to block write tools
- Generic search limits and sanitized XML-RPC error messages
- GitHub Actions CI, issue templates, CONTRIBUTING and SECURITY docs
- Example configs for Cursor and Claude Desktop

### Changed

- Refactored tools into modular handlers under `src/odoo_mcp_server/tools/`
- README rewrite with quick start and multi-connection setup

## [0.1.0] - 2026-02-27

### Added

- Initial MCP server with partner, task, and project tools
- Environment-based Odoo XML-RPC configuration
