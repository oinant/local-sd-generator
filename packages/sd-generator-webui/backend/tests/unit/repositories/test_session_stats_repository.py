"""
Tests for SessionStatsRepository.

Tests CRUD operations, batch loading, and edge cases.
"""

from sd_generator_webui.repositories.session_stats_repository import SQLiteSessionStatsRepository
from sd_generator_webui.models_stats import SessionStats


class TestSessionStatsRepository:
    """Test suite for SessionStatsRepository."""

    def test_save_and_get(self, stats_repository: SQLiteSessionStatsRepository, sample_stats: SessionStats):
        """Test saving and retrieving stats."""
        # Save
        stats_repository.save(sample_stats)

        # Get
        retrieved = stats_repository.get(sample_stats.session_name)

        assert retrieved is not None
        assert retrieved.session_name == sample_stats.session_name
        assert retrieved.sd_model == sample_stats.sd_model
        assert retrieved.images_requested == sample_stats.images_requested
        assert retrieved.images_actual == sample_stats.images_actual
        assert retrieved.placeholders == sample_stats.placeholders
        assert retrieved.variations_summary == sample_stats.variations_summary

    def test_get_nonexistent(self, stats_repository: SQLiteSessionStatsRepository):
        """Test getting non-existent stats returns None."""
        result = stats_repository.get("nonexistent_session")
        assert result is None

    def test_save_upsert(self, stats_repository: SQLiteSessionStatsRepository, sample_stats: SessionStats):
        """Test that save() upserts (INSERT OR REPLACE)."""
        # Save once
        stats_repository.save(sample_stats)

        # Modify and save again
        sample_stats.images_actual = 100
        sample_stats.completion_percent = 1.0
        stats_repository.save(sample_stats)

        # Get and verify update
        retrieved = stats_repository.get(sample_stats.session_name)
        assert retrieved is not None
        assert retrieved.images_actual == 100
        assert retrieved.completion_percent == 1.0

    def test_delete(self, stats_repository: SQLiteSessionStatsRepository, sample_stats: SessionStats):
        """Test deleting stats."""
        # Save
        stats_repository.save(sample_stats)

        # Delete
        deleted = stats_repository.delete(sample_stats.session_name)
        assert deleted is True

        # Verify deleted
        retrieved = stats_repository.get(sample_stats.session_name)
        assert retrieved is None

    def test_delete_nonexistent(self, stats_repository: SQLiteSessionStatsRepository):
        """Test deleting non-existent stats returns False."""
        deleted = stats_repository.delete("nonexistent_session")
        assert deleted is False

    def test_get_batch(self, stats_repository: SQLiteSessionStatsRepository, sample_stats: SessionStats):
        """Test batch loading multiple stats (PERFORMANCE)."""
        # Create multiple stats
        stats1 = sample_stats
        stats_repository.save(stats1)

        stats2 = SessionStats(
            session_name="20251110_130000-second_session",
            images_requested=50,
            images_actual=50,
            stats_computed_at=stats1.stats_computed_at
        )
        stats_repository.save(stats2)

        stats3 = SessionStats(
            session_name="20251110_140000-third_session",
            images_requested=75,
            images_actual=70,
            stats_computed_at=stats1.stats_computed_at
        )
        stats_repository.save(stats3)

        # Batch get
        session_names = [stats1.session_name, stats2.session_name, stats3.session_name, "nonexistent"]
        batch_result = stats_repository.get_batch(session_names)

        # Verify
        assert len(batch_result) == 3  # nonexistent not included
        assert stats1.session_name in batch_result
        assert stats2.session_name in batch_result
        assert stats3.session_name in batch_result
        assert "nonexistent" not in batch_result

        # Verify data
        assert batch_result[stats1.session_name].images_requested == 100
        assert batch_result[stats2.session_name].images_requested == 50
        assert batch_result[stats3.session_name].images_actual == 70

    def test_get_batch_empty(self, stats_repository: SQLiteSessionStatsRepository):
        """Test batch loading with empty list."""
        result = stats_repository.get_batch([])
        assert result == {}

    def test_list_all(self, stats_repository: SQLiteSessionStatsRepository, sample_stats: SessionStats):
        """Test listing all stats."""
        # Save multiple
        stats1 = sample_stats
        stats_repository.save(stats1)

        stats2 = SessionStats(
            session_name="20251110_130000-second_session",
            images_requested=50,
            images_actual=50,
            stats_computed_at=stats1.stats_computed_at
        )
        stats_repository.save(stats2)

        # List all
        all_stats = stats_repository.list_all()

        assert len(all_stats) == 2
        assert all_stats[0].session_name in [stats1.session_name, stats2.session_name]
        assert all_stats[1].session_name in [stats1.session_name, stats2.session_name]

    def test_list_all_empty(self, stats_repository: SQLiteSessionStatsRepository):
        """Test listing all stats when empty."""
        all_stats = stats_repository.list_all()
        assert all_stats == []

    def test_placeholders_serialization(self, stats_repository: SQLiteSessionStatsRepository, sample_stats: SessionStats):
        """Test that placeholders (JSON array) are correctly serialized/deserialized."""
        # Save with placeholders
        stats_repository.save(sample_stats)

        # Retrieve and verify
        retrieved = stats_repository.get(sample_stats.session_name)
        assert retrieved is not None
        assert retrieved.placeholders == ["FacialExpression", "Angle"]
        assert retrieved.variations_summary == {"FacialExpression": 10, "Angle": 10}

    def test_null_fields(self, stats_repository: SQLiteSessionStatsRepository, sample_stats: SessionStats):
        """Test handling of NULL fields."""
        from datetime import datetime
        stats = SessionStats(
            session_name="minimal_session",
            images_requested=0,
            images_actual=0,
            stats_computed_at=datetime.now()
        )

        stats_repository.save(stats)

        retrieved = stats_repository.get("minimal_session")
        assert retrieved is not None
        assert retrieved.sd_model is None
        assert retrieved.placeholders is None
        assert retrieved.variations_summary is None
