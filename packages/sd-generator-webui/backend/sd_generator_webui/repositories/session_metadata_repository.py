"""
Session Metadata Repository - Data access layer for session metadata.

This module provides the repository interface and SQLite implementation
for persisting and retrieving session metadata (ratings, tags, notes, flags).

Separation of concerns:
- Repository: Data access (SQL queries, schema, persistence)
- Service: Business logic (metadata validation, orchestration)
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from sd_generator_webui.config import METADATA_DIR
from sd_generator_webui.models import SessionMetadata, SessionMetadataUpdate, UserRating
from sd_generator_webui.repositories.base import Repository


class SessionMetadataRepository(Repository[SessionMetadata]):
    """
    Abstract repository interface for session metadata.

    This interface defines the contract for storing and retrieving SessionMetadata.
    Implementations can use different storage backends (SQLite, PostgreSQL, etc.).

    Note: This interface extends Repository with metadata-specific methods
    (upsert with partial updates, list_all).
    """

    def upsert(
        self,
        session_id: str,
        session_path: str,
        update: SessionMetadataUpdate
    ) -> SessionMetadata:
        """
        Create or update metadata for a session (partial update support).

        Args:
            session_id: Session folder name
            session_path: Full path to session folder
            update: Update data (only non-None fields are updated)

        Returns:
            Updated SessionMetadata
        """
        pass  # Abstract method

    def list_all(self) -> List[SessionMetadata]:
        """
        List all session metadata.

        Returns:
            List of SessionMetadata objects
        """
        pass  # Abstract method


class SQLiteSessionMetadataRepository(SessionMetadataRepository):
    """
    SQLite implementation of SessionMetadataRepository.

    This implementation uses SQLite for storage and provides efficient
    operations for user-generated metadata (ratings, tags, notes, flags).
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize repository.

        Note: Schema initialization is handled by the migration system.
        See migrations/v001_initial_schema.py

        Args:
            db_path: Path to SQLite database file. Defaults to METADATA_DIR/sessions.db
        """
        if db_path is None:
            db_path = METADATA_DIR / "sessions.db"

        self.db_path = db_path

    def get(self, session_id: str) -> Optional[SessionMetadata]:
        """
        Get metadata for a session.

        Args:
            session_id: Session folder name

        Returns:
            SessionMetadata if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM session_metadata WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_metadata(row)

    def save(self, metadata: SessionMetadata) -> None:
        """
        Save metadata (insert or update).

        Args:
            metadata: SessionMetadata object to persist
        """
        with sqlite3.connect(self.db_path) as conn:
            tags_json = json.dumps(metadata.tags) if metadata.tags else "[]"
            auto_metadata_json = json.dumps(metadata.auto_metadata) if metadata.auto_metadata else None

            conn.execute("""
                INSERT OR REPLACE INTO session_metadata
                (session_id, session_path, is_test, is_complete, is_favorite,
                 user_rating, user_note, tags, auto_metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.session_id,
                metadata.session_path,
                int(metadata.is_test),
                int(metadata.is_complete),
                int(metadata.is_favorite),
                metadata.user_rating.value if metadata.user_rating else None,
                metadata.user_note,
                tags_json,
                auto_metadata_json,
                metadata.created_at.isoformat(),
                metadata.updated_at.isoformat()
            ))
            conn.commit()

    def delete(self, session_id: str) -> bool:
        """
        Delete metadata for a session.

        Args:
            session_id: Session folder name

        Returns:
            True if metadata was deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM session_metadata WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_all(self) -> List[SessionMetadata]:
        """
        List all session metadata.

        Returns:
            List of SessionMetadata objects, sorted by updated_at descending
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM session_metadata ORDER BY updated_at DESC")
            rows = cursor.fetchall()

            return [self._row_to_metadata(row) for row in rows]

    def upsert(
        self,
        session_id: str,
        session_path: str,
        update: SessionMetadataUpdate
    ) -> SessionMetadata:
        """
        Create or update metadata for a session (partial update support).

        This is a higher-level method that handles the logic of:
        1. Check if metadata exists
        2. Create new metadata if not exists
        3. Update only provided fields if exists

        Args:
            session_id: Session folder name
            session_path: Full path to session folder
            update: Update data (only non-None fields are updated)

        Returns:
            Updated SessionMetadata
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check if exists
            existing = self.get(session_id)

            now = datetime.now().isoformat()

            if existing is None:
                # Create new
                tags_json = json.dumps(update.tags) if update.tags else "[]"

                conn.execute(
                    """
                    INSERT INTO session_metadata
                    (session_id, session_path, is_test, is_complete, is_favorite,
                     user_rating, user_note, tags, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        session_path,
                        int(update.is_test) if update.is_test is not None else 0,
                        int(update.is_complete) if update.is_complete is not None else 1,
                        int(update.is_favorite) if update.is_favorite is not None else 0,
                        update.user_rating.value if update.user_rating else None,
                        update.user_note,
                        tags_json,
                        now,
                        now
                    )
                )
            else:
                # Update existing (partial update - only provided fields)
                updates: List[str] = []
                params: List[Any] = []

                if update.is_test is not None:
                    updates.append("is_test = ?")
                    params.append(int(update.is_test))

                if update.is_complete is not None:
                    updates.append("is_complete = ?")
                    params.append(int(update.is_complete))

                if update.is_favorite is not None:
                    updates.append("is_favorite = ?")
                    params.append(int(update.is_favorite))

                if update.user_rating is not None:
                    updates.append("user_rating = ?")
                    params.append(update.user_rating.value)

                if update.user_note is not None:
                    updates.append("user_note = ?")
                    params.append(update.user_note)

                if update.tags is not None:
                    updates.append("tags = ?")
                    params.append(json.dumps(update.tags))

                # Always update timestamp
                updates.append("updated_at = ?")
                params.append(now)

                if updates:
                    params.append(session_id)
                    conn.execute(
                        f"UPDATE session_metadata SET {', '.join(updates)} WHERE session_id = ?",
                        params
                    )

            conn.commit()

        # Return updated metadata
        result = self.get(session_id)
        if result is None:
            raise RuntimeError(f"Failed to retrieve metadata after upsert: {session_id}")
        return result

    def _row_to_metadata(self, row: sqlite3.Row) -> SessionMetadata:
        """
        Convert SQLite row to SessionMetadata object.

        Args:
            row: SQLite row with column names

        Returns:
            SessionMetadata object
        """
        tags = json.loads(row["tags"]) if row["tags"] else []
        auto_metadata = json.loads(row["auto_metadata"]) if row["auto_metadata"] else None

        user_rating = None
        if row["user_rating"]:
            user_rating = UserRating(row["user_rating"])

        return SessionMetadata(
            session_id=row["session_id"],
            session_path=row["session_path"],
            is_test=bool(row["is_test"]),
            is_complete=bool(row["is_complete"]),
            is_favorite=bool(row["is_favorite"]),
            user_rating=user_rating,
            user_note=row["user_note"],
            tags=tags,
            auto_metadata=auto_metadata,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
