"""
Symbols MCP Server — Exposes Symbols/DOMQL AI assistant capabilities
as tools, resources, and prompts for Cursor, Claude Code, and Windsurf.
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4.1-mini")
SKILLS_DIR = os.getenv("SYMBOLS_SKILLS_DIR", str(Path(__file__).resolve().parent / "skills"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("symbols-mcp")

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "Symbols AI Assistant",
    instructions=(
        "AI-powered assistant for the Symbols design-system framework. "
        "Generates DOMQL v3 components, pages, and full projects; converts "
        "React/Angular/Vue code to Symbols; searches Symbols documentation; "
        "and provides comprehensive framework reference."
    ),
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
SKILLS_PATH = Path(SKILLS_DIR)


def _read_skill(filename: str) -> str:
    """Read a skill markdown file from the skills directory."""
    path = SKILLS_PATH / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"Skill file '{filename}' not found at {path}"


async def _call_openrouter(prompt: str, max_tokens: int = 4000) -> str:
    """Call OpenRouter API for AI generation via proxy or direct."""
    # Check if using proxy (no API key needed) or direct (API key required)
    proxy_url = os.getenv("SYMBOLS_MCP_URL")
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if proxy_url:
        # Use proxy - no API key needed
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{proxy_url}/api/chat",
                headers={"Content-Type": "application/json"},
                json={
                    "model": os.getenv("LLM_MODEL", "openai/gpt-4.1-mini"),
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    elif api_key:
        # Direct OpenRouter call - API key required
        model = os.getenv("LLM_MODEL", "openai/gpt-4.1-mini")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/baronsilver/symbols-mcp-server",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    else:
        return "Error: Either SYMBOLS_MCP_URL or OPENROUTER_API_KEY must be set"


def _clean_code_response(text: str) -> str:
    """Strip markdown code fences from an AI response."""
    cleaned = text.strip()
    for prefix in ("```javascript", "```js", "```json", "```"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _build_symbols_system_context() -> str:
    """Build the core Symbols/DOMQL v3 knowledge context from skills files."""
    parts = []
    for fname in ("CLAUDE.md", "SYMBOLS_LOCAL_INSTRUCTIONS.md", "DESIGN_DIRECTION.md"):
        content = _read_skill(fname)
        if not content.startswith("Skill file"):
            parts.append(content)
    return "\n\n---\n\n".join(parts)


# Cache the system context at module load
_SYMBOLS_CONTEXT: str | None = None


def _get_symbols_context() -> str:
    global _SYMBOLS_CONTEXT
    if _SYMBOLS_CONTEXT is None:
        _SYMBOLS_CONTEXT = _build_symbols_system_context()
    return _SYMBOLS_CONTEXT


# ---------------------------------------------------------------------------
# TOOLS
# ---------------------------------------------------------------------------


@mcp.tool()
async def generate_component(
    description: str,
    component_name: str = "GeneratedComponent",
    interactive: bool = False,
) -> str:
    """Generate a Symbols/DOMQL v3 component from a natural-language description.

    Args:
        description: What the component should do/look like (e.g. "a pricing card with 3 tiers").
        component_name: PascalCase name for the component export.
        interactive: If True, include event handlers and state management.
    """
    ctx = _get_symbols_context()

    interactive_note = ""
    if interactive:
        interactive_note = """
IMPORTANT — This component must be INTERACTIVE:
- Include realistic event handlers (onClick, onInput, onSubmit, etc.)
- Add state management where needed (state: { ... }, s.update({ ... }))
- Use scope: { ... } for local helper functions
- Make buttons, inputs, and toggles functional
"""

    prompt = f"""You are an expert Symbols/DOMQL v3 developer. Generate a production-ready component.

{ctx}

---

TASK: Create a component named `{component_name}` based on this description:

{description}

{interactive_note}

RULES:
1. Output ONLY the JavaScript code — no markdown, no explanations.
2. Use DOMQL v3 syntax exclusively (extends, childExtends, flattened props, onX events).
3. Use design-system tokens for spacing (padding: 'A', gap: 'B'), colors, and typography.
4. Components are plain objects with named exports: export const {component_name} = {{ ... }}
5. NO imports between project files. Reference child components by PascalCase key.
6. Keep folders flat — this is a single component file.
7. Follow the modern UI/UX direction: clarity, hierarchy, minimal cognitive load.

