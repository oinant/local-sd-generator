"""
Background service for session synchronization.

Watches the sessions directory and automatically imports new sessions into the database.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Set, Optional, List, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, DirCreatedEvent, FileModifiedEvent
from sd_generator_watchdog.observer_factory import get_observer_class


logger = logging.getLogger(__name__)


# Import SessionStatsService from webui package
# Note: watchdog depends on webui for this service
try:
    from sd_generator_webui.services.session_stats import SessionStatsService  # type: ignore[import-untyped]
except ImportError:
    # Fallback: define minimal interface for standalone use
    logger.warning("Could not import SessionStatsService from webui, using fallback")

    @dataclass
    class SessionStats:
        session_name: str
        images_requested: int = 0
        images_actual: int = 0

    class SessionStatsService:  # type: ignore[no-redef]
        def __init__(self, db_path: Optional[Path] = None, sessions_root: Optional[Path] = None):
            self.db_path = db_path
            self.sessions_root = sessions_root

        def compute_and_save(self, session_path: Path):
            logger.warning(f"Fallback SessionStatsService: skipping {session_path}")


class SessionSyncService:
    """
    Background service that:
    1. Performs initial catch-up of missing sessions on startup
    2. Watches filesystem for new sessions and imports them automatically
    """

    def __init__(
        self,
        sessions_root: Path,
        db_path: Optional[Path] = None
    ):
        """
        Args:
            sessions_root: Directory containing session folders (e.g., apioutput/)
            db_path: Path to sessions.db (defaults to sessions_root/../.sdgen/sessions.db)
        """
        self.sessions_root = sessions_root

        if db_path is None:
            # Default: .sdgen/sessions.db in parent of sessions_root
            db_path = sessions_root.parent / ".sdgen" / "sessions.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.service = SessionStatsService(sessions_root=sessions_root)
        self.root_observer: "Observer" | None = None  # type: ignore[valid-type]
        self.session_observers: Dict[str, "Observer"] = {}  # type: ignore[valid-type]
        self._stop_event = asyncio.Event()
        self._sessions_in_db: Set[str] = set()

    def _session_exists_in_db(self, session_name: str) -> bool:
        """Check if a session exists in database (single query)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM session_stats WHERE session_name = ? LIMIT 1",
                    (session_name,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check session in DB: {e}")
            return False

    def _get_filesystem_sessions_sorted(self) -> list[Path]:
        """Get all session directories from filesystem, sorted by creation time (newest first)."""
        if not self.sessions_root.exists():
            logger.warning(f"Sessions root not found: {self.sessions_root}")
            return []

        sessions = []
        for item in self.sessions_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Valid session: has manifest.json or PNG files
                has_manifest = (item / "manifest.json").exists()
                has_images = any(item.glob("*.png"))

                if has_manifest or has_images:
                    sessions.append(item)

        # Sort by modification time (newest first) for smart catchup
        return sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)

    def _import_session(self, session_path: Path) -> bool:
        """Import a single session into the database."""
        session_name = session_path.name

        try:
            # Compute stats
            stats = self.service.compute_stats(session_path)

            # Save to database
            self.service.save_stats(stats)

            # Update cache
            self._sessions_in_db.add(session_name)

            logger.info(f"✓ Imported session: {session_name}")
            return True

        except FileNotFoundError as e:
            logger.warning(f"Session not found: {session_name} ({e})")
            return False
        except Exception as e:
            logger.error(f"Error importing {session_name}: {e}", exc_info=True)
            return False

    def _start_watching_session(self, session_path: Path) -> None:
        """Start watching a specific session for manifest updates."""
        session_name = session_path.name

        # Don't watch if already watching
        if session_name in self.session_observers:
            return

        logger.info(f"👁️  Starting watch on active session: {session_name}")

        # Create handler for this session
        handler = SessionDirectoryHandler(self)

        # Create observer for this session only
        observer_class = get_observer_class()
        observer = observer_class()  # type: ignore[misc]
        observer.schedule(handler, str(session_path), recursive=False)
        observer.start()  # type: ignore[attr-defined]

        # Store observer
        self.session_observers[session_name] = observer

    def _stop_watching_session(self, session_name: str) -> None:
        """Stop watching a specific session."""
        observer = self.session_observers.get(session_name)
        if observer is None:
            return

        logger.info(f"👁️  Stopping watch on completed session: {session_name}")
        observer.stop()  # type: ignore[attr-defined]
        observer.join(timeout=2)  # type: ignore[attr-defined]

        # Remove from dict
        del self.session_observers[session_name]

    def initial_catchup(self) -> tuple[int, int]:
        """
        Smart catch-up: import only missing sessions.

        Strategy:
        1. Sort sessions by creation time (newest first)
        2. For each session, check if exists in DB (single query)
        3. If exists → add to cache, skip, continue
        4. If missing → import this session, continue to next
        5. Stop at next existing session (assume older ones exist)

        Returns:
            (imported_count, error_count)
        """
        logger.info("🔄 Starting smart session catch-up...")

        # Get filesystem sessions sorted by creation time (newest first)
        all_sessions = self._get_filesystem_sessions_sorted()
        logger.info(f"📂 Found {len(all_sessions)} sessions in filesystem")

        # Process sessions until we find an existing one
        found_missing = False
        imported = 0
        errors = 0

        for session_path in all_sessions:
            session_name = session_path.name

            if self._session_exists_in_db(session_name):
                # Session exists in DB - add to cache
                self._sessions_in_db.add(session_name)

                if found_missing:
                    # We've imported missing sessions and now found an existing one → stop
                    logger.info(f"✓ Found existing session: {session_name}, stopping catch-up")
                    break
                # Skip this existing session, continue to next
                continue

            # Session missing - import it
            found_missing = True
            logger.info(f"📍 Importing missing session: {session_name}")

            if self._import_session(session_path):
                imported += 1
                # _import_session() already adds to cache on success
            else:
                errors += 1

        if not found_missing:
            logger.info("✓ All sessions already in database")

        logger.info(f"✅ Smart catch-up complete: {imported} imported, {errors} errors")
        return imported, errors

    def _resume_latest_active_session(self) -> None:
        """
        Check the latest session in DB and resume watching if still active.

        This fixes the bug where watchdog doesn't update stats for ongoing sessions
        when it starts after the session has already begun.
        """
        try:
            # Use repository to get latest session (sorted DESC by default)
            all_stats = self.service.repository.list_all()
            if not all_stats:
                logger.info("✓ No sessions in database yet")
                return

            latest_stats = all_stats[0]  # First item is the latest
            session_path = self.sessions_root / latest_stats.session_name

            # Check manifest status
            manifest_path = session_path / "manifest.json"
            if not manifest_path.exists():
                logger.info(f"⚠️  Latest session has no manifest: {latest_stats.session_name}")
                return

            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    status = manifest.get("status", "in_progress")

                    if status == "ongoing" or status == "in_progress":
                        logger.info(f"🔄 Resuming watch on active session: {latest_stats.session_name}")
                        self._start_watching_session(session_path)
                    else:
                        logger.info(f"✓ Latest session already {status}: {latest_stats.session_name}")

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse manifest for {latest_stats.session_name}: {e}")
            except Exception as e:
                logger.warning(f"Error reading manifest for {latest_stats.session_name}: {e}")

        except AttributeError as e:
            logger.warning(f"Repository not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to resume active session watching: {e}", exc_info=True)

    def start_watching(self):
        """Start watching filesystem for new sessions."""
        if self.root_observer is not None:
            logger.warning("Filesystem watcher already started")
            return

        logger.info(f"👀 Starting filesystem watcher on: {self.sessions_root}")

        # Create event handler
        handler = SessionDirectoryHandler(self)

        # Create and start root observer (non-recursive, detects new session folders)
        observer_class = get_observer_class()
        self.root_observer = observer_class()  # type: ignore[misc]
        self.root_observer.schedule(handler, str(self.sessions_root), recursive=False)
        self.root_observer.start()  # type: ignore[attr-defined]

        logger.info("✓ Filesystem watcher started (root observer)")

    def stop_watching(self):
        """Stop watching filesystem."""
        # Stop root observer
        if self.root_observer is not None:
            logger.info("🛑 Stopping root filesystem watcher...")
            self.root_observer.stop()  # type: ignore[attr-defined]
            self.root_observer.join(timeout=5)  # type: ignore[attr-defined]
            self.root_observer = None
            logger.info("✓ Root watcher stopped")

        # Stop all session observers
        for session_name in list(self.session_observers.keys()):
            self._stop_watching_session(session_name)

        logger.info("✓ All watchers stopped")

    async def run(self):
        """
        Main service loop.
        1. Initial catch-up
        2. Start filesystem watcher
        3. Wait for stop signal
        """
        try:
            # Initial catch-up
            imported, errors = self.initial_catchup()
            logger.info(f"Initial sync: {imported} imported, {errors} errors")

            # Resume watching latest active session if ongoing
            self._resume_latest_active_session()

            # Start filesystem watcher
            self.start_watching()

            # Wait for stop signal
            logger.info("📡 Session sync service running...")
            await self._stop_event.wait()

        except Exception as e:
            logger.error(f"Session sync service error: {e}", exc_info=True)
        finally:
            self.stop_watching()

    def stop(self):
        """Signal service to stop."""
        logger.info("Stopping session sync service...")
        self._stop_event.set()


