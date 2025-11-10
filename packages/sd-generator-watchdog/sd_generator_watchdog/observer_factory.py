"""
Observer factory for filesystem watching.

Provides platform-aware observer selection:
- PollingObserver for WSL (inotify doesn't work on /mnt/*)
- Observer (inotify) for native Linux/macOS
"""

import logging
from typing import Any

from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

logger = logging.getLogger(__name__)


def is_wsl() -> bool:
    """
    Detect if running under WSL.

    Returns:
        True if running under WSL, False otherwise
    """
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False


def get_observer_class() -> Any:  # type: ignore[misc]
    """
    Get appropriate Observer class based on platform.

    Returns:
        PollingObserver for WSL (inotify doesn't work on NTFS mounts)
        Observer for native Linux/macOS (uses inotify/kqueue)
    """
    if is_wsl():
        logger.info("🐧 WSL detected - using PollingObserver for filesystem watching")
        return PollingObserver  # type: ignore[return-value]
    return Observer  # type: ignore[return-value]
