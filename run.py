"""Application runner for BreathQuest.

Supports running directly with Waitress (production) or Flask dev server (development).
Loads .env explicitly so Waitress does not depend on Flask CLI's dotenv behavior.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded prior to configuring app
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

from app import create_app

app = create_app()

if __name__ == "__main__":
    env_name = os.getenv("FLASK_ENV", "development").lower()
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8080"))

    if env_name == "development":
        print(f"Starting BreathQuest development server on http://{host}:{port}")
        app.run(host=host, port=port, debug=True)
    else:
        from waitress import serve

        print(f"Serving BreathQuest with Waitress WSGI on http://{host}:{port}")
        serve(app, host=host, port=port)
