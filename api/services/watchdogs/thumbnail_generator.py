#!/usr/bin/env python3
"""
Thumbnail Generator for SD Image Gallery
Converts PNG images from CLI/apioutput to WebP thumbnails in api/static/
Supports three modes: initial (full scan), diff (incremental), and watch (real-time)
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Set
from PIL import Image
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SOURCE_DIR = Path("CLI/apioutput")
TARGET_DIR = Path("api/static/thumbnails")
THUMBNAIL_HEIGHT = 240
WEBP_QUALITY = 85
STATE_FILE = Path("api/services/watchdogs/.thumbnail_state.json")
TIMESTAMP_FORMAT = "%Y-%m-%d_%H%M%S"


class ThumbnailGenerator:
    """Handles conversion of PNG images to WebP thumbnails"""

    def __init__(self, source_dir: Path, target_dir: Path):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def create_thumbnail(self, source_path: Path, target_path: Path) -> bool:
        """
        Create a WebP thumbnail from a PNG image

        Args:
            source_path: Path to source PNG image
            target_path: Path to target WebP thumbnail

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Open and process image
            with Image.open(source_path) as img:
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

                # Save as WebP
                img_resized.save(target_path, 'WEBP', quality=WEBP_QUALITY, method=6)

            logger.info(f"✓ Created thumbnail: {target_path.relative_to(self.target_dir)}")
            self.processed_count += 1
            return True

        except Exception as e:
            logger.error(f"✗ Failed to process {source_path}: {e}")
            self.error_count += 1
            return False

    def should_process(self, source_path: Path, target_path: Path) -> bool:
        """Check if thumbnail needs to be created"""
        # Don't process if target already exists
        if target_path.exists():
            self.skipped_count += 1
            return False
        return True

    def process_image(self, source_path: Path) -> bool:
        """Process a single image file"""
        # Calculate relative path and target path
        rel_path = source_path.relative_to(self.source_dir)
        target_path = self.target_dir / rel_path.with_suffix('.webp')

        if self.should_process(source_path, target_path):
            return self.create_thumbnail(source_path, target_path)
        return False

    def process_directory(self, directory: Optional[Path] = None) -> None:
        """Process all PNG images in directory and subdirectories"""
        if directory is None:
            directory = self.source_dir

        logger.info(f"Scanning directory: {directory}")

        # Find all PNG files recursively
        png_files = list(directory.rglob("*.png"))
        logger.info(f"Found {len(png_files)} PNG files")

        for png_file in png_files:
            self.process_image(png_file)

        self.print_summary()

    def print_summary(self):
        """Print processing summary"""
        logger.info("="*60)
        logger.info(f"Processing complete:")
        logger.info(f"  ✓ Processed: {self.processed_count}")
        logger.info(f"  ⊘ Skipped: {self.skipped_count}")
        logger.info(f"  ✗ Errors: {self.error_count}")
        logger.info("="*60)