OUTPUT:
"""
    response = await _call_openrouter(prompt)
    return _clean_code_response(response)


@mcp.tool()
async def generate_page(
    description: str,
    page_name: str = "main",
    route: str = "/",
) -> str:
    """Generate a Symbols/DOMQL v3 page with routing support.

    Args:
        description: What the page should contain (e.g. "a dashboard with metrics cards and a chart").
        page_name: camelCase name for the page export.
        route: The URL route for this page (e.g. "/dashboard").
    """
    ctx = _get_symbols_context()
    prompt = f"""You are an expert Symbols/DOMQL v3 developer. Generate a production-ready page.

{ctx}

---

TASK: Create a page named `{page_name}` (route: {route}) based on this description:

{description}

RULES:
1. Output ONLY the JavaScript code — no markdown, no explanations.
2. Pages extend from 'Page': export const {page_name} = {{ extends: 'Page', ... }}
3. Use DOMQL v3 syntax exclusively.
4. Use design-system tokens for all spacing, colors, typography.
5. Reference child components by PascalCase key name — no imports.
6. Include onRender/onInit for data loading if the page needs dynamic data.
7. Follow modern UI/UX: clear hierarchy, confident typography, balanced composition.
8. Pages use dash-case filenames but camelCase exports.

OUTPUT:
"""
    response = await _call_openrouter(prompt)
    return _clean_code_response(response)


@mcp.tool()
async def generate_project(
    description: str,
    project_name: str = "my-symbols-app",
) -> str:
    """Generate a complete multi-file Symbols/DOMQL v3 project structure.

    Args:
        description: What the application should be (e.g. "a restaurant website with menu, about, and contact pages").
        project_name: Name for the project.
    """
    ctx = _get_symbols_context()
    local_instructions = _read_skill("SYMBOLS_LOCAL_INSTRUCTIONS.md")

    prompt = f"""You are an expert Symbols/DOMQL v3 architect. Generate a COMPLETE project.

{ctx}

---

PROJECT STRUCTURE REFERENCE:
{local_instructions}

---

TASK: Create a complete Symbols project called "{project_name}" based on:

{description}

OUTPUT FORMAT — Return a JSON object with this exact structure:
{{
  "type": "project_structure",
  "title": "Project title",
  "description": "Brief description",
  "files": [
    {{
      "path": "smbls/index.js",
      "language": "javascript",
      "code": "// file contents here"
    }}
  ]
}}

RULES:
1. Include ALL required files: index.js, config.js, vars.js, dependencies.js, pages/index.js, components/index.js, functions/index.js, designSystem/index.js
2. Generate 6-10 meaningful files covering components, pages, design system, and state.
3. Use DOMQL v3 syntax exclusively. NO React/Vue/Angular syntax.
4. Use design-system tokens, not hardcoded pixel values.
5. All folders are FLAT — no subfolders within components/, pages/, etc.
6. Components use named exports (export const X = {{}}), designSystem uses default exports.
7. NO imports between project files for components — reference by PascalCase key.
8. Output ONLY the JSON — no markdown fences, no explanations.

OUTPUT:
"""
    response = await _call_openrouter(prompt, max_tokens=16000)
    cleaned = _clean_code_response(response)

    # Validate JSON
    try:
        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        return cleaned


@mcp.tool()
async def convert_to_symbols(
    code: str,
    source_framework: str = "auto",
) -> str:
    """Convert React, Angular, Vue, or HTML code to Symbols/DOMQL v3 format.

    Args:
        code: The source code to convert (React JSX, Angular template, Vue SFC, or HTML).
        source_framework: Source framework — "auto", "react", "angular", "vue", or "html".
    """
    migration_guide = _read_skill("MIGRATE_TO_SYMBOLS.md")
    v3_migration = _read_skill("DOMQL_v2-v3_MIGRATION.md")
    ctx = _get_symbols_context()

    prompt = f"""You are an expert migration assistant converting code to Symbols/DOMQL v3.

{ctx}

---

MIGRATION REFERENCE:
{migration_guide}

V2→V3 CHANGES:
{v3_migration}

---

TASK: Convert this {source_framework} code to Symbols/DOMQL v3 format:

```
{code}
```

RULES:
1. Output ONLY the converted Symbols/DOMQL v3 code — no markdown, no explanations.
2. Use v3 syntax ONLY: extends (not extend), childExtends (not childExtend), flattened props (no props: wrapper), onX events (no on: wrapper).
3. Replace all framework-specific patterns (useState, useEffect, v-if, *ngFor, etc.) with Symbols equivalents.
4. Use design-system tokens for spacing and colors where possible.
5. NO imports between project files — reference components by PascalCase key.
6. Components are plain objects with named exports.
7. Extract styles into flattened props with design tokens.

