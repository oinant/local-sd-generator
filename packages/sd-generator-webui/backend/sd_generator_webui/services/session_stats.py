"""
Session Statistics Service - Calculate and cache session stats.

Handles:
- Stats calculation from manifest.json + filesystem
- Session type detection (normal vs seed-sweep)
- Completion percentage calculation
- Orchestration with repository for persistence

This service contains ONLY business logic. All data access is delegated
to the SessionStatsRepository following the Repository Pattern.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sd_generator_webui.models_stats import SessionStats
from sd_generator_webui.repositories.session_stats_repository import (
    SessionStatsRepository,
    SQLiteSessionStatsRepository
)
from sd_generator_webui.storage.session_storage import (
    SessionStorage,
    LocalSessionStorage
)


class SessionStatsService:
    """
    Service for computing and caching session statistics.

    This service contains ONLY business logic:
    - compute_stats(): Calculate stats from manifest + filesystem
    - Session type detection (normal vs seed-sweep)
    - Seed mode detection (fixed/progressive/random)
    - Orchestration (compute + save, batch operations)

    All data access is delegated to SessionStatsRepository.
    """

    def __init__(
        self,
        repository: Optional[SessionStatsRepository] = None,
        storage: Optional[SessionStorage] = None,
        sessions_root: Optional[Path] = None
    ):
        """
        Initialize the service.

        Args:
            repository: SessionStatsRepository implementation. Defaults to SQLiteSessionStatsRepository
            storage: SessionStorage implementation. Defaults to LocalSessionStorage
            sessions_root: Root directory containing session folders
        """
        if repository is None:
            repository = SQLiteSessionStatsRepository()

        if storage is None:
            storage = LocalSessionStorage()

        self.repository = repository
        self.storage = storage
        self.sessions_root = sessions_root

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

        # Load manifest via storage
        manifest = self.storage.read_manifest(session_path)

        if manifest is None:
            # No manifest - count images only via storage
            stats.images_actual = self.storage.count_images(session_path)
            # Get session created_at from first image or directory
            images = self.storage.list_images(session_path)
            if images:
                from sd_generator_webui.storage.local_storage import LocalStorage
                local_storage = LocalStorage()
                metadata = local_storage.get_metadata(images[0])
                stats.session_created_at = metadata.created_at
            else:
                # Fallback to directory creation time
                from sd_generator_webui.storage.local_storage import LocalStorage
                local_storage = LocalStorage()
                metadata = local_storage.get_metadata(session_path)
                stats.session_created_at = metadata.created_at
            stats.stats_computed_at = datetime.now()
            return stats

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
        stats.images_actual = self.storage.count_images(session_path)

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

        # Timestamps - get from directory metadata via storage
        from sd_generator_webui.storage.local_storage import LocalStorage
        local_storage = LocalStorage()
        dir_metadata = local_storage.get_metadata(session_path)
        stats.session_created_at = dir_metadata.created_at
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
        self.repository.save(stats)

    def get_stats(self, session_name: str) -> Optional[SessionStats]:
        """
        Get cached stats for a session.

        Args:
            session_name: Session folder name

        Returns:
            SessionStats if found, None otherwise
        """
        return self.repository.get(session_name)

    def list_all_stats(self) -> List[SessionStats]:
        """
        List stats for all sessions.

        Returns:
            List of SessionStats objects
        """
        return self.repository.list_all()

    def get_stats_batch(self, session_names: List[str]) -> Dict[str, SessionStats]:
        """
        Get stats for multiple sessions in a single query (batch - PERFORMANCE).

        Args:
            session_names: List of session names to fetch

        Returns:
            Dict mapping session_name to SessionStats (missing sessions not included)
        """
        return self.repository.get_batch(session_names)

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

        # List sessions via storage
        session_paths = self.storage.list_sessions(sessions_root)

        for session_path in session_paths:
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

    def get_global_stats(self) -> Dict[str, Any]:
        """
        Get global statistics across all sessions.

        Returns:
            Dict with global stats (total_sessions, sessions_ongoing, sessions_completed,
            sessions_aborted, total_images, max_images, min_images, avg_images)
        """
        return self.repository.get_global_stats()
