"""
Unit tests for SessionStatsService.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from sd_generator_webui.services.session_stats import SessionStats, SessionStatsService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def service(temp_db):
    """Create a SessionStatsService instance with temp database."""
    return SessionStatsService(db_path=temp_db)


@pytest.fixture
def sample_manifest():
    """Sample manifest.json data."""
    return {
        "sd_model": "animagine-xl-3.1",
        "sampler_name": "Euler a",
        "scheduler": "automatic",
        "cfg_scale": 7.0,
        "steps": 20,
        "width": 1024,
        "height": 1024,
        "template_config": {
            "variations": {
                "HairColor": ["red", "blue", "blonde"],
                "Pose": ["standing", "sitting"]
            }
        },
        "images": [
            {"seed": 42, "prompt": "masterpiece, best quality, 1girl"},
            {"seed": 43, "prompt": "masterpiece, best quality, 1girl"},
            {"seed": 44, "prompt": "masterpiece, best quality, 1girl"}
        ]
    }


def test_database_initialization(service):
    """Test that database and table are created correctly."""
    # Check that session_stats table exists
    import sqlite3
    with sqlite3.connect(service.db_path) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='session_stats'"
        )
        assert cursor.fetchone() is not None


def test_compute_stats_with_manifest(service, sample_manifest, tmp_path):
    """Test computing stats from a valid manifest.json."""
    session_path = tmp_path / "test_session"
    session_path.mkdir()

    # Write manifest
    manifest_path = session_path / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(sample_manifest, f)

    # Create 3 PNG files
    for i in range(3):
        (session_path / f"image_{i}.png").touch()

    # Compute stats
    stats = service.compute_stats(session_path)

    # Assertions
    assert stats.session_name == "test_session"
    assert stats.sd_model == "animagine-xl-3.1"
    assert stats.sampler_name == "Euler a"
    assert stats.cfg_scale == 7.0
    assert stats.steps == 20
    assert stats.width == 1024
    assert stats.height == 1024
    assert stats.images_requested == 3
    assert stats.images_actual == 3
    assert stats.completion_percent == 1.0
    assert stats.placeholders_count == 2
    assert stats.placeholders == ["HairColor", "Pose"]
    assert stats.variations_theoretical == 6  # 3 * 2
    assert stats.variations_summary == {"HairColor": 3, "Pose": 2}
    assert stats.session_type == "seed-sweep"
    assert stats.is_seed_sweep is True
    assert stats.seed_min == 42
    assert stats.seed_max == 44
    assert stats.seed_mode == "progressive"


def test_compute_stats_without_manifest(service, tmp_path):
    """Test computing stats when manifest.json is missing."""
    session_path = tmp_path / "no_manifest_session"
    session_path.mkdir()

    # Create 5 PNG files
    for i in range(5):
        (session_path / f"image_{i}.png").touch()

    # Compute stats
    stats = service.compute_stats(session_path)

    # Assertions
    assert stats.session_name == "no_manifest_session"
    assert stats.sd_model is None
    assert stats.images_requested == 0
    assert stats.images_actual == 5
    assert stats.completion_percent == 0.0
    assert stats.placeholders_count == 0


def test_detect_seed_sweep_progressive_seeds(service, sample_manifest, tmp_path):
    """Test seed-sweep detection with progressive seeds."""
    session_path = tmp_path / "seed_sweep_session"
    session_path.mkdir()

    # Manifest with progressive seeds and identical prompts
    manifest_path = session_path / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(sample_manifest, f)

    stats = service.compute_stats(session_path)

    assert stats.session_type == "seed-sweep"
    assert stats.is_seed_sweep is True


def test_detect_normal_session_random_seeds(service, tmp_path):
    """Test normal session detection with random seeds."""
    session_path = tmp_path / "normal_session"
    session_path.mkdir()

    # Manifest with random seeds
    manifest = {
        "images": [
            {"seed": 100, "prompt": "test1"},
            {"seed": 250, "prompt": "test2"},
            {"seed": 42, "prompt": "test3"}
        ]
    }

    manifest_path = session_path / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    stats = service.compute_stats(session_path)

    assert stats.session_type == "normal"
    assert stats.is_seed_sweep is False


def test_save_and_retrieve_stats(service, tmp_path):
    """Test saving stats to database and retrieving them."""
    session_path = tmp_path / "save_test_session"
    session_path.mkdir()
    (session_path / "manifest.json").write_text("{}")

    # Compute and save
    stats = service.compute_and_save(session_path)

    # Retrieve
    retrieved = service.get_stats("save_test_session")

    assert retrieved is not None
    assert retrieved.session_name == stats.session_name
    assert retrieved.images_actual == stats.images_actual


def test_batch_compute_all(service, tmp_path, sample_manifest):
    """Test batch computing stats for multiple sessions."""
    sessions_root = tmp_path / "sessions"
    sessions_root.mkdir()

    # Create 3 sessions
    for i in range(3):
        session_path = sessions_root / f"session_{i}"
        session_path.mkdir()

        manifest_path = session_path / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(sample_manifest, f)

        # Create some images
        for j in range(2):
            (session_path / f"image_{j}.png").touch()

    # Batch compute
    count = service.batch_compute_all(sessions_root)

    assert count == 3

    # Verify all sessions have stats
    all_stats = service.list_all_stats()
    assert len(all_stats) == 3


def test_completion_percentage_calculation(service, tmp_path):
    """Test completion percentage is calculated correctly."""
    session_path = tmp_path / "completion_test"
    session_path.mkdir()

    # Manifest with 10 requested images
    manifest = {
        "images": [{"seed": i, "prompt": "test"} for i in range(10)]
    }

    manifest_path = session_path / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    # Create only 8 PNG files (80% complete)
    for i in range(8):
        (session_path / f"image_{i}.png").touch()

    stats = service.compute_stats(session_path)

    assert stats.images_requested == 10
    assert stats.images_actual == 8
    assert stats.completion_percent == 0.8


def test_detect_seed_mode_fixed(service):
    """Test seed mode detection for fixed seeds."""
    seeds = [42, 42, 42, 42]
    mode = service._detect_seed_mode(seeds)
    assert mode == "fixed"


def test_detect_seed_mode_progressive(service):
    """Test seed mode detection for progressive seeds."""
    seeds = [100, 101, 102, 103, 104]
    mode = service._detect_seed_mode(seeds)
    assert mode == "progressive"


def test_detect_seed_mode_random(service):
    """Test seed mode detection for random seeds."""
    seeds = [42, 100, 250, 7, 999]
    mode = service._detect_seed_mode(seeds)
    assert mode == "random"
