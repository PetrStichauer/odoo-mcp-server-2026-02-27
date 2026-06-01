# Odoo MCP Server

[![CI](https://github.com/PetrStichauer/odoo-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/PetrStichauer/odoo-mcp-server/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![MCP](https://img.shields.io/badge/MCP-stdio-purple.svg)

A [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes Odoo ERP data and actions as tools for AI agents in Cursor, Claude Desktop, and other MCP clients.

**Author:** [Petr Stichauer](https://github.com/PetrStichauer)

## Why this server?

Instead of teaching an agent raw Odoo XML-RPC, this server provides typed MCP tools with safe defaults: connection profiles, read-only mode, result limits, and sanitized error messages. Point your agent at customers, projects, tasks, or any Odoo model with minimal setup.

## Features

| Category | Tools |
|----------|-------|
| Connections | `list_connections`, `test_connection` |
| Partners | `search_partners`, `get_partner` |
| Projects & tasks | `get_project`, `search_tasks`, `create_task` |
| Generic reads | `search_records`, `read_record`, `list_models` |

All tools accept an optional `connection` parameter for multi-instance setups.

## Quick start

```bash
git clone https://github.com/PetrStichauer/odoo-mcp-server.git
cd odoo-mcp-server
pip install -e .

# Interactive setup (stores API key locally with secure permissions)
odoo-mcp-server configure

# Verify authentication
odoo-mcp-server test

# Run the MCP server (stdio)
odoo-mcp-server
```

### Getting an Odoo API key

1. Log in to your Odoo instance
2. Open your user profile → Preferences / Account Security
3. Under **API Keys**, create a new key and copy it
4. Use a dedicated Odoo user with least-privilege access

## Configuration

### Named connection profiles (recommended)

Profiles are stored at `~/.config/odoo-mcp-server/connections.json` (mode `0600`, directory `0700`).

```bash
# Add or update a profile
odoo-mcp-server configure

# List profiles (no secrets shown)
odoo-mcp-server configure --list

# Test a specific profile
odoo-mcp-server test --connection staging
```

Set the active profile when starting the server:

```bash
export ODOO_CONNECTION=production
odoo-mcp-server
```

Override the profiles file path:

```bash
export ODOO_MCP_CONFIG=/path/to/connections.json
```

### Environment variables (CI / single connection)

Set all four variables to use an implicit `"env"` connection (overrides profiles):

```env
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database_name
ODOO_USER=your_username
ODOO_API_KEY=your_api_key
```

See [`.env.example`](.env.example) for all options including `ODOO_READONLY`.

### Read-only mode

Block write tools (`create_task`, future writes) for read-only agents:

```bash
export ODOO_READONLY=true
```

## MCP client setup

### Cursor

Add to `.cursor/mcp.json` (see [`examples/cursor-mcp.json`](examples/cursor-mcp.json)):

```json
{
  "mcpServers": {
    "odoo": {
      "command": "odoo-mcp-server",
      "env": {
        "ODOO_CONNECTION": "production"
      }
    }
  }
}
```

**Multiple Odoo instances:** add another entry with a different name and `ODOO_CONNECTION` value — same install, different profile.

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS (see [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json)):

```json
{
  "mcpServers": {
    "odoo": {
      "command": "odoo-mcp-server",
      "env": {
        "ODOO_CONNECTION": "production"
      }
    }
  }
}
```

## Tool reference

### Connection tools

- **`list_connections`** — profile names, active/default connection, URLs (no credentials)
- **`test_connection`** — authenticate and return server version info

### Partner tools

- **`search_partners`** — filter by name, email, company flag
- **`get_partner`** — full partner details by ID

### Project & task tools

- **`get_project`** — project details by ID
- **`search_tasks`** — filter by project, user, state, priority
- **`create_task`** — create a task (blocked when `ODOO_READONLY=true`)

### Generic read tools

- **`search_records`** — `search_read` on any model with domain, fields, limit (max 100), order
- **`read_record`** — read one record by ID
- **`list_models`** — list non-transient models from `ir.model`

All search tools enforce a maximum of **100 records** and **20 domain clauses**.

## Odoo compatibility

Tested against Odoo **16 / 17 / 18 Community** via XML-RPC.

Note: `project.task` assignee field changed in newer versions (`user_ids` vs legacy `user_id`). This server uses `user_ids` for Odoo 17+.

## Development

```bash
pip install -e ".[dev]"
ruff check src/ tests/
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for pull request guidelines.

## Security

- Never commit `.env` or API keys — see [SECURITY.md](SECURITY.md)
- Profiles store API keys in plaintext locally (standard for MCP); use env vars on shared machines
- Use least-privilege Odoo users and `ODOO_READONLY` when agents should not write data

## License

MIT — see [LICENSE](LICENSE). Copyright © 2026 Petr Stichauer.
