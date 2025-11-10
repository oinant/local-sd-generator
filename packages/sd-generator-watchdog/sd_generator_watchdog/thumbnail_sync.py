"""
Background service for thumbnail synchronization.

Watches the sessions directory and automatically generates WebP thumbnails
for PNG images in real-time.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional
from PIL import Image
import io

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from sd_generator_watchdog.observer_factory import get_observer_class

logger = logging.getLogger(__name__)

# Import Storage interfaces from webui package
try:
    from sd_generator_webui.storage.image_storage import ImageStorage, LocalImageStorage  # type: ignore[import-untyped]
    from sd_generator_webui.storage.session_storage import SessionStorage, LocalSessionStorage  # type: ignore[import-untyped]
except ImportError:
    logger.warning("Could not import Storage interfaces from webui, thumbnails disabled")
    ImageStorage = None  # type: ignore
    LocalImageStorage = None  # type: ignore
    SessionStorage = None  # type: ignore
    LocalSessionStorage = None  # type: ignore


# Constants
THUMBNAIL_HEIGHT = 240
WEBP_QUALITY = 85


class ThumbnailSyncService(FileSystemEventHandler):
    """
    Background service that:
    1. Performs initial catch-up of missing thumbnails on startup
    2. Watches filesystem for new images and generates thumbnails automatically
    """

    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        image_storage: Optional[ImageStorage] = None,
        session_storage: Optional[SessionStorage] = None
    ):
        """
        Initialize ThumbnailSyncService.

        Args:
            source_dir: Source directory containing session folders (e.g., ./apioutput)
            target_dir: Target directory for thumbnails (e.g., ./api/static/thumbnails)
            image_storage: ImageStorage implementation (optional)
            session_storage: SessionStorage implementation (optional)
        """
        self.source_dir = source_dir
        self.target_dir = target_dir

        # Storage dependencies (with fallback)
        if LocalImageStorage is None or LocalSessionStorage is None:
            raise RuntimeError("Storage interfaces not available - install sd-generator-webui")

        self.image_storage = image_storage or LocalImageStorage()
        self.session_storage = session_storage or LocalSessionStorage()

        self.observer: Optional["Observer"] = None  # type: ignore[valid-type]
        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def create_thumbnail(self, source_path: Path, target_path: Path) -> bool:
        """
        Create a WebP thumbnail from a PNG image.

        Args:
            source_path: Path to source PNG image
            target_path: Path to target WebP thumbnail

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read image bytes via ImageStorage
            image_bytes = self.image_storage.read_image_bytes(source_path)

            # Open and process image
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Calculate new dimensions maintaining aspect ratio
                aspect_ratio = img.width / img.height
                new_height = THUMBNAIL_HEIGHT
                new_width = int(new_height * aspect_ratio)

                # Resize image
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Convert to RGB if necessary (WebP doesn't support palette mode well)
                if img_resized.mode in ('P', 'RGBA', 'LA'):
                    rgb_img = Image.new('RGB', img_resized.size, (255, 255, 255))
                    if img_resized.mode == 'P':
                        img_resized = img_resized.convert('RGBA')
                    rgb_img.paste(img_resized, mask=img_resized.split()[-1] if 'A' in img_resized.mode else None)
                    img_resized = rgb_img

                # Save as WebP to bytes buffer
                output_buffer = io.BytesIO()
                img_resized.save(output_buffer, 'WEBP', quality=WEBP_QUALITY, method=6)
                output_bytes = output_buffer.getvalue()

            # Write WebP bytes via ImageStorage
            self.image_storage.write_image_bytes(target_path, output_bytes)

            logger.info(f"✓ Created thumbnail: {target_path.relative_to(self.target_dir)}")
            self.processed_count += 1
            return True

        except Exception as e:
            logger.error(f"✗ Failed to process {source_path}: {e}")
            self.error_count += 1
            return False

    def should_process(self, source_path: Path, target_path: Path) -> bool:
        """Check if thumbnail needs to be created."""
        # Don't process if target already exists
        if self.image_storage.image_exists(target_path):
            self.skipped_count += 1
            return False
        return True

    def process_image(self, source_path: Path) -> bool:
        """Process a single image file."""
        try:
            # Calculate relative path and target path
            rel_path = source_path.relative_to(self.source_dir)
            target_path = self.target_dir / rel_path.with_suffix('.webp')

            if self.should_process(source_path, target_path):
                return self.create_thumbnail(source_path, target_path)
            return False
        except ValueError:
            # Path is not relative to source_dir
            return False

    def _count_session_thumbnails(self, session_path: Path) -> int:
        """Count existing thumbnails for a session."""
        try:
            rel_path = session_path.relative_to(self.source_dir)
            session_thumb_dir = self.target_dir / rel_path

            if not self.image_storage.image_exists(session_thumb_dir):
                return 0

            # Count .webp files in session thumbnail directory
            return self.session_storage.count_images(session_thumb_dir, extensions=[".webp"])
        except Exception:
            return 0

    async def initial_catchup(self) -> None:
        """
        Smart catch-up: process only incomplete sessions.

        Strategy:
        1. Sort sessions by creation time (newest first)
        2. For each session, compare thumbnail count vs source image count
        3. If counts match → session complete, skip
        4. If mismatch → process this session, continue to next session
        5. Stop at next complete session (assume older ones are complete)
        """
        logger.info(f"🔄 Starting smart catch-up: {self.source_dir}")

        # List all sessions and sort by creation time (newest first)
        sessions = self.session_storage.list_sessions(self.source_dir)
        sessions_sorted = sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)

        logger.info(f"📂 Found {len(sessions_sorted)} sessions")

        # Process sessions until we find a complete one
        found_incomplete = False
        sessions_processed = 0

        for session_path in sessions_sorted:
            source_count = self.session_storage.count_images(session_path, extensions=[".png"])
            thumb_count = self._count_session_thumbnails(session_path)

            if source_count == thumb_count:
                # Session complete
                if found_incomplete:
                    # We've processed incomplete sessions and now found a complete one → stop
                    logger.info(f"✓ Found complete session: {session_path.name}, stopping catch-up")
                    break
                # Skip this complete session, continue to next
                continue

            # Session incomplete - process it
            found_incomplete = True
            sessions_processed += 1
            logger.info(f"📍 Processing incomplete session: {session_path.name} ({thumb_count}/{source_count} thumbnails)")

            session_pngs = self.session_storage.list_images(session_path, extensions=[".png"])
            for png_file in session_pngs:
                self.process_image(png_file)

        if not found_incomplete:
            logger.info("✓ All sessions up-to-date, no catch-up needed")

        logger.info("="*60)
        logger.info(f"✓ Initial catch-up complete:")
        logger.info(f"  ✓ Processed: {self.processed_count}")
        logger.info(f"  ⊘ Skipped: {self.skipped_count}")
        logger.info(f"  📦 Sessions processed: {sessions_processed}")
        logger.info(f"  ✗ Errors: {self.error_count}")
        logger.info("="*60)

    def on_created(self, event):
        """Handle file creation events (watchdog callback)."""
        if isinstance(event, FileCreatedEvent):
            file_path = Path(event.src_path)

            # Only process PNG files
            if file_path.suffix.lower() != '.png':
                return

            # Check if file is in source directory
            try:
                file_path.relative_to(self.source_dir)
            except ValueError:
                return

            logger.info(f"🆕 New image detected: {file_path.relative_to(self.source_dir)}")
            self.process_image(file_path)

    async def run(self) -> None:
        """Run the thumbnail sync service (async main loop)."""
        logger.info(f"🖼️  Starting Thumbnail Sync Service")
        logger.info(f"📂 Source: {self.source_dir}")
        logger.info(f"🎯 Target: {self.target_dir}")

        # Initial catch-up
        await self.initial_catchup()

        # Start watching
        logger.info("👀 Watching for new images...")
        observer_class = get_observer_class()
        self.observer = observer_class()  # type: ignore[misc]
        self.observer.schedule(self, str(self.source_dir), recursive=True)
        self.observer.start()  # type: ignore[attr-defined]

        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("🛑 Received stop signal")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the thumbnail sync service."""
        if self.observer:
            logger.info("🛑 Stopping observer...")
            self.observer.stop()  # type: ignore[attr-defined]
            self.observer.join()  # type: ignore[attr-defined]
            logger.info("✓ Observer stopped")

        logger.info("="*60)
        logger.info(f"Final stats:")
        logger.info(f"  ✓ Processed: {self.processed_count}")
        logger.info(f"  ⊘ Skipped: {self.skipped_count}")
        logger.info(f"  ✗ Errors: {self.error_count}")
        logger.info("="*60)
