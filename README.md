# Odoo MCP Server

A Model Context Protocol (MCP) server that exposes Odoo ERP functionality as tools for AI agents.

## Features

- **search_partners** - Search customers/contacts by name, email, or company status
- **get_partner** - Get detailed information about a specific partner
- **create_task** - Create new project tasks with optional assignment and deadlines
- **search_tasks** - List tasks with filters (project, user, state, priority)
- **get_project** - Get detailed project information

## Installation

```bash
# Clone or create the project
git clone <repository-url>
cd odoo-mcp-server

# Install with pip
pip install -e .

# Or install in development mode
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file or set environment variables:

```env
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database_name
ODOO_USER=your_username
ODOO_API_KEY=your_api_key_or_password
```

### Getting Odoo API Key

1. Log in to your Odoo instance
2. Go to your user profile (top right menu)
3. Click "Preferences" / "Account Security"
4. Under "API Keys", click "New API Key"
5. Give it a name and copy the generated key

## Usage

### Running the Server

```bash
# With environment variables loaded from .env
python -m odoo_mcp_server.server

# Or use the console script
odoo-mcp-server
```

### Using with Claude Desktop

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "odoo_mcp_server.server"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_DB": "your_database_name",
        "ODOO_USER": "your_username",
        "ODOO_API_KEY": "your_api_key"
      }
    }
  }
}
```

### Using with Other MCP Clients

The server uses stdio transport, so it works with any MCP client:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["-m", "odoo_mcp_server.server"],
    env={
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_DB": "your_database_name",
        "ODOO_USER": "your_username",
        "ODOO_API_KEY": "your_api_key",
    },
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        # Use the session to call tools
```

## Available Tools

### search_partners

Search for customers/contacts in Odoo.

**Parameters:**
- `name` (string, optional): Name or partial name to search for
- `email` (string, optional): Email address to search for
- `is_company` (boolean, optional): Filter by company vs individual
- `limit` (integer, default: 20): Maximum number of results

**Example:**
```json
{
  "name": "Acme",
  "is_company": true,
  "limit": 10
}
```

### get_partner

Get detailed information about a specific partner.

**Parameters:**
- `partner_id` (integer, required): ID of the partner to retrieve

**Example:**
```json
{
  "partner_id": 42
}
```

### create_task

Create a new project task.

**Parameters:**
- `name` (string, required): Name/title of the task
- `project_id` (integer, optional): ID of the project
- `user_id` (integer, optional): ID of the assigned user
- `partner_id` (integer, optional): ID of the related customer
- `description` (string, optional): Task description
- `priority` (string, optional): Priority - "0" (low) or "1" (high)
- `deadline` (string, optional): Deadline date in YYYY-MM-DD format

**Example:**
```json
{
  "name": "Review Q4 financials",
  "project_id": 5,
  "user_id": 3,
  "priority": "1",
  "deadline": "2026-03-15"
}
```

### search_tasks

Search for project tasks with filters.

**Parameters:**
- `name` (string, optional): Task name to search for
- `project_id` (integer, optional): Filter by project ID
- `user_id` (integer, optional): Filter by assigned user ID
- `state` (string, optional): Filter by state - "draft", "open", "pending", "cancelled", "done"
- `priority` (string, optional): Filter by priority - "0" (low) or "1" (high)
- `limit` (integer, default: 20): Maximum number of results

**Example:**
```json
{
  "project_id": 5,
  "state": "open",
  "priority": "1",
  "limit": 10
}
```

### get_project

Get project information by ID.

**Parameters:**
- `project_id` (integer, required): ID of the project to retrieve

**Example:**
```json
{
  "project_id": 5
}
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check src/
black src/

# Run tests
pytest
```

## Requirements

- Python 3.10+
- MCP SDK (`mcp>=1.0.0`)
- python-dotenv (for environment configuration)
- Access to an Odoo instance with XML-RPC enabled

## Security Notes

- Store your API key securely (use environment variables, not hardcoded values)
- Use Odoo API keys instead of passwords when possible
- Consider restricting the Odoo user's permissions to only what's necessary
- The server connects via XML-RPC over HTTPS (ensure your Odoo uses SSL)

## License

MIT
