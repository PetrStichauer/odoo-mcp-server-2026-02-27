# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.2.x   | Yes       |
| < 0.2   | No        |

## Reporting a vulnerability

If you discover a security issue, please open a private security advisory on GitHub or contact the maintainer via GitHub profile: https://github.com/PetrStichauer

Do not file public issues for undisclosed vulnerabilities.

## Credential handling

- Never commit `.env`, `connections.json`, or API keys to the repository.
- Store connection profiles in `~/.config/odoo-mcp-server/connections.json` with file mode `0600`.
- Prefer Odoo API keys over account passwords.
- Use a dedicated Odoo user with least-privilege access.
- Set `ODOO_READONLY=true` when the MCP client should not create or modify records.

## Pre-publish checklist

Before pushing to a public repository:

```bash
git log -p --all -S 'ODOO_API_KEY=' -- . ':!*.example'
```

Ensure no real secrets appear in git history.
