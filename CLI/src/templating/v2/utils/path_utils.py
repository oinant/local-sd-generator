"""
Path resolution utilities for Template System V2.0.

This module provides path resolution helpers. Most path logic is
handled directly in YamlLoader.resolve_path(), but this module
can contain additional path-related utilities if needed.
"""

from pathlib import Path


def normalize_path(path: Path | str) -> Path:
    """
    Normalize a path by resolving symlinks and relative components.

    Args:
        path: Path to normalize

    Returns:
        Normalized absolute Path object
    """
    return Path(path).resolve()


def is_relative_to(path: Path, base: Path) -> bool:
    """
    Check if a path is relative to a base path.

    This is a compatibility shim for Python < 3.9 which doesn't have
    Path.is_relative_to() built-in.

    Args:
        path: Path to check
        base: Base path

    Returns:
        True if path is under base, False otherwise
    """
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False
