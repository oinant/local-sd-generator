"""
Migration runner - Executes migrations in order and tracks applied migrations.

The runner maintains a schema_version table to track which migrations
have been applied. It ensures migrations run exactly once and in order.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sd_generator_webui.config import METADATA_DIR
from sd_generator_webui.migrations.base import Migration


class MigrationRunner:
    """
    Idempotent migration runner.

    Features:
    - Tracks applied migrations in schema_version table
    - Runs migrations in order by version number
    - Idempotent: Safe to run multiple times
    - Transactional: Each migration runs in its own transaction
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize migration runner.

        Args:
            db_path: Path to SQLite database. Defaults to METADATA_DIR/sessions.db
        """
        if db_path is None:
            db_path = METADATA_DIR / "sessions.db"

        self.db_path = db_path
        self._ensure_version_table()

    def _ensure_version_table(self) -> None:
        """Create schema_version table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def get_current_version(self) -> int:
        """
        Get current schema version.

        Returns:
            Current version number (0 if no migrations applied)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()

            if result is None or result[0] is None:
                return 0

            return result[0]

    def is_migration_applied(self, version: int) -> bool:
        """
        Check if a migration has been applied.

        Args:
            version: Migration version number

        Returns:
            True if migration has been applied
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM schema_version WHERE version = ?",
                (version,)
            )
            count = cursor.fetchone()[0]
            return count > 0

    def run_migration(self, migration: Migration) -> bool:
        """
        Run a single migration if not already applied.

        Args:
            migration: Migration to run

        Returns:
            True if migration was applied, False if already applied
        """
        # Check if already applied
        if self.is_migration_applied(migration.version):
            return False

        # Apply migration in transaction
        with sqlite3.connect(self.db_path) as conn:
            try:
                # Run migration
                migration.up(conn)

                # Record in schema_version
                conn.execute(
                    """
                    INSERT INTO schema_version (version, description, applied_at)
                    VALUES (?, ?, ?)
                    """,
                    (migration.version, migration.description, datetime.now().isoformat())
                )

                conn.commit()
                return True

            except Exception as e:
                conn.rollback()
                raise RuntimeError(
                    f"Migration v{migration.version} failed: {migration.description}"
                ) from e

    def run_migrations(self, migrations: List[Migration]) -> int:
        """
        Run all pending migrations in order.

        Args:
            migrations: List of migrations to apply

        Returns:
            Number of migrations applied
        """
        # Sort migrations by version
        sorted_migrations = sorted(migrations, key=lambda m: m.version)

        applied_count = 0

        for migration in sorted_migrations:
            if self.run_migration(migration):
                applied_count += 1
                print(f"✓ Applied migration v{migration.version}: {migration.description}")
            else:
                print(f"- Skipped migration v{migration.version}: {migration.description} (already applied)")

        return applied_count

    def get_migration_history(self) -> List[tuple]:
        """
        Get migration history.

        Returns:
            List of (version, description, applied_at) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT version, description, applied_at FROM schema_version ORDER BY version"
            )
            return cursor.fetchall()
