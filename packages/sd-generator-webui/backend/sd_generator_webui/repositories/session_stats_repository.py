"""
Session Statistics Repository - Data access layer for session stats.

This module provides the repository interface and SQLite implementation
for persisting and retrieving session statistics.

Separation of concerns:
- Repository: Data access (SQL queries, schema, persistence)
- Service: Business logic (stats computation, orchestration)
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sd_generator_webui.config import METADATA_DIR
from sd_generator_webui.models_stats import SessionStats
from sd_generator_webui.repositories.base import BatchRepository


class SessionStatsRepository(BatchRepository[SessionStats]):
    """
    Abstract repository interface for session statistics.

    This interface defines the contract for storing and retrieving SessionStats.
    Implementations can use different storage backends (SQLite, PostgreSQL, etc.).
    """

    pass  # Interface inherits all methods from BatchRepository


class SQLiteSessionStatsRepository(SessionStatsRepository):
    """
    SQLite implementation of SessionStatsRepository.

    This implementation uses SQLite for storage and provides efficient
    batch operations for performance.
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

    def get(self, session_name: str) -> Optional[SessionStats]:
        """
        Get cached stats for a session.

        Args:
            session_name: Session folder name

        Returns:
            SessionStats if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM session_stats WHERE session_name = ?",
                (session_name,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_stats(row)

    def save(self, stats: SessionStats) -> None:
        """
        Save computed stats to database (upsert).

        Args:
            stats: SessionStats object to persist
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO session_stats (
                    session_name, sd_model, sampler_name, scheduler, cfg_scale, steps, width, height,
                    images_requested, images_actual, completion_percent,
                    placeholders_count, placeholders, variations_theoretical, variations_summary,
                    session_type, is_seed_sweep,
                    seed_min, seed_max, seed_mode,
                    session_created_at, stats_computed_at, completion_threshold
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats.session_name,
                stats.sd_model,
                stats.sampler_name,
                stats.scheduler,
                stats.cfg_scale,
                stats.steps,
                stats.width,
                stats.height,
                stats.images_requested,
                stats.images_actual,
                stats.completion_percent,
                stats.placeholders_count,
                json.dumps(stats.placeholders) if stats.placeholders else None,
                stats.variations_theoretical,
                json.dumps(stats.variations_summary) if stats.variations_summary else None,
                stats.session_type,
                int(stats.is_seed_sweep),
                stats.seed_min,
                stats.seed_max,
                stats.seed_mode,
                stats.session_created_at.isoformat() if stats.session_created_at else None,
                stats.stats_computed_at.isoformat() if stats.stats_computed_at else None,
                stats.completion_threshold
            ))
            conn.commit()

    def delete(self, session_name: str) -> bool:
        """
        Delete stats for a session.

        Args:
            session_name: Session folder name

        Returns:
            True if stats were deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM session_stats WHERE session_name = ?",
                (session_name,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_batch(self, session_names: List[str]) -> Dict[str, SessionStats]:
        """
        Get stats for multiple sessions in a single query (PERFORMANCE).

        This method is critical for performance when listing many sessions
        (e.g., 1000+ sessions). It replaces N individual queries with 1 batch query.

        Args:
            session_names: List of session names to fetch

        Returns:
            Dict mapping session_name to SessionStats (missing sessions not included)
        """
        if not session_names:
            return {}

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Build IN clause with placeholders
            placeholders = ",".join("?" * len(session_names))
            query = f"SELECT * FROM session_stats WHERE session_name IN ({placeholders})"

            cursor = conn.execute(query, session_names)
            rows = cursor.fetchall()

            return {row["session_name"]: self._row_to_stats(row) for row in rows}

    def list_all(self) -> List[SessionStats]:
        """
        List stats for all sessions.

        Returns:
            List of SessionStats objects, sorted by creation date descending
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM session_stats ORDER BY session_created_at DESC")
            rows = cursor.fetchall()

            return [self._row_to_stats(row) for row in rows]

    def _row_to_stats(self, row: sqlite3.Row) -> SessionStats:
        """
        Convert SQLite row to SessionStats object.

        Args:
            row: SQLite row with column names

        Returns:
            SessionStats object
        """
        placeholders = json.loads(row["placeholders"]) if row["placeholders"] else None
        variations_summary = json.loads(row["variations_summary"]) if row["variations_summary"] else None

        return SessionStats(
            session_name=row["session_name"],
            sd_model=row["sd_model"],
            sampler_name=row["sampler_name"],
            scheduler=row["scheduler"],
            cfg_scale=row["cfg_scale"],
            steps=row["steps"],
            width=row["width"],
            height=row["height"],
            images_requested=row["images_requested"],
            images_actual=row["images_actual"],
            completion_percent=row["completion_percent"],
            placeholders_count=row["placeholders_count"],
            placeholders=placeholders,
            variations_theoretical=row["variations_theoretical"],
            variations_summary=variations_summary,
            session_type=row["session_type"],
            is_seed_sweep=bool(row["is_seed_sweep"]),
            seed_min=row["seed_min"],
            seed_max=row["seed_max"],
            seed_mode=row["seed_mode"],
            session_created_at=datetime.fromisoformat(row["session_created_at"]) if row["session_created_at"] else None,
            stats_computed_at=datetime.fromisoformat(row["stats_computed_at"]) if row["stats_computed_at"] else None,
            completion_threshold=row["completion_threshold"]
        )
