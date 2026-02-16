#!/bin/bash
# Wrapper script for running symbols-mcp server

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed"
    exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    pip install uv
fi

# Run the MCP server
exec python -m uv run symbols-mcp
