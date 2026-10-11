#!/usr/bin/env python3
"""BreathQuest Image Import & Sync Utility.

Syncs and optimizes images placed in `import_images/` into `app/static/images/`.
Supports .jpg, .jpeg, .png, .webp, and .svg.
Uses macOS sips (if available) to automatically optimize large camera photos for web delivery.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMPORT_DIR = BASE_DIR / "import_images"
STATIC_IMAGES_DIR = BASE_DIR / "app" / "static" / "images"

CATEGORIES = ["patients", "equipment", "badges", "procedures", "scenarios", "branding"]
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg"}


def optimize_raster_image(file_path: Path, max_dim: int = 1200) -> None:
    """Optimize raster image using macOS sips if available."""
    if file_path.suffix.lower() in [".jpg", ".jpeg", ".png"] and shutil.which("sips"):
        try:
            subprocess.run(
                ["sips", "-Z", str(max_dim), str(file_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass


def main():
    print("=" * 60)
    print("  BreathQuest Image Import & Synchronization Utility")
    print("=" * 60)

    if not IMPORT_DIR.exists():
        print(f"Error: {IMPORT_DIR} not found.")
        return

    synced_count = 0

    for category in CATEGORIES:
        src_cat_dir = IMPORT_DIR / category
        dst_cat_dir = STATIC_IMAGES_DIR / category
        dst_cat_dir.mkdir(parents=True, exist_ok=True)

        if not src_cat_dir.exists():
            continue

        items = list(src_cat_dir.glob("*"))
        for item in items:
            if item.is_file() and item.suffix.lower() in VALID_EXTENSIONS:
                target_file = dst_cat_dir / item.name
                shutil.copy2(item, target_file)
                optimize_raster_image(target_file, max_dim=1200)

                size_kb = target_file.stat().st_size / 1024
                print(f"  [OK] {category}/{item.name} -> {target_file.name} ({size_kb:.1f} KB)")
                synced_count += 1

    print("-" * 60)
    if synced_count > 0:
        print(f"SUCCESS: Synchronized and optimized {synced_count} image(s)!")
    else:
        print("Note: No new image files found in import_images/ subdirectories.")
        print("Please place your images into:")
        for cat in CATEGORIES:
            print(f"  - import_images/{cat}/")
        print("\nThen run this script again: python sync_images.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