OUTPUT:
"""
    response = await _call_openrouter(prompt, max_tokens=12000)
    return _clean_code_response(response)


@mcp.tool()
async def search_symbols_docs(
    query: str,
    max_results: int = 3,
) -> str:
    """Search the Symbols documentation knowledge base for relevant information.

    Args:
        query: Natural language search query about Symbols/DOMQL.
        max_results: Maximum number of results to return (1-5).
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        # Fall back to local skills search if no Supabase
        results = []
        for fname in SKILLS_PATH.glob("*.md"):
            content = fname.read_text(encoding="utf-8")
            if query.lower() in content.lower():
                # Find relevant section
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if query.lower() in line.lower():
                        start = max(0, i - 2)
                        end = min(len(lines), i + 20)
                        snippet = "\n".join(lines[start:end])
                        results.append({"file": fname.name, "snippet": snippet})
                        break
                if len(results) >= max_results:
                    break

        if results:
            return json.dumps(results, indent=2)
        return f"No results found for '{query}'. Try a different search term."

    # Use Supabase vector search if available
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/rpc/match_documents",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                },
                json={"query_text": query, "match_count": max_results},
            )
            if resp.status_code == 200:
                docs = resp.json()
                results = []
                for doc in docs[:max_results]:
                    results.append({
                        "title": doc.get("title", "Untitled"),
                        "content": doc.get("content", "")[:1000],
                        "similarity": doc.get("similarity", 0),
                    })
                return json.dumps(results, indent=2)
            else:
                return f"Search API returned status {resp.status_code}. Falling back to local search."
    except Exception as e:
        logger.warning(f"Supabase search failed: {e}")
        return f"Search failed: {str(e)}"


@mcp.tool()
async def explain_symbols_concept(concept: str) -> str:
    """Explain a Symbols/DOMQL concept with examples (state, routing, events, design tokens, etc.).

    Args:
        concept: The concept to explain (e.g. "state management", "routing", "design tokens", "events", "children pattern").
    """
    ctx = _get_symbols_context()
    prompt = f"""You are an expert Symbols/DOMQL v3 instructor.

{ctx}

---

TASK: Explain the concept "{concept}" in Symbols/DOMQL v3.

RULES:
1. Give a clear, concise explanation (2-3 paragraphs max).
2. Include 1-2 practical code examples using DOMQL v3 syntax.
3. Highlight common mistakes and how to avoid them.
4. Reference relevant design-system tokens or patterns where applicable.
5. Do NOT use React/Vue/Angular — only Symbols/DOMQL v3.

OUTPUT:
"""
    return await _call_openrouter(prompt, max_tokens=4000, temperature=0.2)


@mcp.tool()
async def review_symbols_code(code: str) -> str:
    """Review Symbols/DOMQL code for correctness, best practices, and v3 compliance.

    Args:
        code: The Symbols/DOMQL code to review.
    """
    ctx = _get_symbols_context()
    prompt = f"""You are a strict Symbols/DOMQL v3 code reviewer.

{ctx}

---

TASK: Review this Symbols/DOMQL code for correctness and best practices:

```javascript
{code}
```

CHECK FOR:
1. v2 syntax violations: extend (should be extends), childExtend (should be childExtends), props: {{ }} wrapper, on: {{ }} wrapper
2. Forbidden imports between project files
3. Function-based components (must be plain objects)
4. Subfolder usage (must be flat)
5. Hardcoded pixel values instead of design tokens
6. Incorrect event handler signatures
7. Missing or incorrect extends declarations
8. Default exports for components (should use named exports)

OUTPUT FORMAT:
- List issues found with line references
- Provide corrected code for each issue
- Give an overall score (1-10) for v3 compliance
- Suggest improvements for better Symbols patterns

OUTPUT:
"""
    return await _call_openrouter(prompt, max_tokens=6000, temperature=0.1)


