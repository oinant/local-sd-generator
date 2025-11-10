"""
Tests for MigrationRunner.

Tests idempotent migrations, version tracking, and error handling.
"""

import sqlite3
from pathlib import Path

import pytest

from sd_generator_webui.migrations.base import Migration
from sd_generator_webui.migrations.runner import MigrationRunner


class TestMigration1(Migration):
    """Test migration v1."""

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return "Create test_table"

    def up(self, conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")


class TestMigration2(Migration):
    """Test migration v2."""

    @property
    def version(self) -> int:
        return 2

    @property
    def description(self) -> str:
        return "Add column to test_table"

    def up(self, conn: sqlite3.Connection) -> None:
        # Check if column exists before adding (idempotent)
        cursor = conn.execute("PRAGMA table_info(test_table)")
        columns = [row[1] for row in cursor.fetchall()]
        if "email" not in columns:
            conn.execute("ALTER TABLE test_table ADD COLUMN email TEXT")


class FailingMigration(Migration):
    """Migration that fails (for testing error handling)."""

    @property
    def version(self) -> int:
        return 99

    @property
    def description(self) -> str:
        return "Failing migration"

    def up(self, conn: sqlite3.Connection) -> None:
        raise RuntimeError("Migration intentionally failed")


class TestMigrationRunner:
    """Test suite for MigrationRunner."""

    def test_runner_creates_version_table(self, temp_db: Path):
        """Test runner creates schema_version table."""
        runner = MigrationRunner(db_path=temp_db)

        # Check table exists
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            assert cursor.fetchone() is not None

    def test_get_current_version_empty(self, temp_db: Path):
        """Test get_current_version returns 0 when no migrations applied."""
        runner = MigrationRunner(db_path=temp_db)
        assert runner.get_current_version() == 0

    def test_run_single_migration(self, temp_db: Path):
        """Test running a single migration."""
        runner = MigrationRunner(db_path=temp_db)
        migration = TestMigration1()

        applied = runner.run_migration(migration)

        assert applied is True
        assert runner.get_current_version() == 1
        assert runner.is_migration_applied(1) is True

        # Check table was created
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
            )
            assert cursor.fetchone() is not None

    def test_run_migration_idempotent(self, temp_db: Path):
        """Test running same migration twice is idempotent."""
        runner = MigrationRunner(db_path=temp_db)
        migration = TestMigration1()

        # Run first time
        applied1 = runner.run_migration(migration)
        assert applied1 is True

        # Run second time (should skip)
        applied2 = runner.run_migration(migration)
        assert applied2 is False

        assert runner.get_current_version() == 1

    def test_run_migrations_in_order(self, temp_db: Path):
        """Test running multiple migrations in order."""
        runner = MigrationRunner(db_path=temp_db)
        migrations = [TestMigration1(), TestMigration2()]

        applied_count = runner.run_migrations(migrations)

        assert applied_count == 2
        assert runner.get_current_version() == 2
        assert runner.is_migration_applied(1) is True
        assert runner.is_migration_applied(2) is True

        # Check column was added
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("PRAGMA table_info(test_table)")
            columns = [row[1] for row in cursor.fetchall()]
            assert "id" in columns
            assert "name" in columns
            assert "email" in columns

    def test_run_migrations_skips_applied(self, temp_db: Path):
        """Test running migrations skips already applied ones."""
        runner = MigrationRunner(db_path=temp_db)

        # Apply first migration
        runner.run_migration(TestMigration1())

        # Run both migrations (should skip first)
        migrations = [TestMigration1(), TestMigration2()]
        applied_count = runner.run_migrations(migrations)

        assert applied_count == 1  # Only second migration applied
        assert runner.get_current_version() == 2

    def test_run_migrations_sorts_by_version(self, temp_db: Path):
        """Test run_migrations sorts migrations by version."""
        runner = MigrationRunner(db_path=temp_db)

        # Pass migrations in wrong order
        migrations = [TestMigration2(), TestMigration1()]

        applied_count = runner.run_migrations(migrations)

        assert applied_count == 2
        assert runner.get_current_version() == 2

        # Verify both applied
        history = runner.get_migration_history()
        assert len(history) == 2
        assert history[0][0] == 1  # First applied
        assert history[1][0] == 2  # Second applied

    def test_migration_failure_rolls_back(self, temp_db: Path):
        """Test migration failure triggers rollback."""
        runner = MigrationRunner(db_path=temp_db)
        failing_migration = FailingMigration()

        with pytest.raises(RuntimeError, match="Migration v99 failed"):
            runner.run_migration(failing_migration)

        # Verify not recorded in schema_version
        assert runner.is_migration_applied(99) is False
        assert runner.get_current_version() == 0

    def test_get_migration_history(self, temp_db: Path):
        """Test get_migration_history returns correct data."""
        runner = MigrationRunner(db_path=temp_db)
        migrations = [TestMigration1(), TestMigration2()]

        runner.run_migrations(migrations)

        history = runner.get_migration_history()

        assert len(history) == 2
        assert history[0][0] == 1
        assert history[0][1] == "Create test_table"
        assert history[1][0] == 2
        assert history[1][1] == "Add column to test_table"

    def test_migration_records_timestamp(self, temp_db: Path):
        """Test migrations record applied_at timestamp."""
        runner = MigrationRunner(db_path=temp_db)
        migration = TestMigration1()

        runner.run_migration(migration)

        history = runner.get_migration_history()
        assert len(history) == 1
        assert history[0][2] is not None  # applied_at timestamp exists
