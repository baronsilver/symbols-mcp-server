# Symbols MCP Server

An MCP (Model Context Protocol) server that exposes the Symbols/DOMQL v3 AI assistant capabilities to any MCP-compatible platform — **Cursor**, **Claude Code**, **Windsurf**, and more.

## Features

### Tools
| Tool | Description |
|------|-------------|
| `generate_component` | Generate a Symbols/DOMQL v3 component from natural language |
| `generate_page` | Generate a full page with routing support |
| `generate_project` | Scaffold a complete multi-file Symbols project |
| `convert_to_symbols` | Convert React/Angular/Vue/HTML to Symbols/DOMQL v3 |
| `search_symbols_docs` | Search Symbols documentation (vector or local) |
| `explain_symbols_concept` | Explain any Symbols concept with examples |
| `review_symbols_code` | Review code for v3 compliance and best practices |
| `create_design_system` | Generate design system files (colors, spacing, themes, icons) |

### Resources
| Resource URI | Description |
|-------------|-------------|
| `symbols://skills/domql-v3-reference` | Complete DOMQL v3 syntax reference |
| `symbols://skills/project-structure` | Project folder structure conventions |
| `symbols://skills/design-direction` | Modern UI/UX design direction |
| `symbols://skills/migration-guide` | React/Angular/Vue → Symbols migration |
| `symbols://skills/v2-to-v3-migration` | DOMQL v2 → v3 changes |
| `symbols://skills/quickstart` | CLI setup and quickstart |
| `symbols://reference/spacing-tokens` | Spacing token reference table |
| `symbols://reference/atom-components` | Built-in primitive components |
| `symbols://reference/event-handlers` | Event handler reference |

### Prompts
| Prompt | Description |
|--------|-------------|
| `symbols_component_prompt` | Template for component generation |
| `symbols_migration_prompt` | Template for framework migration |
| `symbols_project_prompt` | Template for project scaffolding |
| `symbols_review_prompt` | Template for code review |

---

## Installation

### Quick Start (No API Keys Required!)

1. **Clone the repository**:
```bash
git clone https://github.com/baronsilver/symbols-mcp-server.git
cd symbols-mcp-server
```

2. **Install dependencies**:
```bash
pip install uv
uv sync
```

3. **Configure**:
```bash
cp .env.example .env
# Edit .env and add either:
# - SYMBOLS_MCP_URL (contact maintainer for public server URL)
# - Or your own OPENROUTER_API_KEY from https://openrouter.ai
```

4. **Test the server**:
```bash
uv run symbols-mcp
```

### Advanced: Use Your Own API Key

If you prefer to use your own OpenRouter API key:

1. Get an API key from https://openrouter.ai
2. Edit `.env` and replace:
```bash
# Comment out the proxy URL
# SYMBOLS_MCP_URL=your_mcp_server_url_here

# Add your own key
OPENROUTER_API_KEY=your_key_here
```

---

## Platform Integration

### Claude Code

```bash
claude mcp add symbols-mcp -- uv run --directory C:\repos\symbols-mcp-server symbols-mcp
```

Or manually edit `~/.claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "python",
      "args": ["-m", "uv", "run", "--directory", "C:\\repos\\symbols-mcp-server", "symbols-mcp"],
      "env": {
        "SYMBOLS_MCP_URL": "your_mcp_server_url_here"
      }
    }
  }
}
```

Contact the maintainer for the public server URL, or use your own OPENROUTER_API_KEY.

### Cursor

Add to your Cursor MCP settings (`.cursor/mcp.json` in your project or global settings):

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\repos\\symbols-mcp-server", "symbols-mcp"],
      "env": {
        "OPENROUTER_API_KEY": "your_key_here"
      }
    }
  }
}
```

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "python",
      "args": ["-m", "uv", "run", "--directory", "C:\\repos\\symbols-mcp-server", "symbols-mcp"],
      "env": {
        "SYMBOLS_MCP_URL": "your_mcp_server_url_here"
      }
    }
  }
}
```

Contact the maintainer for the public server URL, or use your own OPENROUTER_API_KEY.

### Alternative: Using pip

If you prefer pip over uv:

```bash
pip install -e C:\repos\symbols-mcp-server
```

Then use `symbols-mcp` as the command in any MCP config:

```json
{
  "mcpServers": {
    "symbols-mcp": {
      "command": "symbols-mcp",
      "env": {
        "OPENROUTER_API_KEY": "your_key_here"
      }
    }
  }
}
```

---

## Development

### Test with MCP Inspector

```bash
# Start the server
uv run symbols-mcp

# In another terminal, use the MCP Inspector
npx -y @modelcontextprotocol/inspector
```

### Run directly

```bash
uv run symbols-mcp
```

### Debug mode

```bash
uv run mcp dev symbols_mcp/server.py
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | **Yes** | — | API key for OpenRouter (powers AI generation) |
| `SUPABASE_URL` | No | — | Supabase project URL for vector search |
| `SUPABASE_KEY` | No | — | Supabase service role key |
| `LLM_MODEL` | No | `openai/gpt-4.1-mini` | AI model to use via OpenRouter |
| `SYMBOLS_SKILLS_DIR` | No | `./symbols_mcp/skills` | Path to skills markdown files |

---

## Architecture

```
symbols-mcp-server/
├── pyproject.toml              # Project config and dependencies
├── .env.example                # Environment variable template
├── README.md                   # This file
└── symbols_mcp/
    ├── __init__.py
    ├── server.py               # MCP server with tools, resources, prompts
    └── skills/                 # Bundled Symbols knowledge base
        ├── CLAUDE.md           # DOMQL v3 complete reference
        ├── SYMBOLS_LOCAL_INSTRUCTIONS.md  # Project structure rules
        ├── DESIGN_DIRECTION.md # UI/UX design direction
        ├── MIGRATE_TO_SYMBOLS.md # Framework migration guide
        ├── DOMQL_v2-v3_MIGRATION.md # v2→v3 changes
        └── QUICKSTART.md       # CLI quickstart
```

The server reads skills files at startup and uses them as context for all AI-powered tools.
When Supabase is configured, the `search_symbols_docs` tool also queries the vector database
for additional documentation matches.

---

## Publishing

### NPM Package (Recommended)

To make your MCP server easily installable via `npx` or `npm`:

1. **Create `package.json`**:
```json
{
  "name": "@baronsilver/symbols-mcp",
  "version": "1.0.0",
  "description": "MCP server for Symbols/DOMQL v3 AI assistant",
  "bin": {
    "symbols-mcp": "./run.sh"
  },
  "repository": "baronsilver/symbols-mcp-server",
  "keywords": ["mcp", "symbols", "domql", "ai", "code-generation"],
  "license": "MIT"
}
```

2. **Publish to NPM**:
```bash
npm login
npm publish --access public
```

3. **Users can install with**:
```bash
npx @baronsilver/symbols-mcp
```

### PyPI Package

To publish as a Python package:

```bash
python -m build
python -m twine upload dist/*
```

Users can then install with:
```bash
pip install symbols-mcp-server
```

### MCP Registry

Submit to the official MCP registry at https://github.com/modelcontextprotocol/servers

Create a PR adding your server to the registry with the `mcp.json` metadata.

### Smithery (MCP Marketplace)

Publish to Smithery at https://smithery.ai for broader discovery.

1. Create account at https://smithery.ai
2. Submit your GitHub repository
3. Users can install with one click
