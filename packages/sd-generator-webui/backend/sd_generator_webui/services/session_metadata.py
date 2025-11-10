"""
Session Metadata Service - Business logic for session ratings and metadata.

Handles:
- User ratings (like/dislike)
- Flags (is_test, is_complete, is_favorite)
- Tags
- User notes
- Auto-extracted metadata
- Orchestration with repository for persistence

This service contains ONLY business logic. All data access is delegated
to the SessionMetadataRepository following the Repository Pattern.
"""

from pathlib import Path
from typing import List, Optional

from sd_generator_webui.models import SessionMetadata, SessionMetadataUpdate
from sd_generator_webui.repositories.session_metadata_repository import (
    SessionMetadataRepository,
    SQLiteSessionMetadataRepository
)


class SessionMetadataService:
    """
    Service for managing session metadata.

    This service contains ONLY business logic and orchestration.
    All data access is delegated to SessionMetadataRepository.
    """

    def __init__(self, repository: Optional[SessionMetadataRepository] = None):
        """
        Initialize the service.

        Args:
            repository: SessionMetadataRepository implementation. Defaults to SQLiteSessionMetadataRepository
        """
        if repository is None:
            repository = SQLiteSessionMetadataRepository()

        self.repository = repository

    def get_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """
        Get metadata for a session.

        Args:
            session_id: Session folder name

        Returns:
            SessionMetadata if found, None otherwise
        """
        return self.repository.get(session_id)

    def upsert_metadata(
        self,
        session_id: str,
        session_path: str,
        update: SessionMetadataUpdate
    ) -> SessionMetadata:
        """
        Create or update metadata for a session.

        Args:
            session_id: Session folder name
            session_path: Full path to session folder
            update: Update data

        Returns:
            Updated SessionMetadata
        """
        return self.repository.upsert(session_id, session_path, update)

    def list_all_metadata(self) -> List[SessionMetadata]:
        """
        List all session metadata.

        Returns:
            List of SessionMetadata objects
        """
        return self.repository.list_all()

    def delete_metadata(self, session_id: str) -> bool:
        """
        Delete metadata for a session.

        Args:
            session_id: Session folder name

        Returns:
            True if deleted, False if not found
        """
        return self.repository.delete(session_id)
