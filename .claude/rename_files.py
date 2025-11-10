#!/usr/bin/env python3
"""
Script to rename .claude/*.md files with timestamp prefix based on filesystem mtime.
Format: YYYYMMDD_HHMMSS-filename.md

Usage:
    python3 .claude/rename_files.py
"""

import os
from pathlib import Path
from datetime import datetime

def main():
    claude_dir = Path(__file__).parent

    print(f"Working directory: {claude_dir}\n")
    print("Files to rename:")

    renames = []

    # Loop through all .md files
    for md_file in sorted(claude_dir.glob("*.md")):
        filename = md_file.name

        # Skip if already has timestamp prefix
        if filename[0:8].isdigit() and filename[8] == '_' and filename[15] == '-':
            print(f"  ⊘ SKIP: {filename} (already has timestamp prefix)")
            continue

        # Get file modification time
        mtime = md_file.stat().st_mtime
        dt = datetime.fromtimestamp(mtime)
        timestamp = dt.strftime("%Y%m%d_%H%M%S")

        new_name = f"{timestamp}-{filename}"
        new_path = claude_dir / new_name

        if new_path.exists():
            print(f"  ⚠ SKIP: {filename} (target already exists)")
            continue

        renames.append((md_file, new_path, filename, new_name))
        print(f"  ✓ {filename}")
        print(f"      → {new_name}")

    if not renames:
        print("\nNo files to rename.")
        return

    print(f"\n❓ Proceed with {len(renames)} renames? [y/N]: ", end="")
    response = input().strip().lower()

    if response != 'y':
        print("Aborted.")
        return

    print("\nRenaming files...")
    success = 0
    for old_path, new_path, old_name, new_name in renames:
        try:
            old_path.rename(new_path)
            print(f"  ✓ {new_name}")
            success += 1
        except Exception as e:
            print(f"  ✗ Error renaming {old_name}: {e}")

    print(f"\n✅ Done! {success}/{len(renames)} files renamed.")

if __name__ == "__main__":
    main()
