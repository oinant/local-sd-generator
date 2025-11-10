"""
Pytest fixtures for WebUI backend tests.

Provides common fixtures for testing repositories, migrations, and services.
"""

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest

from sd_generator_webui.repositories.session_stats_repository import SQLiteSessionStatsRepository
from sd_generator_webui.repositories.session_metadata_repository import SQLiteSessionMetadataRepository
from sd_generator_webui.models_stats import SessionStats
from sd_generator_webui.models import SessionMetadata, UserRating


@pytest.fixture
def temp_db() -> Generator[Path, None, None]:
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def stats_repository(temp_db: Path) -> SQLiteSessionStatsRepository:
    """Create a SessionStatsRepository with temporary database."""
    # Initialize schema manually (since we're not using migration runner in tests)
    with sqlite3.connect(temp_db) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_stats (
                session_name TEXT PRIMARY KEY,
                sd_model TEXT,
                sampler_name TEXT,
                scheduler TEXT,
                cfg_scale REAL,
                steps INTEGER,
                width INTEGER,
                height INTEGER,
                images_requested INTEGER DEFAULT 0,
                images_actual INTEGER DEFAULT 0,
                completion_percent REAL DEFAULT 0.0,
                placeholders_count INTEGER DEFAULT 0,
                placeholders TEXT,
                variations_theoretical INTEGER DEFAULT 0,
                variations_summary TEXT,
                session_type TEXT DEFAULT 'normal',
                is_seed_sweep INTEGER DEFAULT 0,
                seed_min INTEGER,
                seed_max INTEGER,
                seed_mode TEXT,
                session_created_at TEXT,
                stats_computed_at TEXT NOT NULL,
                completion_threshold REAL DEFAULT 0.95
            )
        """)
        conn.commit()

    return SQLiteSessionStatsRepository(db_path=temp_db)


@pytest.fixture
def metadata_repository(temp_db: Path) -> SQLiteSessionMetadataRepository:
    """Create a SessionMetadataRepository with temporary database."""
    # Initialize schema manually
    with sqlite3.connect(temp_db) as conn:
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

    return SQLiteSessionMetadataRepository(db_path=temp_db)


@pytest.fixture
def sample_stats() -> SessionStats:
    """Create a sample SessionStats object for testing."""
    return SessionStats(
        session_name="20251110_120000-test_session",
        sd_model="sd_xl_base_1.0.safetensors",
        sampler_name="DPM++ 2M",
        scheduler="Karras",
        cfg_scale=7.0,
        steps=20,
        width=1024,
        height=1024,
        images_requested=100,
        images_actual=95,
        completion_percent=0.95,
        placeholders_count=2,
        placeholders=["FacialExpression", "Angle"],
        variations_theoretical=100,
        variations_summary={"FacialExpression": 10, "Angle": 10},
        session_type="normal",
        is_seed_sweep=False,
        seed_min=42,
        seed_max=141,
        seed_mode="progressive",
        session_created_at=datetime(2025, 11, 10, 12, 0, 0),
        stats_computed_at=datetime.now(),
        completion_threshold=0.95
    )


@pytest.fixture
def sample_metadata() -> SessionMetadata:
    """Create a sample SessionMetadata object for testing."""
    return SessionMetadata(
        session_id="20251110_120000-test_session",
        session_path="/path/to/session",
        is_test=False,
        is_complete=True,
        is_favorite=False,
        user_rating=UserRating.LIKE,
        user_note="Test note",
        tags=["portrait", "cyberpunk"],
        auto_metadata=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
