"""Script to render and capture responsive screenshots using headless Google Chrome.

Inspects target viewports: 360, 390, 768, 1024, and 1440 CSS pixels.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from threading import Thread

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from waitress import create_server
from app import create_app

ARTIFACT_DIR = Path("/Users/laoongnam-air/.gemini/antigravity/brain/cb9d346e-3c83-43f9-8428-98bd6d82957e/screenshots")
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

VIEWPORTS = [
    (360, 800, "360px_compact_mobile"),
    (390, 844, "390px_standard_mobile"),
    (768, 1024, "768px_tablet_portrait"),
    (1024, 768, "1024px_desktop"),
    (1440, 900, "1440px_large_desktop"),
]

PAGES = [
    ("/", "home"),
    ("/ward", "ward"),
    ("/missions/clear-the-airway", "room_501_gameplay"),
    ("/missions/support-the-breath", "room_502_gameplay"),
    ("/missions/open-the-airway", "room_503_gameplay"),
    ("/missions/respiratory-rescue?demo=1", "room_504_gameplay"),
]


def run_waitress_server(server):
    server.run()


def main():
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Start application on loopback
    app = create_app()
    server = create_server(app, host="127.0.0.1", port=8085)
    thread = Thread(target=run_waitress_server, args=(server,), daemon=True)
    thread.start()
    time.sleep(1)

    print("Server running on http://127.0.0.1:8085")

    captured_files = []

    # 2. Capture screenshots for each page and viewport
    for path, page_name in PAGES:
        url = f"http://127.0.0.1:8085{path}"
        for width, height, vp_name in VIEWPORTS:
            output_file = ARTIFACT_DIR / f"{page_name}_{vp_name}.png"
            cmd = [
                CHROME_BIN,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-proxy-server",
                f"--user-data-dir=/Users/laoongnam-air/Developer/GitHub/NLabS/scratch/chrome_user_data",
                f"--window-size={width},{height}",
                f"--screenshot={output_file}",
                url,
            ]
            try:
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
                if output_file.exists():
                    print(f"Captured: {output_file.name} ({output_file.stat().st_size} bytes)")
                    captured_files.append(str(output_file))
                else:
                    print(f"Failed to capture {output_file.name}: {res.stderr}")
            except subprocess.TimeoutExpired:
                print(f"Timeout capturing {output_file.name}")

    server.close()
    print(f"\nDone! Captured {len(captured_files)} screenshots in {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
