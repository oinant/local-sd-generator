"""
Poetry build script for sd-generator-webui.

Builds the frontend (npm run build) before packaging the Python wheel.

IMPORTANT: For editable installs (pip install -e .), set SKIP_FRONTEND_BUILD=1
to skip the frontend build (dev mode with Vite dev server).
"""

import os
import subprocess
import sys
from pathlib import Path


def build():
    """Build frontend before packaging."""
    # Check if we should skip the build (editable/dev mode)
    skip_build = os.environ.get("SKIP_FRONTEND_BUILD", "0") == "1"

    if skip_build:
        print("=" * 60)
        print("SKIP_FRONTEND_BUILD=1 detected - Skipping frontend build")
        print("Mode: DEV (use Vite dev server)")
        print("=" * 60)
        return

    print("=" * 60)
    print("Building frontend for production...")
    print("=" * 60)

    # Get paths
    package_root = Path(__file__).parent
    frontend_dir = package_root / "front"

    if not frontend_dir.exists():
        print(f"ERROR: Frontend directory not found: {frontend_dir}")
        sys.exit(1)

    # Check if package.json exists
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print(f"ERROR: package.json not found: {package_json}")
        sys.exit(1)

    # Run npm install (ensure dependencies are installed)
    print("\n→ Installing npm dependencies...")
    result = subprocess.run(
        ["npm", "install"],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("ERROR: npm install failed")
        print(result.stderr)
        sys.exit(1)

    print("✓ npm dependencies installed")

    # Run npm run build
    print("\n→ Building frontend (npm run build)...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("ERROR: npm run build failed")
        print(result.stderr)
        sys.exit(1)

    # Check if dist was created
    dist_dir = frontend_dir / "dist"
    if not dist_dir.exists():
        print(f"ERROR: Build output not found: {dist_dir}")
        sys.exit(1)

    print(f"✓ Frontend built successfully: {dist_dir}")

    # List built files
    files = list(dist_dir.rglob("*"))
    print(f"\n→ Built {len(files)} files")

    print("=" * 60)
    print("Frontend build complete!")
    print("=" * 60)


if __name__ == "__main__":
    build()
