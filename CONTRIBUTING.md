# Contributing

Thanks for your interest in improving Odoo MCP Server.

## Development setup

```bash
git clone https://github.com/PetrStichauer/odoo-mcp-server.git
cd odoo-mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running checks

```bash
ruff check src/ tests/
black --check src/ tests/
pytest
```

## Pull requests

- Keep changes focused and include tests for new behavior.
- Update `README.md` and `CHANGELOG.md` when user-facing behavior changes.
- Do not commit credentials, `.env` files, or real Odoo API keys.

## Reporting issues

Use GitHub Issues and include your Odoo version, connection method (env vs profile), and the error message from `odoo-mcp-server test`.
