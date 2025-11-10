"""
Session Storage - Filesystem operations for sessions.

This module provides storage adapter for session-related filesystem operations:
- Listing session folders
- Counting images in sessions
- Reading manifest.json files
- Checking session existence
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sd_generator_webui.storage.base import Storage, FileMetadata


class SessionStorage(ABC):
    """
    Abstract storage interface for session operations.

    This interface defines session-specific operations beyond basic Storage.
    Implementations can use local filesystem, S3, MinIO, etc.
    """

    @abstractmethod
    def list_sessions(self, root: Path) -> List[Path]:
        """
        List all session directories in root.

        Args:
            root: Root directory containing sessions

        Returns:
            List of session directory paths
        """
        pass

    @abstractmethod
    def count_images(self, session_path: Path, extensions: Optional[List[str]] = None) -> int:
        """
        Count images in a session.

        Args:
            session_path: Path to session directory
            extensions: List of image extensions (default: [".png", ".jpg", ".jpeg", ".webp"])

        Returns:
            Number of image files
        """
        pass

    @abstractmethod
    def list_images(
        self,
        session_path: Path,
        extensions: Optional[List[str]] = None
    ) -> List[Path]:
        """
        List all image files in a session.

        Args:
            session_path: Path to session directory
            extensions: List of image extensions (default: [".png", ".jpg", ".jpeg", ".webp"])

        Returns:
            List of image file paths (sorted by name)
        """
        pass

    @abstractmethod
    def read_manifest(self, session_path: Path) -> Optional[Dict]:
        """
        Read manifest.json from session.

        Args:
            session_path: Path to session directory

        Returns:
            Parsed manifest dict, or None if doesn't exist
        """
        pass

    @abstractmethod
    def session_exists(self, session_path: Path) -> bool:
        """
        Check if session directory exists.

        Args:
            session_path: Path to session directory

        Returns:
            True if exists and is directory
        """
        pass


class LocalSessionStorage(SessionStorage):
    """
    Local filesystem implementation of SessionStorage.

    This adapter uses pathlib for local filesystem operations.
    For S3/MinIO, implement S3SessionStorage with boto3.
    """

    def __init__(self, storage: Optional[Storage] = None):
        """
        Initialize local session storage.

        Args:
            storage: Base storage adapter (defaults to LocalStorage if None)
        """
        if storage is None:
            from sd_generator_webui.storage.local_storage import LocalStorage
            storage = LocalStorage()

        self.storage = storage

    def list_sessions(self, root: Path) -> List[Path]:
        """
        List all session directories in root (local filesystem).

        Args:
            root: Root directory containing sessions

        Returns:
            List of session directory paths
        """
        if not self.storage.exists(root):
            return []

        all_items = self.storage.list_dir(root)
        return [item for item in all_items if self.storage.is_dir(item)]

    def count_images(self, session_path: Path, extensions: Optional[List[str]] = None) -> int:
        """
        Count images in a session (local filesystem).

        Args:
            session_path: Path to session directory
            extensions: List of image extensions (default: [".png", ".jpg", ".jpeg", ".webp"])

        Returns:
            Number of image files
        """
        if extensions is None:
            extensions = [".png", ".jpg", ".jpeg", ".webp"]

        if not self.storage.exists(session_path):
            return 0

        count = 0
        for item in self.storage.list_dir(session_path):
            if self.storage.is_file(item) and item.suffix.lower() in extensions:
                count += 1

        return count

    def list_images(
        self,
        session_path: Path,
        extensions: Optional[List[str]] = None
    ) -> List[Path]:
        """
        List all image files in a session (local filesystem).

        Args:
            session_path: Path to session directory
            extensions: List of image extensions (default: [".png", ".jpg", ".jpeg", ".webp"])

        Returns:
            List of image file paths (sorted by name)
        """
        if extensions is None:
            extensions = [".png", ".jpg", ".jpeg", ".webp"]

        if not self.storage.exists(session_path):
            return []

        images = []
        for item in self.storage.list_dir(session_path):
            if self.storage.is_file(item) and item.suffix.lower() in extensions:
                images.append(item)

        # Sort by filename
        return sorted(images)

    def read_manifest(self, session_path: Path) -> Optional[Dict]:
        """
        Read manifest.json from session (local filesystem).

        Args:
            session_path: Path to session directory

        Returns:
            Parsed manifest dict, or None if doesn't exist
        """
        manifest_path = session_path / "manifest.json"

        if not self.storage.exists(manifest_path):
            return None

        try:
            content = self.storage.read_text(manifest_path)
            return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def session_exists(self, session_path: Path) -> bool:
        """
        Check if session directory exists (local filesystem).

        Args:
            session_path: Path to session directory

        Returns:
            True if exists and is directory
        """
        return self.storage.exists(session_path) and self.storage.is_dir(session_path)