class SessionDirectoryHandler(FileSystemEventHandler):
    """
    Watchdog handler for session directory events.

    Triggers import when:
    - New directory created (potential new session)
    - manifest.json created in a directory
    """

    def __init__(self, sync_service: SessionSyncService):
        self.sync_service = sync_service
        super().__init__()

    def on_created(self, event):
        """Handle creation events."""
        # Ignore non-directory events for now
        if isinstance(event, DirCreatedEvent):
            # New directory created - potential session
            session_path = Path(event.src_path)
            session_name = session_path.name

            # Skip hidden directories
            if session_name.startswith('.'):
                return

            # Check if already in DB
            if session_name in self.sync_service._sessions_in_db:
                return

            logger.info(f"📁 New session directory detected: {session_name}")

            # Wait a bit for manifest.json to be written
            # (manifest is usually written shortly after directory creation)
            asyncio.create_task(self._delayed_import(session_path))

        elif isinstance(event, FileCreatedEvent) and event.src_path.endswith("manifest.json"):
            # manifest.json created - session is ready
            session_path = Path(event.src_path).parent
            session_name = session_path.name

            # Check if already in DB
            if session_name in self.sync_service._sessions_in_db:
                return

            logger.info(f"📄 Manifest detected for: {session_name}")
            self.sync_service._import_session(session_path)

            # Start watching this session for updates
            self.sync_service._start_watching_session(session_path)

    def on_modified(self, event):
        """Handle modification events."""
        if isinstance(event, FileModifiedEvent) and event.src_path.endswith("manifest.json"):
            # manifest.json modified - update session stats
            session_path = Path(event.src_path).parent
            session_name = session_path.name

            # Only update if session already in DB
            if session_name in self.sync_service._sessions_in_db:
                logger.info(f"📝 Manifest updated for: {session_name}, re-computing stats")
                self.sync_service._import_session(session_path)

                # Check if session is completed or aborted
                manifest_file = Path(event.src_path)
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                        status = manifest.get("status", "in_progress")

                        if status in ("completed", "aborted"):
                            # Session finished - stop watching
                            logger.info(f"✅ Session {status}: {session_name}")
                            self.sync_service._stop_watching_session(session_name)
                except Exception as e:
                    logger.warning(f"Failed to read manifest status for {session_name}: {e}")

            else:
                # Not in DB yet - treat as new session
                logger.info(f"📄 Manifest detected for new session: {session_name}")
                self.sync_service._import_session(session_path)
                # Start watching this new session
                self.sync_service._start_watching_session(session_path)

    async def _delayed_import(self, session_path: Path):
        """
        Wait for manifest.json to be written, then import.

        Some session directories are created before manifest.json is written.
        We wait a short time to ensure the manifest is ready.
        """
        session_name = session_path.name

        # Wait up to 5 seconds for manifest.json
        manifest_path = session_path / "manifest.json"

        for _ in range(10):  # 10 * 0.5s = 5s max
            await asyncio.sleep(0.5)

            if manifest_path.exists():
                logger.info(f"📄 Manifest ready for delayed import: {session_name}")
                self.sync_service._import_session(session_path)
                # Start watching this new session
                self.sync_service._start_watching_session(session_path)
                return

        # No manifest after 5s - still try to import (might have images only)
        logger.warning(f"⏱️ Timeout waiting for manifest: {session_name} (importing anyway)")
        self.sync_service._import_session(session_path)
        # Start watching even without manifest (will watch for its creation)
        self.sync_service._start_watching_session(session_path)