@mcp.tool()
async def create_design_system(
    description: str,
    include_theme: bool = True,
    include_icons: bool = True,
) -> str:
    """Generate Symbols design system files (colors, spacing, typography, theme, icons).

    Args:
        description: Description of the design direction (e.g. "dark modern SaaS dashboard", "light minimal e-commerce").
        include_theme: Whether to include theme definitions.
        include_icons: Whether to include a basic icon set.
    """
    ctx = _get_symbols_context()
    design_direction = _read_skill("DESIGN_DIRECTION.md")

    prompt = f"""You are an expert Symbols design-system architect.

{ctx}

---

DESIGN DIRECTION:
{design_direction}

---

TASK: Create a complete design system for: "{description}"

Generate the following files as a JSON object:
{{
  "files": [
    {{ "path": "designSystem/color.js", "code": "export default {{ ... }}" }},
    {{ "path": "designSystem/spacing.js", "code": "export default {{ ... }}" }},
    {{ "path": "designSystem/typography.js", "code": "export default {{ ... }}" }},
    {('{{ "path": "designSystem/theme.js", "code": "..." }},' if include_theme else "")}
    {('{{ "path": "designSystem/icons.js", "code": "..." }},' if include_icons else "")}
    {{ "path": "designSystem/index.js", "code": "..." }}
  ]
}}

RULES:
1. Colors: Define a cohesive palette with semantic names. Support dark/light modes using array format.
2. Spacing: Use base + ratio system (default base: 16, ratio: 1.618).
3. Typography: Use base + ratio system (default base: 16, ratio: 1.25).
4. Theme: Define component themes (button, field, document, transparent) with @dark/@light variants.
5. Icons: Use inline SVG strings with camelCase keys and currentColor for fill/stroke.
6. Index: Import and re-export all design system modules.
7. All files use default exports.
8. Output ONLY the JSON — no markdown, no explanations.

OUTPUT:
"""
    response = await _call_openrouter(prompt, max_tokens=10000)
    cleaned = _clean_code_response(response)
    try:
        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        return cleaned


# ---------------------------------------------------------------------------
# RESOURCES — Expose skills documentation as browsable resources
# ---------------------------------------------------------------------------


@mcp.resource("symbols://skills/domql-v3-reference")
def get_domql_v3_reference() -> str:
    """Complete DOMQL v3 syntax reference and rules."""
    return _read_skill("CLAUDE.md")


@mcp.resource("symbols://skills/project-structure")
def get_project_structure() -> str:
    """Symbols project folder structure and file conventions."""
    return _read_skill("SYMBOLS_LOCAL_INSTRUCTIONS.md")


@mcp.resource("symbols://skills/design-direction")
def get_design_direction() -> str:
    """Modern UI/UX design direction for generating Symbols interfaces."""
    return _read_skill("DESIGN_DIRECTION.md")


@mcp.resource("symbols://skills/migration-guide")
def get_migration_guide() -> str:
    """Guide for migrating React/Angular/Vue apps to Symbols/DOMQL v3."""
    return _read_skill("MIGRATE_TO_SYMBOLS.md")


@mcp.resource("symbols://skills/v2-to-v3-migration")
def get_v2_v3_migration() -> str:
    """DOMQL v2 to v3 migration changes and examples."""
    return _read_skill("DOMQL_v2-v3_MIGRATION.md")


@mcp.resource("symbols://skills/quickstart")
def get_quickstart() -> str:
    """Symbols CLI setup and usage quickstart guide."""
    return _read_skill("QUICKSTART.md")


@mcp.resource("symbols://reference/spacing-tokens")
def get_spacing_tokens() -> str:
    """Spacing token reference for the Symbols design system."""
    return """# Symbols Spacing Tokens

Ratio-based system (base 16px, ratio 1.618 golden ratio):

| Token | ~px  | Token | ~px  | Token | ~px  |
|-------|------|-------|------|-------|------|
| X     | 3    | A     | 16   | D     | 67   |
| Y     | 6    | A1    | 20   | E     | 109  |
| Z     | 10   | A2    | 22   | F     | 177  |
| Z1    | 12   | B     | 26   |       |      |
| Z2    | 14   | B1    | 32   |       |      |
|       |      | B2    | 36   |       |      |
|       |      | C     | 42   |       |      |
|       |      | C1    | 52   |       |      |
|       |      | C2    | 55   |       |      |

Usage: padding: 'A B', gap: 'C', borderRadius: 'Z', fontSize: 'B1'
Tokens work with padding, margin, gap, width, height, borderRadius, position, and any spacing property.
Negative values: margin: '-Y1 -Z2 - auto'
Math: padding: 'A+V2'
"""


