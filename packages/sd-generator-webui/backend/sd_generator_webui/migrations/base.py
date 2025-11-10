"""
Base migration interface.

Each migration is a Python class that implements the Migration interface.
Migrations are versioned and executed in order.
"""

import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path


class Migration(ABC):
    """
    Abstract base class for database migrations.

    Each migration must:
    - Have a unique version number
    - Implement up() to apply changes
    - Implement down() to revert changes (optional)
    - Be idempotent (safe to run multiple times)
    """

    @property
    @abstractmethod
    def version(self) -> int:
        """
        Migration version number.

        Versions must be unique and sequential (e.g., 1, 2, 3...).
        Runner executes migrations in ascending order.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of this migration.

        Examples:
        - "Initial schema"
        - "Add user_rating column to session_metadata"
        - "Create indexes for performance"
        """
        pass

    @abstractmethod
    def up(self, conn: sqlite3.Connection) -> None:
        """
        Apply migration (upgrade schema).

        This method MUST be idempotent - it should be safe to run multiple times.
        Use CREATE TABLE IF NOT EXISTS, CREATE INDEX IF NOT EXISTS, etc.

        Args:
            conn: SQLite connection (already in transaction)
        """
        pass

    def down(self, conn: sqlite3.Connection) -> None:
        """
        Revert migration (downgrade schema) - OPTIONAL.

        Only implement if rollback is needed. Most migrations don't need this.

        Args:
            conn: SQLite connection (already in transaction)
        """
        pass
