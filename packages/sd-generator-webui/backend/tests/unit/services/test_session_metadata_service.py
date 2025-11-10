"""
Tests for SessionMetadataService with mocked repository.

Tests that service correctly delegates to repository.
"""

from unittest.mock import Mock

import pytest

from sd_generator_webui.services.session_metadata import SessionMetadataService
from sd_generator_webui.models import SessionMetadataUpdate, UserRating


class TestSessionMetadataService:
    """Test suite for SessionMetadataService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create service with mocked repository."""
        return SessionMetadataService(repository=mock_repository)

    def test_get_metadata_delegates_to_repository(self, service, mock_repository, sample_metadata):
        """Test get_metadata delegates to repository."""
        mock_repository.get.return_value = sample_metadata

        result = service.get_metadata("test_session")

        mock_repository.get.assert_called_once_with("test_session")
        assert result == sample_metadata

    def test_upsert_metadata_delegates_to_repository(self, service, mock_repository, sample_metadata):
        """Test upsert_metadata delegates to repository."""
        update = SessionMetadataUpdate(is_favorite=True)
        mock_repository.upsert.return_value = sample_metadata

        result = service.upsert_metadata(
            session_id="test_session",
            session_path="/path",
            update=update
        )

        mock_repository.upsert.assert_called_once_with("test_session", "/path", update)
        assert result == sample_metadata

    def test_list_all_metadata_delegates_to_repository(self, service, mock_repository, sample_metadata):
        """Test list_all_metadata delegates to repository."""
        mock_repository.list_all.return_value = [sample_metadata]

        result = service.list_all_metadata()

        mock_repository.list_all.assert_called_once()
        assert result == [sample_metadata]

    def test_delete_metadata_delegates_to_repository(self, service, mock_repository):
        """Test delete_metadata delegates to repository."""
        mock_repository.delete.return_value = True

        result = service.delete_metadata("test_session")

        mock_repository.delete.assert_called_once_with("test_session")
        assert result is True

    def test_service_uses_default_repository_if_none_provided(self):
        """Test service creates default SQLite repository if none provided."""
        # This would fail if repository initialization is broken
        service = SessionMetadataService()
        assert service.repository is not None
