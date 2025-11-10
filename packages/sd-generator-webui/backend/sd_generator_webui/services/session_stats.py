"""
Session Statistics Service - Calculate and cache session stats.

Handles:
- Stats calculation from manifest.json + filesystem
- Session type detection (normal vs seed-sweep)
- Completion percentage calculation
- Caching stats in SQLite for performance
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sd_generator_webui.config import METADATA_DIR


@dataclass
class SessionStats:
    """Calculated statistics for a session."""

    # Identity
    session_name: str

    # Generation info
    sd_model: Optional[str] = None
    sampler_name: Optional[str] = None
    scheduler: Optional[str] = None
    cfg_scale: Optional[float] = None
    steps: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None

    # Images
    images_requested: int = 0
    images_actual: int = 0
    completion_percent: float = 0.0

    # Placeholders & Variations
    placeholders_count: int = 0
    placeholders: Optional[List[str]] = None
    variations_theoretical: int = 0
    variations_summary: Optional[Dict[str, int]] = None  # {placeholder: count}

    # Session type
    session_type: str = "normal"  # "normal" | "seed-sweep"
    is_seed_sweep: bool = False

    # Seed info
    seed_min: Optional[int] = None
    seed_max: Optional[int] = None
    seed_mode: Optional[str] = None  # "fixed" | "progressive" | "random"

    # Timestamps
    session_created_at: Optional[datetime] = None
    stats_computed_at: Optional[datetime] = None

    # Completion threshold (configurable)
    completion_threshold: float = 0.95


class SessionStatsService:
    """Service for computing and caching session statistics."""

    def __init__(self, db_path: Optional[Path] = None, sessions_root: Optional[Path] = None):
        """
        Initialize the service.

        Args:
            db_path: Path to SQLite database file. Defaults to METADATA_DIR/sessions.db
            sessions_root: Root directory containing session folders
        """
        if db_path is None:
            db_path = METADATA_DIR / "sessions.db"

        self.db_path = db_path
        self.sessions_root = sessions_root
        self._init_database()

    def _init_database(self) -> None:
        """Create session_stats table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
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

            # Create indexes for future features
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

            conn.commit()

    def compute_stats(self, session_path: Path) -> SessionStats:
        """
        Compute statistics for a session from manifest.json + filesystem.

        Args:
            session_path: Path to session folder

        Returns:
            SessionStats object with all computed fields
        """
        session_name = session_path.name
        manifest_path = session_path / "manifest.json"

        # Initialize stats
        stats = SessionStats(session_name=session_name)

        # Load manifest
        if not manifest_path.exists():
            # No manifest - count images only
            stats.images_actual = len(list(session_path.glob("*.png")))
            stats.session_created_at = datetime.fromtimestamp(session_path.stat().st_ctime)
            stats.stats_computed_at = datetime.now()
            return stats

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Extract generation info from nested structure
        snapshot = manifest.get("snapshot", {})
        runtime_info = snapshot.get("runtime_info", {})
        api_params = snapshot.get("api_params", {})

        # SD model from runtime_info
        stats.sd_model = runtime_info.get("sd_model_checkpoint")

        # API params
        stats.sampler_name = api_params.get("sampler")
        stats.scheduler = api_params.get("scheduler")
        stats.cfg_scale = api_params.get("cfg_scale")
        stats.steps = api_params.get("steps")
        stats.width = api_params.get("width")
        stats.height = api_params.get("height")

        # Images count
        images = manifest.get("images", [])
        generation_params = snapshot.get("generation_params", {})

        # Requested images from generation_params (more reliable than len(images))
        stats.images_requested = generation_params.get("num_images", len(images))
        stats.images_actual = len(list(session_path.glob("*.png")))

        # Completion percentage
        if stats.images_requested > 0:
            stats.completion_percent = stats.images_actual / stats.images_requested

        # Placeholders & Variations (from snapshot.variations)
        variations = snapshot.get("variations", {})

        if variations:
            stats.placeholders = list(variations.keys())
            stats.placeholders_count = len(stats.placeholders)

            # Variations summary: {placeholder: count}
            # New format has 'count' key in each variation
            stats.variations_summary = {
                ph: var_data.get("count", len(var_data.get("used", [])))
                for ph, var_data in variations.items()
            }

            # Theoretical max combinations
            counts = list(stats.variations_summary.values())
            stats.variations_theoretical = 1
            for count in counts:
                stats.variations_theoretical *= count

            # Cap to SQLite INTEGER max (2^63 - 1) to avoid overflow
            MAX_SQLITE_INT = 9223372036854775807
            if stats.variations_theoretical > MAX_SQLITE_INT:
                stats.variations_theoretical = MAX_SQLITE_INT

        # Detect session type (seed-sweep)
        stats.session_type, stats.is_seed_sweep = self._detect_session_type(manifest)

        # Seed info
        if images:
            seeds = [img.get("seed") for img in images if img.get("seed") is not None]
            if seeds:
                stats.seed_min = min(seeds)
                stats.seed_max = max(seeds)
                stats.seed_mode = self._detect_seed_mode(seeds)

        # Timestamps
        stats.session_created_at = datetime.fromtimestamp(session_path.stat().st_ctime)
        stats.stats_computed_at = datetime.now()

        return stats

    def _detect_session_type(self, manifest: Dict[str, Any]) -> tuple[str, bool]:
        """
        Detect if session is seed-sweep or normal.

        Args:
            manifest: Parsed manifest.json

        Returns:
            Tuple of (session_type, is_seed_sweep)
        """
        # Method 1: Explicit flag in manifest
        if manifest.get("generation_mode") == "seed-sweep":
            return ("seed-sweep", True)

        # Method 2: Heuristic - progressive seeds with identical prompts
        images = manifest.get("images", [])
        if len(images) < 2:
            return ("normal", False)

        # Check if seeds are progressive
        seeds = [img.get("seed") for img in images if img.get("seed") is not None]
        if not seeds or len(seeds) < 2:
            return ("normal", False)

        # Progressive = seed, seed+1, seed+2, ...
        diffs = [seeds[i+1] - seeds[i] for i in range(len(seeds) - 1)]
        is_progressive = all(d == 1 for d in diffs)

        if not is_progressive:
            return ("normal", False)

        # Check if all prompts are identical (only seed varies)
        prompts = [img.get("prompt") for img in images]
        unique_prompts = set(prompts)

        if len(unique_prompts) == 1:
            return ("seed-sweep", True)

        return ("normal", False)

    def _detect_seed_mode(self, seeds: List[int]) -> str:
        """
        Detect seed mode from seeds.

        Args:
            seeds: List of seeds

        Returns:
            "fixed" | "progressive" | "random"
        """
        if not seeds:
            return "random"

        unique_seeds = set(seeds)

        # Fixed: all seeds are identical
        if len(unique_seeds) == 1:
            return "fixed"

        # Progressive: seeds are sequential (seed, seed+1, seed+2, ...)
        if len(seeds) > 1:
            diffs = [seeds[i+1] - seeds[i] for i in range(len(seeds) - 1)]
            if all(d == 1 for d in diffs):
                return "progressive"

        return "random"

    def save_stats(self, stats: SessionStats) -> None:
        """
        Save computed stats to database (upsert).

        Args:
            stats: SessionStats object
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

    def get_stats(self, session_name: str) -> Optional[SessionStats]:
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

    def list_all_stats(self) -> List[SessionStats]:
        """
        List stats for all sessions.

        Returns:
            List of SessionStats objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM session_stats ORDER BY session_created_at DESC")
            rows = cursor.fetchall()

            return [self._row_to_stats(row) for row in rows]

    def get_stats_batch(self, session_names: List[str]) -> Dict[str, SessionStats]:
        """
        Get stats for multiple sessions in a single query (batch - PERFORMANCE).

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

    def _row_to_stats(self, row: sqlite3.Row) -> SessionStats:
        """Convert SQLite row to SessionStats object."""
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

    def compute_and_save(self, session_path: Path) -> SessionStats:
        """
        Convenience method: compute + save stats.

        Args:
            session_path: Path to session folder

        Returns:
            SessionStats object
        """
        stats = self.compute_stats(session_path)
        self.save_stats(stats)
        return stats

    def batch_compute_all(self, sessions_root: Path, force_recompute: bool = False) -> int:
        """
        Batch compute stats for all sessions in a directory.

        Args:
            sessions_root: Root directory containing session folders
            force_recompute: If True, recompute even if stats exist

        Returns:
            Number of sessions processed
        """
        count = 0

        for session_path in sessions_root.iterdir():
            if not session_path.is_dir():
                continue

            session_name = session_path.name

            # Skip if stats exist (unless force_recompute)
            if not force_recompute and self.get_stats(session_name) is not None:
                continue

            try:
                self.compute_and_save(session_path)
                count += 1
            except Exception as e:
                print(f"Error computing stats for {session_name}: {e}")
                continue

        return count
