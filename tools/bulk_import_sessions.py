#!/usr/bin/env python3
"""
Bulk import and sync script for session statistics.

This script scans all session directories and imports/updates their stats in the database.

Usage:
    # Import all sessions
    python3 tools/bulk_import_sessions.py

    # Import only missing sessions (not in DB)
    python3 tools/bulk_import_sessions.py --missing-only

    # Import specific sessions
    python3 tools/bulk_import_sessions.py --sessions session1 session2

    # Dry run (show what would be imported)
    python3 tools/bulk_import_sessions.py --dry-run

    # Force reimport (even if already in DB)
    python3 tools/bulk_import_sessions.py --force
"""

import argparse
import sys
from pathlib import Path
from typing import List, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "sd-generator-webui" / "backend"))

from sd_generator_webui.config import IMAGES_DIR, METADATA_DIR
from sd_generator_webui.services.session_stats import SessionStatsService


def get_all_session_folders(sessions_root: Path) -> List[Path]:
    """
    Get all session directories from filesystem.

    Args:
        sessions_root: Root directory containing sessions

    Returns:
        List of session directory paths
    """
    if not sessions_root.exists():
        print(f"❌ Sessions root not found: {sessions_root}")
        return []

    sessions = []
    for item in sessions_root.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Valid session: has manifest.json or PNG files
            has_manifest = (item / "manifest.json").exists()
            has_images = any(item.glob("*.png"))

            if has_manifest or has_images:
                sessions.append(item)

    return sorted(sessions, key=lambda p: p.name)


def get_sessions_in_db(service: SessionStatsService) -> Set[str]:
    """
    Get set of session names already in database.

    Args:
        service: SessionStatsService instance

    Returns:
        Set of session names
    """
    import sqlite3

    with sqlite3.connect(service.db_path) as conn:
        cursor = conn.execute("SELECT session_name FROM session_stats")
        return {row[0] for row in cursor.fetchall()}


def import_session(service: SessionStatsService, session_path: Path, force: bool = False, dry_run: bool = False) -> bool:
    """
    Import a single session into the database.

    Args:
        service: SessionStatsService instance
        session_path: Path to session directory
        force: Force reimport even if exists
        dry_run: Don't actually import, just show what would happen

    Returns:
        True if imported successfully
    """
    session_name = session_path.name

    try:
        # Compute stats (pass Path, not str)
        stats = service.compute_stats(session_path)

        if dry_run:
            print(f"  [DRY RUN] Would import: {session_name}")
            print(f"    - Images: {stats.images_actual}/{stats.images_requested}")
            print(f"    - Completion: {stats.completion_percent:.1%}")
            print(f"    - Type: {stats.session_type}")
            if stats.sd_model:
                print(f"    - Model: {stats.sd_model}")
            return True

        # Save to database
        service.save_stats(stats)
        return True

    except FileNotFoundError as e:
        print(f"  ⚠️  Session not found: {session_name} ({e})")
        return False
    except Exception as e:
        print(f"  ❌ Error importing {session_name}: {e}")
        return False


def bulk_import(
    sessions_root: Path,
    missing_only: bool = False,
    force: bool = False,
    dry_run: bool = False,
    specific_sessions: List[str] = None
):
    """
    Bulk import sessions into database.

    Args:
        sessions_root: Root directory containing sessions
        missing_only: Only import sessions not in DB
        force: Force reimport even if exists
        dry_run: Don't actually import
        specific_sessions: List of specific session names to import
    """
    print(f"🔍 Scanning sessions in: {sessions_root}")
    print(f"📊 Database: {METADATA_DIR / 'sessions.db'}")
    print()

    # Initialize service
    service = SessionStatsService(sessions_root=sessions_root)

    # Get all sessions from filesystem
    all_sessions = get_all_session_folders(sessions_root)
    print(f"Found {len(all_sessions)} sessions in filesystem")

    # Filter by specific sessions if requested
    if specific_sessions:
        all_sessions = [s for s in all_sessions if s.name in specific_sessions]
        print(f"Filtered to {len(all_sessions)} requested sessions")

    # Get sessions already in DB
    sessions_in_db = get_sessions_in_db(service)
    print(f"Found {len(sessions_in_db)} sessions in database")
    print()

    # Determine what to import
    to_import = []
    for session_path in all_sessions:
        session_name = session_path.name
        in_db = session_name in sessions_in_db

        if missing_only and in_db:
            continue  # Skip already imported
        elif not force and in_db:
            print(f"⏭️  Skipping {session_name} (already in DB, use --force to reimport)")
            continue

        to_import.append(session_path)

    if not to_import:
        print("✅ Nothing to import!")
        return

    print(f"📦 Importing {len(to_import)} sessions...")
    if dry_run:
        print("🧪 DRY RUN MODE - No actual changes will be made")
    print()

    # Import sessions
    success_count = 0
    error_count = 0

    for i, session_path in enumerate(to_import, 1):
        session_name = session_path.name
        status = "UPDATE" if session_name in sessions_in_db else "NEW"

        print(f"[{i}/{len(to_import)}] {status} {session_name}")

        if import_session(service, session_path, force=force, dry_run=dry_run):
            success_count += 1
        else:
            error_count += 1

    # Summary
    print()
    print("=" * 60)
    if dry_run:
        print(f"✅ DRY RUN: Would import {success_count} sessions")
    else:
        print(f"✅ Successfully imported: {success_count} sessions")
    if error_count > 0:
        print(f"❌ Errors: {error_count} sessions")
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bulk import session statistics into database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--missing-only",
        action="store_true",
        help="Only import sessions not already in database"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reimport even if session exists in database"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without making changes"
    )

    parser.add_argument(
        "--sessions",
        nargs="+",
        help="Import only specific sessions (by name)"
    )

    parser.add_argument(
        "--sessions-root",
        type=Path,
        default=IMAGES_DIR,
        help=f"Sessions root directory (default: {IMAGES_DIR})"
    )

    args = parser.parse_args()

    # Run bulk import
    bulk_import(
        sessions_root=args.sessions_root,
        missing_only=args.missing_only,
        force=args.force,
        dry_run=args.dry_run,
        specific_sessions=args.sessions
    )


if __name__ == "__main__":
    main()
