"""
WSGI entry point for Railway deployment.
Nixpacks will automatically detect and run this file.
"""
from symbols_mcp.server import flask_app

app = flask_app

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
