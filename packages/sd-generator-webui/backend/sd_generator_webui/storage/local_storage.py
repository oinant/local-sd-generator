"""
Local filesystem storage implementation.

This module provides a concrete implementation of Storage interface
using local filesystem via pathlib.
"""

from datetime import datetime
from pathlib import Path
from typing import List

from sd_generator_webui.storage.base import Storage, FileMetadata


class LocalStorage(Storage):
    """
    Local filesystem implementation of Storage interface.

    Uses pathlib for all filesystem operations.
    This is the default storage adapter for local development.
    """

    def exists(self, path: Path) -> bool:
        """Check if file or directory exists."""
        return path.exists()

    def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        return path.is_file()

    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory."""
        return path.is_dir()

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """Read text content from file."""
        return path.read_text(encoding=encoding)

    def read_bytes(self, path: Path) -> bytes:
        """Read binary content from file."""
        return path.read_bytes()

    def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """Write text content to file."""
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)

    def write_bytes(self, path: Path, content: bytes) -> None:
        """Write binary content to file."""
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def list_dir(self, path: Path) -> List[Path]:
        """List all items in directory."""
        if not path.is_dir():
            return []
        return list(path.iterdir())

    def get_metadata(self, path: Path) -> FileMetadata:
        """Get metadata for a file."""
        stat = path.stat()

        return FileMetadata(
            filename=path.name,
            path=path,
            size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime)
        )
