"""
Tests for SessionStatsService with mocked repository.

Tests that service correctly delegates to repository and focuses on business logic.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

from sd_generator_webui.services.session_stats import SessionStatsService
from sd_generator_webui.models_stats import SessionStats


class TestSessionStatsService:
    """Test suite for SessionStatsService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return Mock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create service with mocked repository."""
        return SessionStatsService(repository=mock_repository)

    def test_get_stats_delegates_to_repository(self, service, mock_repository, sample_stats):
        """Test get_stats delegates to repository."""
        mock_repository.get.return_value = sample_stats

        result = service.get_stats("test_session")

        mock_repository.get.assert_called_once_with("test_session")
        assert result == sample_stats

    def test_save_stats_delegates_to_repository(self, service, mock_repository, sample_stats):
        """Test save_stats delegates to repository."""
        service.save_stats(sample_stats)

        mock_repository.save.assert_called_once_with(sample_stats)

    def test_list_all_stats_delegates_to_repository(self, service, mock_repository, sample_stats):
        """Test list_all_stats delegates to repository."""
        mock_repository.list_all.return_value = [sample_stats]

        result = service.list_all_stats()

        mock_repository.list_all.assert_called_once()
        assert result == [sample_stats]

    def test_get_stats_batch_delegates_to_repository(self, service, mock_repository, sample_stats):
        """Test get_stats_batch delegates to repository (PERFORMANCE)."""
        session_names = ["session1", "session2"]
        mock_repository.get_batch.return_value = {"session1": sample_stats}

        result = service.get_stats_batch(session_names)

        mock_repository.get_batch.assert_called_once_with(session_names)
        assert result == {"session1": sample_stats}

    def test_compute_and_save_calls_both_methods(self, service, mock_repository, tmp_path):
        """Test compute_and_save computes and saves."""
        # Create minimal manifest
        session_path = tmp_path / "test_session"
        session_path.mkdir()

        manifest_path = session_path / "manifest.json"
        manifest_path.write_text('{"snapshot": {}, "images": []}')

        # Call compute_and_save
        result = service.compute_and_save(session_path)

        # Verify save was called with computed stats
        mock_repository.save.assert_called_once()
        saved_stats = mock_repository.save.call_args[0][0]
        assert saved_stats.session_name == "test_session"
        assert result.session_name == "test_session"

    def test_compute_stats_handles_missing_manifest(self, service, tmp_path):
        """Test compute_stats handles missing manifest gracefully."""
        session_path = tmp_path / "test_session"
        session_path.mkdir()

        # No manifest.json - should still compute basic stats
        stats = service.compute_stats(session_path)

        assert stats.session_name == "test_session"
        assert stats.images_actual == 0
        assert stats.images_requested == 0

    def test_service_uses_default_repository_if_none_provided(self):
        """Test service creates default SQLite repository if none provided."""
        # This would fail if repository initialization is broken
        service = SessionStatsService()
        assert service.repository is not None

    def test_detect_session_type_normal(self, service):
        """Test _detect_session_type identifies normal sessions."""
        manifest = {
            "images": [
                {"seed": 42, "prompt": "portrait of cat"},
                {"seed": 43, "prompt": "portrait of dog"},
            ]
        }

        session_type, is_seed_sweep = service._detect_session_type(manifest)

        assert session_type == "normal"
        assert is_seed_sweep is False

    def test_detect_session_type_seed_sweep(self, service):
        """Test _detect_session_type identifies seed-sweep sessions."""
        manifest = {
            "images": [
                {"seed": 42, "prompt": "portrait of cat"},
                {"seed": 43, "prompt": "portrait of cat"},  # Same prompt
                {"seed": 44, "prompt": "portrait of cat"},  # Progressive seeds
            ]
        }

        session_type, is_seed_sweep = service._detect_session_type(manifest)

        assert session_type == "seed-sweep"
        assert is_seed_sweep is True

    def test_detect_seed_mode_fixed(self, service):
        """Test _detect_seed_mode identifies fixed seed."""
        seeds = [42, 42, 42, 42]

        seed_mode = service._detect_seed_mode(seeds)

        assert seed_mode == "fixed"

    def test_detect_seed_mode_progressive(self, service):
        """Test _detect_seed_mode identifies progressive seeds."""
        seeds = [42, 43, 44, 45]

        seed_mode = service._detect_seed_mode(seeds)

        assert seed_mode == "progressive"

    def test_detect_seed_mode_random(self, service):
        """Test _detect_seed_mode identifies random seeds."""
        seeds = [42, 100, 55, 200]

        seed_mode = service._detect_seed_mode(seeds)

        assert seed_mode == "random"

    def test_batch_compute_all_skips_existing(self, service, mock_repository, tmp_path):
        """Test batch_compute_all skips sessions with existing stats."""
        # Create test sessions
        session1 = tmp_path / "session1"
        session1.mkdir()
        (session1 / "manifest.json").write_text('{}')

        session2 = tmp_path / "session2"
        session2.mkdir()
        (session2 / "manifest.json").write_text('{}')

        # Mock: session1 has stats, session2 doesn't
        def mock_get_stats(name):
            if name == "session1":
                return Mock()  # Has stats
            return None  # No stats

        mock_repository.get.side_effect = mock_get_stats

        # Run batch compute (force_recompute=False)
        service.sessions_root = tmp_path
        count = service.batch_compute_all(tmp_path, force_recompute=False)

        # Should only process session2
        assert count == 1
        assert mock_repository.save.call_count == 1

    def test_batch_compute_all_force_recompute(self, service, mock_repository, tmp_path):
        """Test batch_compute_all with force_recompute processes all."""
        # Create test sessions
        session1 = tmp_path / "session1"
        session1.mkdir()
        (session1 / "manifest.json").write_text('{}')

        session2 = tmp_path / "session2"
        session2.mkdir()
        (session2 / "manifest.json").write_text('{}')

        # Mock: both sessions have stats
        mock_repository.get.return_value = Mock()

        # Run batch compute (force_recompute=True)
        service.sessions_root = tmp_path
        count = service.batch_compute_all(tmp_path, force_recompute=True)

        # Should process both
        assert count == 2
        assert mock_repository.save.call_count == 2
