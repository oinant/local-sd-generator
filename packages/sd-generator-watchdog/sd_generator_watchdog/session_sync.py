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
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, DirCreatedEvent


logger = logging.getLogger(__name__)


# Import SessionStatsService from webui package
# Note: watchdog depends on webui for this service
try:
    from sd_generator_webui.services.session_stats import SessionStatsService
except ImportError:
    # Fallback: define minimal interface for standalone use
    logger.warning("Could not import SessionStatsService from webui, using fallback")

    @dataclass
    class SessionStats:
        session_name: str
        images_requested: int = 0
        images_actual: int = 0

    class SessionStatsService:
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
        self.observer: Observer | None = None
        self._stop_event = asyncio.Event()
        self._sessions_in_db: Set[str] = set()

    def _load_sessions_in_db(self) -> Set[str]:
        """Get set of session names already in database."""
        try:
            with sqlite3.connect(self.service.db_path) as conn:
                cursor = conn.execute("SELECT session_name FROM session_stats")
                return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to load sessions from DB: {e}")
            return set()

    def _get_filesystem_sessions(self) -> list[Path]:
        """Get all session directories from filesystem."""
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

        return sorted(sessions, key=lambda p: p.name)

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

    def initial_catchup(self) -> tuple[int, int]:
        """
        Perform initial catch-up: import all sessions not yet in database.

        Returns:
            (imported_count, error_count)
        """
        logger.info("🔄 Starting initial session catch-up...")

        # Load current DB state
        self._sessions_in_db = self._load_sessions_in_db()
        logger.info(f"Found {len(self._sessions_in_db)} sessions in database")

        # Get all sessions from filesystem
        all_sessions = self._get_filesystem_sessions()
        logger.info(f"Found {len(all_sessions)} sessions in filesystem")

        # Determine what to import (missing sessions)
        to_import = [
            s for s in all_sessions
            if s.name not in self._sessions_in_db
        ]

        if not to_import:
            logger.info("✓ All sessions already in database")
            return 0, 0

        logger.info(f"📦 Importing {len(to_import)} missing sessions...")

        # Import sessions
        imported = 0
        errors = 0

        for session_path in to_import:
            if self._import_session(session_path):
                imported += 1
            else:
                errors += 1

        logger.info(f"✅ Initial catch-up complete: {imported} imported, {errors} errors")
        return imported, errors

    def start_watching(self):
        """Start watching filesystem for new sessions."""
        if self.observer is not None:
            logger.warning("Filesystem watcher already started")
            return

        logger.info(f"👀 Starting filesystem watcher on: {self.sessions_root}")

        # Create event handler
        handler = SessionDirectoryHandler(self)

        # Create and start observer
        self.observer = Observer()
        self.observer.schedule(handler, str(self.sessions_root), recursive=False)
        self.observer.start()

        logger.info("✓ Filesystem watcher started")

    def stop_watching(self):
        """Stop watching filesystem."""
        if self.observer is None:
            return

        logger.info("🛑 Stopping filesystem watcher...")
        self.observer.stop()
        self.observer.join(timeout=5)
        self.observer = None
        logger.info("✓ Filesystem watcher stopped")

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
                return

        # No manifest after 5s - still try to import (might have images only)
        logger.warning(f"⏱️ Timeout waiting for manifest: {session_name} (importing anyway)")
        self.sync_service._import_session(session_path)
