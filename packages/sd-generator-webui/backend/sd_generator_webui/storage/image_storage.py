"""
Image Storage - Pure filesystem repository for images.

This module provides storage adapter for image file operations (CRUD only).
NO business logic - just filesystem operations for image files.

Business logic (thumbnail generation, image processing) should be in services.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from sd_generator_webui.storage.base import Storage, FileMetadata


class ImageStorage(ABC):
    """
    Abstract storage interface for image file operations.

    This is a PURE filesystem repository - no business logic.
    Only CRUD operations for image files.
    """

    @abstractmethod
    def read_image_bytes(self, path: Path) -> bytes:
        """
        Read image file as bytes.

        Args:
            path: Path to image file

        Returns:
            Image file bytes

        Raises:
            FileNotFoundError: If image doesn't exist
        """
        pass

    @abstractmethod
    def write_image_bytes(self, path: Path, content: bytes) -> None:
        """
        Write bytes to image file.

        Args:
            path: Path to image file
            content: Image bytes to write
        """
        pass

    @abstractmethod
    def list_images(
        self,
        directory: Path,
        extensions: Optional[List[str]] = None
    ) -> List[Path]:
        """
        List all image files in directory.

        Args:
            directory: Directory to list
            extensions: List of image extensions (default: [".png", ".jpg", ".jpeg", ".webp"])

        Returns:
            List of image file paths (sorted by name)
        """
        pass

    @abstractmethod
    def image_exists(self, path: Path) -> bool:
        """
        Check if image file exists.

        Args:
            path: Path to image file

        Returns:
            True if exists and is file
        """
        pass

    @abstractmethod
    def get_image_metadata(self, path: Path) -> FileMetadata:
        """
        Get metadata for image file.

        Args:
            path: Path to image file

        Returns:
            FileMetadata object

        Raises:
            FileNotFoundError: If image doesn't exist
        """
        pass


class LocalImageStorage(ImageStorage):
    """
    Local filesystem implementation of ImageStorage.

    Pure filesystem operations - delegates to base Storage.
    """

    def __init__(self, storage: Optional[Storage] = None):
        """
        Initialize local image storage.

        Args:
            storage: Base storage adapter (defaults to LocalStorage if None)
        """
        if storage is None:
            from sd_generator_webui.storage.local_storage import LocalStorage
            storage = LocalStorage()

        self.storage = storage

    def read_image_bytes(self, path: Path) -> bytes:
        """
        Read image file as bytes (local filesystem).

        Args:
            path: Path to image file

        Returns:
            Image file bytes

        Raises:
            FileNotFoundError: If image doesn't exist
        """
        return self.storage.read_bytes(path)

    def write_image_bytes(self, path: Path, content: bytes) -> None:
        """
        Write bytes to image file (local filesystem).

        Args:
            path: Path to image file
            content: Image bytes to write
        """
        self.storage.write_bytes(path, content)

    def list_images(
        self,
        directory: Path,
        extensions: Optional[List[str]] = None
    ) -> List[Path]:
        """
        List all image files in directory (local filesystem).

        Args:
            directory: Directory to list
            extensions: List of image extensions (default: [".png", ".jpg", ".jpeg", ".webp"])

        Returns:
            List of image file paths (sorted by name)
        """
        if extensions is None:
            extensions = [".png", ".jpg", ".jpeg", ".webp"]

        if not self.storage.exists(directory):
            return []

        images = []
        for item in self.storage.list_dir(directory):
            if self.storage.is_file(item) and item.suffix.lower() in extensions:
                images.append(item)

        # Sort by filename
        return sorted(images)

    def image_exists(self, path: Path) -> bool:
        """
        Check if image file exists (local filesystem).

        Args:
            path: Path to image file

        Returns:
            True if exists and is file
        """
        return self.storage.exists(path) and self.storage.is_file(path)

    def get_image_metadata(self, path: Path) -> FileMetadata:
        """
        Get metadata for image file (local filesystem).

        Args:
            path: Path to image file

        Returns:
            FileMetadata object

        Raises:
            FileNotFoundError: If image doesn't exist
        """
        return self.storage.get_metadata(path)
