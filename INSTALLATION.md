# Symbols MCP Server - Installation Guide

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/baronsilver/symbols-mcp-server.git
cd symbols-mcp-server
```

### 2. Install Dependencies
```bash
pip install uv
uv sync
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
# Or contact maintainer for shared proxy URL
```

---

## Platform Integration

### Windsurf

Edit `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "python",
      "args": ["-m", "uv", "run", "--directory", "/path/to/symbols-mcp-server", "symbols-mcp"],
      "env": {
        "OPENROUTER_API_KEY": "your_key_here"
      }
    }
  }
}
```

**Replace `/path/to/symbols-mcp-server`** with your actual path.

Then restart Windsurf.

### Claude Code

Edit `~/.config/claude/mcp.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "python",
      "args": ["-m", "uv", "run", "--directory", "/path/to/symbols-mcp-server", "symbols-mcp"],
      "env": {
        "OPENROUTER_API_KEY": "your_key_here"
      }
    }
  }
}
```

**Replace `/path/to/symbols-mcp-server`** with your actual path.

Then restart Claude Code.

---

## Available Tools

Once configured, you'll have access to 8 AI-powered tools:

1. **generate_component** - Create Symbols/DOMQL v3 components
2. **generate_page** - Create pages with routing
3. **generate_project** - Scaffold complete projects
4. **convert_to_symbols** - Migrate React/Vue/Angular to Symbols
5. **search_symbols_docs** - Search documentation
6. **explain_symbols_concept** - Get concept explanations
7. **review_symbols_code** - Code review for v3 compliance
8. **create_design_system** - Generate design systems

---

## Configuration Options

### Option 1: Shared Proxy (Recommended for group members)

Contact the maintainer for the shared proxy URL, then edit `.env`:
```bash
SYMBOLS_MCP_URL=<provided_proxy_url>
```

Update your Windsurf/Claude Code config:
```json
"env": {
  "SYMBOLS_MCP_URL": "<provided_proxy_url>"
}
```

### Option 2: Your Own API Key

Get an API key from https://openrouter.ai and edit `.env`:
```bash
OPENROUTER_API_KEY=your_key_here
```

Update your Windsurf/Claude Code config:
```json
"env": {
  "OPENROUTER_API_KEY": "your_key_here"
}
```

---

## Troubleshooting

### "Error: Either SYMBOLS_MCP_URL or OPENROUTER_API_KEY must be set"

Make sure your `.env` file has one of these set:
```bash
cat .env
```

### "401 Unauthorized"

If using your own API key, verify it's correct at https://openrouter.ai

### "Connection refused"

If using the shared proxy, contact the maintainer to verify service status.

---

## Support

- GitHub Issues: https://github.com/baronsilver/symbols-mcp-server/issues
- Documentation: https://github.com/baronsilver/symbols-mcp-server