class StateManager:
    """Manages persistent state for diff mode"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> dict:
        """Load state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state file: {e}")
        return {}

    def save_state(self, state: dict) -> None:
        """Save state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"State saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def get_last_timestamp(self) -> Optional[datetime]:
        """Get the last processed timestamp"""
        state = self.load_state()
        last_ts = state.get('last_timestamp')
        if last_ts:
            try:
                return datetime.strptime(last_ts, TIMESTAMP_FORMAT)
            except ValueError:
                logger.warning(f"Invalid timestamp in state: {last_ts}")
        return None

    def update_timestamp(self, timestamp: datetime) -> None:
        """Update the last processed timestamp"""
        state = self.load_state()
        state['last_timestamp'] = timestamp.strftime(TIMESTAMP_FORMAT)
        self.save_state(state)


def parse_folder_timestamp(folder_name: str) -> Optional[datetime]:
    """
    Extract timestamp from folder name (format: YYYY-MM-DD_HHMMSS_*)

    Args:
        folder_name: Name of the folder

    Returns:
        datetime object or None if parsing fails
    """
    try:
        # Extract timestamp part (first 17 characters: YYYY-MM-DD_HHMMSS)
        ts_str = folder_name[:17]
        return datetime.strptime(ts_str, TIMESTAMP_FORMAT)
    except (ValueError, IndexError):
        return None


def get_folders_to_process(source_dir: Path, since: Optional[datetime] = None) -> list[Path]:
    """
    Get list of folders to process, optionally filtered by timestamp

    Args:
        source_dir: Source directory to scan
        since: Only return folders newer than this datetime

    Returns:
        List of folder paths to process
    """
    folders = []

    for item in source_dir.iterdir():
        if not item.is_dir():
            continue

        folder_ts = parse_folder_timestamp(item.name)

        if folder_ts is None:
            logger.warning(f"Skipping folder with invalid timestamp format: {item.name}")
            continue

        if since is None or folder_ts > since:
            folders.append((item, folder_ts))

    # Sort by timestamp
    folders.sort(key=lambda x: x[1])

    return [f[0] for f in folders]


def mode_initial(source_dir: Path, target_dir: Path) -> None:
    """Process all images in initial mode"""
    logger.info("Starting INITIAL mode - processing all images")
    generator = ThumbnailGenerator(source_dir, target_dir)
    generator.process_directory()

    # Update state with latest timestamp
    folders = get_folders_to_process(source_dir)
    if folders:
        latest_folder = folders[-1]
        latest_ts = parse_folder_timestamp(latest_folder.name)
        if latest_ts:
            state_mgr = StateManager(STATE_FILE)
            state_mgr.update_timestamp(latest_ts)


def mode_diff(source_dir: Path, target_dir: Path) -> None:
    """Process only new folders since last run"""
    logger.info("Starting DIFF mode - processing new folders only")

    state_mgr = StateManager(STATE_FILE)
    last_ts = state_mgr.get_last_timestamp()

    if last_ts:
        logger.info(f"Last processed: {last_ts.strftime(TIMESTAMP_FORMAT)}")
    else:
        logger.info("No previous state found - processing all folders")

    folders = get_folders_to_process(source_dir, since=last_ts)

    if not folders:
        logger.info("No new folders to process")
        return

    logger.info(f"Found {len(folders)} new folders to process")

    generator = ThumbnailGenerator(source_dir, target_dir)

    for folder in folders:
        generator.process_directory(folder)

    # Update state with latest timestamp
    if folders:
        latest_folder = folders[-1]
        latest_ts = parse_folder_timestamp(latest_folder.name)
        if latest_ts:
            state_mgr.update_timestamp(latest_ts)


def mode_watch(source_dir: Path, target_dir: Path) -> None:
    """Watch for new images and process them in real-time"""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        logger.error("watchdog library not installed. Install with: pip install watchdog")
        sys.exit(1)

    logger.info("Starting WATCH mode - monitoring for new images")
    logger.info(f"Watching: {source_dir.absolute()}")
    logger.info("Press Ctrl+C to stop")

    # First, process any new folders since last run
    logger.info("Processing any pending folders...")
    mode_diff(source_dir, target_dir)

    generator = ThumbnailGenerator(source_dir, target_dir)

    class ImageHandler(FileSystemEventHandler):
        def on_created(self, event):
            if event.is_directory:
                return

            file_path = Path(event.src_path)

            # Only process PNG files
            if file_path.suffix.lower() != '.png':
                return

            # Check if file is in source directory
            if not file_path.is_relative_to(source_dir):
                return

            logger.info(f"New image detected: {file_path.relative_to(source_dir)}")
            generator.process_image(file_path)

    event_handler = ImageHandler()
    observer = Observer()
    observer.schedule(event_handler, str(source_dir.absolute()), recursive=True)
    observer.start()

    try:
        observer.join()
    except KeyboardInterrupt:
        logger.info("\nStopping watcher...")
        observer.stop()
        observer.join()
        generator.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="Generate WebP thumbnails from PNG images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  initial - Process all images (creates thumbnails for all PNGs)
  diff    - Process only new folders since last run
  watch   - Monitor for new images and process them in real-time
        """
    )

    parser.add_argument(
        'mode',
        choices=['initial', 'diff', 'watch'],
        help='Processing mode'
    )

    parser.add_argument(
        '--source',
        type=Path,
        default=SOURCE_DIR,
        help=f'Source directory (default: {SOURCE_DIR})'
    )

    parser.add_argument(
        '--target',
        type=Path,
        default=TARGET_DIR,
        help=f'Target directory (default: {TARGET_DIR})'
    )

    args = parser.parse_args()

    # Validate directories
    if not args.source.exists():
        logger.error(f"Source directory does not exist: {args.source}")
        sys.exit(1)

    # Create target directory if needed
    args.target.mkdir(parents=True, exist_ok=True)

    # Run selected mode
    if args.mode == 'initial':
        mode_initial(args.source, args.target)
    elif args.mode == 'diff':
        mode_diff(args.source, args.target)
    elif args.mode == 'watch':
        mode_watch(args.source, args.target)


if __name__ == '__main__':
    main()
