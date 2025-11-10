"""
Base storage interfaces for filesystem abstraction.

This module provides abstract base classes for storage operations.
Following the Storage Pattern (similar to Repository Pattern for filesystem) allows:
- Easy testing with mock/in-memory implementations
- Swapping local filesystem → S3/MinIO without changing business logic
- Clear separation between domain logic and filesystem operations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class FileMetadata:
    """Metadata for a file in storage."""

    filename: str
    path: Path
    size: int
    created_at: datetime
    modified_at: datetime


class Storage(ABC):
    """
    Base storage interface for filesystem operations.

    This abstract class defines the minimal contract for storage adapters.
    It provides common filesystem operations abstracted from implementation.
    """

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """
        Check if a file or directory exists.

        Args:
            path: Path to check

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    def is_file(self, path: Path) -> bool:
        """
        Check if path is a file.

        Args:
            path: Path to check

        Returns:
            True if is file, False otherwise
        """
        pass

    @abstractmethod
    def is_dir(self, path: Path) -> bool:
        """
        Check if path is a directory.

        Args:
            path: Path to check

        Returns:
            True if is directory, False otherwise
        """
        pass

    @abstractmethod
    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """
        Read text content from a file.

        Args:
            path: Path to file
            encoding: Text encoding (default: utf-8)

        Returns:
            Text content

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass

    @abstractmethod
    def read_bytes(self, path: Path) -> bytes:
        """
        Read binary content from a file.

        Args:
            path: Path to file

        Returns:
            Binary content

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass

    @abstractmethod
    def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """
        Write text content to a file.

        Args:
            path: Path to file
            content: Text content to write
            encoding: Text encoding (default: utf-8)
        """
        pass

    @abstractmethod
    def write_bytes(self, path: Path, content: bytes) -> None:
        """
        Write binary content to a file.

        Args:
            path: Path to file
            content: Binary content to write
        """
        pass

    @abstractmethod
    def list_dir(self, path: Path) -> List[Path]:
        """
        List all items in a directory.

        Args:
            path: Path to directory

        Returns:
            List of paths (files and directories)
        """
        pass

    @abstractmethod
    def get_metadata(self, path: Path) -> FileMetadata:
        """
        Get metadata for a file.

        Args:
            path: Path to file

        Returns:
            FileMetadata object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass
