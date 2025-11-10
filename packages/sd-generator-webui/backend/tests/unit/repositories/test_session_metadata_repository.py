"""
Tests for SessionMetadataRepository.

Tests CRUD operations, upsert with partial updates, and edge cases.
"""

from datetime import datetime

from sd_generator_webui.repositories.session_metadata_repository import SQLiteSessionMetadataRepository
from sd_generator_webui.models import SessionMetadata, SessionMetadataUpdate, UserRating


class TestSessionMetadataRepository:
    """Test suite for SessionMetadataRepository."""

    def test_save_and_get(self, metadata_repository: SQLiteSessionMetadataRepository, sample_metadata: SessionMetadata):
        """Test saving and retrieving metadata."""
        # Save
        metadata_repository.save(sample_metadata)

        # Get
        retrieved = metadata_repository.get(sample_metadata.session_id)

        assert retrieved is not None
        assert retrieved.session_id == sample_metadata.session_id
        assert retrieved.session_path == sample_metadata.session_path
        assert retrieved.is_test == sample_metadata.is_test
        assert retrieved.is_favorite == sample_metadata.is_favorite
        assert retrieved.user_rating == sample_metadata.user_rating
        assert retrieved.user_note == sample_metadata.user_note
        assert retrieved.tags == sample_metadata.tags

    def test_get_nonexistent(self, metadata_repository: SQLiteSessionMetadataRepository):
        """Test getting non-existent metadata returns None."""
        result = metadata_repository.get("nonexistent_session")
        assert result is None

    def test_save_upsert(self, metadata_repository: SQLiteSessionMetadataRepository, sample_metadata: SessionMetadata):
        """Test that save() upserts (INSERT OR REPLACE)."""
        # Save once
        metadata_repository.save(sample_metadata)

        # Modify and save again
        sample_metadata.is_favorite = True
        sample_metadata.user_note = "Updated note"
        metadata_repository.save(sample_metadata)

        # Get and verify update
        retrieved = metadata_repository.get(sample_metadata.session_id)
        assert retrieved is not None
        assert retrieved.is_favorite is True
        assert retrieved.user_note == "Updated note"

    def test_delete(self, metadata_repository: SQLiteSessionMetadataRepository, sample_metadata: SessionMetadata):
        """Test deleting metadata."""
        # Save
        metadata_repository.save(sample_metadata)

        # Delete
        deleted = metadata_repository.delete(sample_metadata.session_id)
        assert deleted is True

        # Verify deleted
        retrieved = metadata_repository.get(sample_metadata.session_id)
        assert retrieved is None

    def test_delete_nonexistent(self, metadata_repository: SQLiteSessionMetadataRepository):
        """Test deleting non-existent metadata returns False."""
        deleted = metadata_repository.delete("nonexistent_session")
        assert deleted is False

    def test_list_all(self, metadata_repository: SQLiteSessionMetadataRepository, sample_metadata: SessionMetadata):
        """Test listing all metadata."""
        # Save multiple
        meta1 = sample_metadata
        metadata_repository.save(meta1)

        meta2 = SessionMetadata(
            session_id="second_session",
            session_path="/path/to/second",
            is_test=True,
            is_complete=False,
            is_favorite=False,
            user_rating=None,
            user_note=None,
            tags=[],
            auto_metadata=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        metadata_repository.save(meta2)

        # List all
        all_metadata = metadata_repository.list_all()

        assert len(all_metadata) == 2
        session_ids = [m.session_id for m in all_metadata]
        assert meta1.session_id in session_ids
        assert meta2.session_id in session_ids

    def test_list_all_empty(self, metadata_repository: SQLiteSessionMetadataRepository):
        """Test listing all metadata when empty."""
        all_metadata = metadata_repository.list_all()
        assert all_metadata == []

    def test_upsert_create_new(self, metadata_repository: SQLiteSessionMetadataRepository):
        """Test upsert creates new metadata if doesn't exist."""
        update = SessionMetadataUpdate(
            is_test=True,
            is_favorite=True,
            user_rating=UserRating.LIKE,
            user_note="Test note",
            tags=["test", "portrait"]
        )

        result = metadata_repository.upsert(
            session_id="new_session",
            session_path="/path/to/new",
            update=update
        )

        assert result is not None
        assert result.session_id == "new_session"
        assert result.is_test is True
        assert result.is_favorite is True
        assert result.user_rating == UserRating.LIKE
        assert result.user_note == "Test note"
        assert result.tags == ["test", "portrait"]

    def test_upsert_partial_update(self, metadata_repository: SQLiteSessionMetadataRepository, sample_metadata: SessionMetadata):
        """Test upsert updates only provided fields (partial update)."""
        # Save initial
        metadata_repository.save(sample_metadata)

        # Partial update (only is_favorite and tags)
        update = SessionMetadataUpdate(
            is_favorite=True,
            tags=["updated", "tags"]
        )

        result = metadata_repository.upsert(
            session_id=sample_metadata.session_id,
            session_path=sample_metadata.session_path,
            update=update
        )

        # Verify only specified fields changed
        assert result.is_favorite is True
        assert result.tags == ["updated", "tags"]
        # Other fields unchanged
        assert result.is_test == sample_metadata.is_test
        assert result.user_rating == sample_metadata.user_rating
        assert result.user_note == sample_metadata.user_note

    def test_upsert_updates_timestamp(self, metadata_repository: SQLiteSessionMetadataRepository, sample_metadata: SessionMetadata):
        """Test upsert updates updated_at timestamp."""
        # Save initial
        metadata_repository.save(sample_metadata)
        initial_updated_at = sample_metadata.updated_at

        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)

        # Update
        update = SessionMetadataUpdate(is_favorite=True)
        result = metadata_repository.upsert(
            session_id=sample_metadata.session_id,
            session_path=sample_metadata.session_path,
            update=update
        )

        assert result.updated_at > initial_updated_at

    def test_tags_serialization(self, metadata_repository: SQLiteSessionMetadataRepository, sample_metadata: SessionMetadata):
        """Test that tags (JSON array) are correctly serialized/deserialized."""
        # Save with tags
        metadata_repository.save(sample_metadata)

        # Retrieve and verify
        retrieved = metadata_repository.get(sample_metadata.session_id)
        assert retrieved is not None
        assert retrieved.tags == ["portrait", "cyberpunk"]

    def test_empty_tags(self, metadata_repository: SQLiteSessionMetadataRepository, sample_metadata: SessionMetadata):
        """Test handling empty tags list."""
        sample_metadata.tags = []
        metadata_repository.save(sample_metadata)

        retrieved = metadata_repository.get(sample_metadata.session_id)
        assert retrieved is not None
        assert retrieved.tags == []

    def test_null_fields(self, metadata_repository: SQLiteSessionMetadataRepository):
        """Test handling of NULL fields."""
        metadata = SessionMetadata(
            session_id="minimal_session",
            session_path="/path",
            is_test=False,
            is_complete=True,
            is_favorite=False,
            user_rating=None,
            user_note=None,
            tags=[],
            auto_metadata=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        metadata_repository.save(metadata)

        retrieved = metadata_repository.get("minimal_session")
        assert retrieved is not None
        assert retrieved.user_rating is None
        assert retrieved.user_note is None
        assert retrieved.auto_metadata is None
