"""
Session Metadata Service - SQLite backend for session ratings and metadata.

Handles:
- User ratings (like/dislike)
- Flags (is_test, is_complete, is_favorite)
- Tags
- User notes
- Auto-extracted metadata
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from sd_generator_webui.config import METADATA_DIR
from sd_generator_webui.models import SessionMetadata, SessionMetadataUpdate, UserRating


class SessionMetadataService:
    """Service for managing session metadata in SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the service and create database if needed.

        Args:
            db_path: Path to SQLite database file. Defaults to METADATA_DIR/sessions.db
        """
        if db_path is None:
            db_path = METADATA_DIR / "sessions.db"

        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Create database schema if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_metadata (
                    session_id TEXT PRIMARY KEY,
                    session_path TEXT NOT NULL,
                    is_test INTEGER DEFAULT 0,
                    is_complete INTEGER DEFAULT 1,
                    is_favorite INTEGER DEFAULT 0,
                    user_rating TEXT,
                    user_note TEXT,
                    tags TEXT,
                    auto_metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def get_metadata(self, session_id: str) -> Optional[SessionMetadata]:
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

    def upsert_metadata(
        self,
        session_id: str,
        session_path: str,
        update: SessionMetadataUpdate
    ) -> SessionMetadata:
        """
        Create or update metadata for a session.

        Args:
            session_id: Session folder name
            session_path: Full path to session folder
            update: Update data

        Returns:
            Updated SessionMetadata
        """
        with sqlite3.connect(self.db_path) as conn:
            # Check if exists
            existing = self.get_metadata(session_id)

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
                # Update existing
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
        result = self.get_metadata(session_id)
        if result is None:
            raise RuntimeError(f"Failed to retrieve metadata after upsert: {session_id}")
        return result

    def list_all_metadata(self) -> List[SessionMetadata]:
        """
        List all session metadata.

        Returns:
            List of SessionMetadata objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM session_metadata ORDER BY updated_at DESC")
            rows = cursor.fetchall()

            return [self._row_to_metadata(row) for row in rows]

    def delete_metadata(self, session_id: str) -> bool:
        """
        Delete metadata for a session.

        Args:
            session_id: Session folder name

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM session_metadata WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_metadata(self, row: sqlite3.Row) -> SessionMetadata:
        """Convert SQLite row to SessionMetadata model."""
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
