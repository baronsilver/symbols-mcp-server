"""
Proxy API for Symbols MCP Server
Handles OpenRouter API calls server-side so users don't need their own keys.
"""
import os
import httpx
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "Symbols MCP Proxy"})

@app.route("/api/chat", methods=["POST"])
def chat():
    """Proxy chat completions to OpenRouter."""
    if not OPENROUTER_API_KEY:
        return jsonify({"error": "Server configuration error"}), 500
    
    data = request.json
    
    # Validate request
    if not data or "messages" not in data:
        return jsonify({"error": "Invalid request - messages required"}), 400
    
    # Add rate limiting per IP (simple version)
    # In production, use Redis or similar for distributed rate limiting
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/baronsilver/symbols-mcp-server",
                },
                json={
                    "model": data.get("model", "openai/gpt-4.1-mini"),
                    "messages": data["messages"],
                    "max_tokens": data.get("max_tokens", 4000),
                    "temperature": data.get("temperature", 0.7),
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return jsonify(response.json())
    except httpx.HTTPError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
