"""
CLI for SD Generator Watchdog service.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from sd_generator_watchdog.session_sync import SessionSyncService
from sd_generator_watchdog.thumbnail_sync import ThumbnailSyncService
from sd_generator_watchdog.__about__ import __version__

app = typer.Typer(
    name="sdgen-watchdog",
    help="Filesystem watchers for SD Image Generator",
    no_args_is_help=True,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@app.command()
def run(
    sessions_dir: Path = typer.Option(
        ...,
        "--sessions-dir",
        "-s",
        help="Directory containing session folders (e.g., ./apioutput)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    db_path: Optional[Path] = typer.Option(
        None,
        "--db-path",
        "-d",
        help="Path to sessions.db (defaults to <sessions_dir>/../.sdgen/sessions.db)",
        resolve_path=True,
    ),
):
    """
    Run watchdog service in foreground.

    Watches sessions_dir for new session folders and automatically
    imports them into the database.
    """
    logger.info(f"🔄 Starting SD Generator Watchdog v{__version__}")
    logger.info(f"📂 Watching sessions directory: {sessions_dir}")

    if db_path:
        logger.info(f"💾 Database: {db_path}")
    else:
        logger.info(f"💾 Database: {sessions_dir.parent}/.sdgen/sessions.db (default)")

    # Create service
    service = SessionSyncService(
        sessions_root=sessions_dir,
        db_path=db_path
    )

    # Run service
    try:
        asyncio.run(service.run())
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal, shutting down...")
        service.stop()
    except Exception as e:
        logger.error(f"❌ Watchdog service crashed: {e}", exc_info=True)
        sys.exit(1)

    logger.info("✓ Watchdog service stopped cleanly")


@app.command()
def thumbnail(
    source_dir: Path = typer.Option(
        ...,
        "--source-dir",
        "-s",
        help="Source directory containing sessions (e.g., ./apioutput)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    target_dir: Path = typer.Option(
        ...,
        "--target-dir",
        "-t",
        help="Target directory for thumbnails (e.g., ./api/static/thumbnails)",
        resolve_path=True,
    ),
):
    """
    Run thumbnail watchdog service in foreground.

    Watches source_dir for new PNG images and automatically
    generates WebP thumbnails in target_dir.
    """
    logger.info(f"🖼️  Starting SD Generator Thumbnail Watchdog v{__version__}")
    logger.info(f"📂 Watching source directory: {source_dir}")
    logger.info(f"🎯 Target directory: {target_dir}")

    # Create target directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)

    # Create service
    service = ThumbnailSyncService(
        source_dir=source_dir,
        target_dir=target_dir
    )

    # Run service
    try:
        asyncio.run(service.run())
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal, shutting down...")
        service.stop()
    except Exception as e:
        logger.error(f"❌ Thumbnail watchdog crashed: {e}", exc_info=True)
        sys.exit(1)

    logger.info("✓ Thumbnail watchdog stopped cleanly")


@app.command()
def version():
    """Show version information."""
    typer.echo(f"sdgen-watchdog version {__version__}")


if __name__ == "__main__":
    app()
