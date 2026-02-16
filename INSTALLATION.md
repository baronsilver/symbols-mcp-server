# Symbols MCP Server - Installation Guide

## Quick Start (No API Keys Required!)

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

### 3. Configure (Copy the public config)
```bash
cp .env.public .env
```

That's it! No API keys needed - the server uses a public proxy.

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
        "SYMBOLS_PROXY_URL": "https://symbols-mcp-server-production.up.railway.app"
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
        "SYMBOLS_PROXY_URL": "https://symbols-mcp-server-production.up.railway.app"
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

## Advanced: Use Your Own API Key

If you prefer to use your own OpenRouter API key:

1. Get an API key from https://openrouter.ai
2. Edit `.env`:
```bash
# Comment out the proxy
# SYMBOLS_PROXY_URL=https://symbols-mcp-server-production.up.railway.app

# Add your key
OPENROUTER_API_KEY=your_key_here
```

3. Update your Windsurf/Claude Code config to use `OPENROUTER_API_KEY` instead of `SYMBOLS_PROXY_URL`

---

## Troubleshooting

### "Error: Either SYMBOLS_PROXY_URL or OPENROUTER_API_KEY must be set"

Make sure your `.env` file has one of these set:
```bash
cat .env
```

### "401 Unauthorized"

If using your own API key, verify it's correct at https://openrouter.ai

### "Connection refused"

The proxy service might be down. Check status at:
https://symbols-mcp-server-production.up.railway.app/health

---

## Support

- GitHub Issues: https://github.com/baronsilver/symbols-mcp-server/issues
- Documentation: https://github.com/baronsilver/symbols-mcp-server