@mcp.resource("symbols://reference/atom-components")
def get_atom_components() -> str:
    """Built-in primitive atom components in Symbols."""
    return """# Symbols Atom Components (Primitives)

| Atom       | HTML Tag   | Description                   |
|------------|------------|-------------------------------|
| Text       | <span>     | Text content                  |
| Box        | <div>      | Generic container             |
| Flex       | <div>      | Flexbox container             |
| Grid       | <div>      | CSS Grid container            |
| Link       | <a>        | Anchor with built-in router   |
| Input      | <input>    | Form input                    |
| Radio      | <input>    | Radio button                  |
| Checkbox   | <input>    | Checkbox                      |
| Svg        | <svg>      | SVG container                 |
| Icon       | <svg>      | Icon from icon sprite         |
| IconText   | <div>      | Icon + text combination       |
| Button     | <button>   | Button with icon/text support |
| Img        | <img>      | Image element                 |
| Iframe     | <iframe>   | Embedded frame                |
| Video      | <video>    | Video element                 |

Usage examples:
  { Box: { padding: 'A', background: 'surface' } }
  { Flex: { flow: 'y', gap: 'B', align: 'center center' } }
  { Grid: { columns: 'repeat(3, 1fr)', gap: 'A' } }
  { Link: { text: 'Click here', href: '/dashboard' } }
  { Button: { text: 'Submit', theme: 'primary', icon: 'check' } }
  { Icon: { name: 'chevronLeft' } }
  { Img: { src: 'photo.png', boxSize: 'D D' } }
"""


@mcp.resource("symbols://reference/event-handlers")
def get_event_handlers() -> str:
    """Event handler reference for Symbols/DOMQL v3."""
    return """# Symbols Event Handlers (v3)

## Lifecycle Events
  onInit: (el, state) => {}              // Once on creation
  onRender: (el, state) => {}            // On each render (return fn for cleanup)
  onUpdate: (el, state) => {}            // On props/state change
  onStateUpdate: (changes, el, state, context) => {}

## DOM Events
  onClick: (event, el, state) => {}
  onInput: (event, el, state) => {}
  onKeydown: (event, el, state) => {}
  onDblclick: (event, el, state) => {}
  onMouseover: (event, el, state) => {}
  onWheel: (event, el, state) => {}
  onSubmit: (event, el, state) => {}
  onLoad: (event, el, state) => {}

## Calling Functions
  onClick: (e, el) => el.call('functionName', args)  // Global function
  onClick: (e, el) => el.scope.localFn(el, s)        // Scope function
  onClick: (e, el) => el.methodName()                  // Element method

## State Updates
  onClick: (e, el, s) => s.update({ count: s.count + 1 })
  onClick: (e, el, s) => s.toggle('isActive')
  onClick: (e, el, s) => s.root.update({ modal: '/add-item' })

## Navigation
  onClick: (e, el) => el.router('/dashboard', el.getRoot())

## Cleanup Pattern
  onRender: (el, s) => {
    const interval = setInterval(() => { /* ... */ }, 1000)
    return () => clearInterval(interval)  // Called on element removal
  }
"""


# ---------------------------------------------------------------------------
# PROMPTS — Reusable prompt templates for common tasks
# ---------------------------------------------------------------------------


@mcp.prompt()
def symbols_component_prompt(description: str, component_name: str = "MyComponent") -> str:
    """Prompt template for generating a Symbols/DOMQL v3 component."""
    return f"""Generate a Symbols/DOMQL v3 component with these requirements:

Component Name: {component_name}
Description: {description}

Follow these strict rules:
- Use DOMQL v3 syntax ONLY (extends, childExtends, flattened props, onX events)
- Components are plain objects with named exports: export const {component_name} = {{ ... }}
- Use design-system tokens for spacing (A, B, C), colors, typography
- NO imports between files — reference components by PascalCase key name
- All folders flat — no subfolders
- Include responsive breakpoints (@mobile, @tablet) where appropriate
- Follow modern UI/UX: visual hierarchy, minimal cognitive load, confident typography

Output ONLY the JavaScript code."""


