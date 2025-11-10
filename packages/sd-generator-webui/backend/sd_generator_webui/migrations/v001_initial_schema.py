"""
Migration v001: Initial schema.

Creates:
- session_stats table (for computed statistics)
- session_metadata table (for user-generated metadata)
- Indexes for performance
"""

import sqlite3

from sd_generator_webui.migrations.base import Migration


class InitialSchemaMigration(Migration):
    """Initial schema migration - creates all tables and indexes."""

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return "Initial schema (session_stats, session_metadata, indexes)"

    def up(self, conn: sqlite3.Connection) -> None:
        """Create initial schema."""
        # ==================== session_stats table ====================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_stats (
                session_name TEXT PRIMARY KEY,

                -- Generation info
                sd_model TEXT,
                sampler_name TEXT,
                scheduler TEXT,
                cfg_scale REAL,
                steps INTEGER,
                width INTEGER,
                height INTEGER,

                -- Images
                images_requested INTEGER DEFAULT 0,
                images_actual INTEGER DEFAULT 0,
                completion_percent REAL DEFAULT 0.0,

                -- Placeholders & Variations
                placeholders_count INTEGER DEFAULT 0,
                placeholders TEXT,  -- JSON array
                variations_theoretical INTEGER DEFAULT 0,
                variations_summary TEXT,  -- JSON object {placeholder: count}

                -- Session type
                session_type TEXT DEFAULT 'normal',
                is_seed_sweep INTEGER DEFAULT 0,

                -- Seed info
                seed_min INTEGER,
                seed_max INTEGER,
                seed_mode TEXT,

                -- Timestamps
                session_created_at TEXT,
                stats_computed_at TEXT NOT NULL,

                -- Config
                completion_threshold REAL DEFAULT 0.95
            )
        """)

        # session_stats indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_stats_model
            ON session_stats(sd_model)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_stats_seed_sweep
            ON session_stats(is_seed_sweep)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_stats_created_at
            ON session_stats(session_created_at DESC)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_stats_completion
            ON session_stats(completion_percent)
        """)

        # ==================== session_metadata table ====================
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

    def down(self, conn: sqlite3.Connection) -> None:
        """Drop all tables (not recommended in production)."""
        conn.execute("DROP TABLE IF EXISTS session_stats")
        conn.execute("DROP TABLE IF EXISTS session_metadata")