@mcp.prompt()
def symbols_migration_prompt(source_framework: str = "React") -> str:
    """Prompt template for migrating code to Symbols/DOMQL v3."""
    return f"""You are migrating {source_framework} code to Symbols/DOMQL v3.

Key conversion rules for {source_framework}:
- Components become plain objects (never functions)
- NO imports between project files
- All folders are flat — no subfolders
- Use extends/childExtends (v3 plural, never v2 singular)
- Flatten all props directly (no props: {{}} wrapper)
- Events use onX prefix (no on: {{}} wrapper)
- Use design-system tokens for spacing/colors
- State: state: {{ key: val }} + s.update({{ key: newVal }})
- Effects: onRender for mount, onStateUpdate for dependency changes
- Lists: children: (el, s) => s.items, childrenAs: 'state', childExtends: 'Item'

Provide the {source_framework} code to convert and I will output clean DOMQL v3."""


@mcp.prompt()
def symbols_project_prompt(description: str) -> str:
    """Prompt template for scaffolding a complete Symbols project."""
    return f"""Create a complete Symbols/DOMQL v3 project:

Project Description: {description}

Required structure (smbls/ folder):
- index.js (root export)
- config.js (platform config)
- vars.js (global constants)
- dependencies.js (external packages)
- components/ (PascalCase files, named exports)
- pages/ (dash-case files, camelCase exports, route mapping in index.js)
- functions/ (camelCase, called via el.call())
- designSystem/ (color, spacing, typography, theme, icons)
- state/ (default exports)

Rules:
- v3 syntax only — extends, childExtends, flattened props, onX events
- Design tokens for all spacing/colors (padding: 'A', not padding: '16px')
- Components are plain objects, never functions
- No imports between project files
- All folders completely flat

Generate all files with complete, production-ready code."""


@mcp.prompt()
def symbols_review_prompt() -> str:
    """Prompt template for reviewing Symbols/DOMQL code."""
    return """Review this Symbols/DOMQL code for v3 compliance and best practices.

Check for these violations:
1. v2 syntax: extend→extends, childExtend→childExtends, props:{}, on:{}
2. Imports between project files (FORBIDDEN)
3. Function-based components (must be plain objects)
4. Subfolders (must be flat)
5. Hardcoded pixels instead of design tokens
6. Wrong event handler signatures
7. Default exports for components (should be named)

Provide:
- Issues found with line references
- Corrected code for each issue
- Overall v3 compliance score (1-10)
- Improvement suggestions

Paste your code below:"""


# ---------------------------------------------------------------------------
# Health Check for Railway
# ---------------------------------------------------------------------------
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create FastAPI app for health check
app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return JSONResponse({
        "status": "healthy",
        "server": "Symbols MCP Server",
        "tools": len(mcp._tool_manager.list_tools()),
        "resources": len(mcp._resource_manager.list_resources()),
        "prompts": len(mcp._prompt_manager.list_prompts())
    })

@app.post("/api/chat")
async def proxy_chat(request: dict):
    """Proxy chat completions to OpenRouter (for users without API keys)."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return JSONResponse({"error": "Server configuration error"}, status_code=500)
    
    # Validate request
    if not request or "messages" not in request:
        return JSONResponse({"error": "Invalid request - messages required"}, status_code=400)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/baronsilver/symbols-mcp-server",
                },
                json={
                    "model": request.get("model", "openai/gpt-4.1-mini"),
                    "messages": request["messages"],
                    "max_tokens": request.get("max_tokens", 4000),
                    "temperature": request.get("temperature", 0.7),
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return JSONResponse(response.json())
    except httpx.HTTPError as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/")
async def root():
    """Root endpoint - redirect to health."""
    return JSONResponse({
        "name": "Symbols MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "sse": "/sse"
        }
    })

@app.get("/sse")
async def sse_endpoint():
    """SSE endpoint for MCP HTTP transport."""
    from sse_starlette.sse import EventSourceResponse
    
    async def event_generator():
        # Send server info
        yield {
            "event": "endpoint",
            "data": json.dumps({
                "jsonrpc": "2.0",
                "method": "endpoint",
                "params": {
                    "uri": "/message"
                }
            })
        }
    
    return EventSourceResponse(event_generator())

@app.post("/message")
async def message_endpoint(request: dict):
    """Message endpoint for MCP HTTP transport."""
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "server": {
                "name": "Symbols AI Assistant",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            }
        }
    })

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    """Run the Symbols MCP server."""
    # Check if running in Railway (HTTP) or local (stdio)
    transport = os.getenv("RAILWAY_ENVIRONMENT", "stdio")
    if transport == "production":
        # Railway deployment - run FastAPI app directly
        import uvicorn
        port = int(os.getenv("PORT", 8080))
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # Local development - use stdio transport
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
