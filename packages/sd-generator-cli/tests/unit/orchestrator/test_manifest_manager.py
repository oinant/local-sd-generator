"""Unit tests for ManifestManager (TDD approach)."""

import json
from pathlib import Path
from unittest.mock import Mock
import pytest

from sd_generator_cli.orchestrator.manifest_manager import ManifestManager
from sd_generator_cli.orchestrator.session_event_collector import SessionEventCollector


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_events():
    """Mock SessionEventCollector."""
    return Mock(spec=SessionEventCollector)


@pytest.fixture
def manifest_path(tmp_path):
    """Path to test manifest file."""
    return tmp_path / "manifest.json"


@pytest.fixture
def manager(manifest_path, mock_events):
    """ManifestManager instance."""
    return ManifestManager(manifest_path, mock_events)


@pytest.fixture
def sample_snapshot():
    """Sample manifest snapshot."""
    return {
        "version": "2.0",
        "timestamp": "2025-11-12T10:00:00",
        "runtime_info": {"sd_model_checkpoint": "model.safetensors"},
        "resolved_template": {"prompt": "test prompt", "negative": "low quality"},
        "generation_params": {"mode": "combinatorial", "seed_mode": "fixed"},
        "api_params": {"steps": 20},
        "variations": {},
        "fixed_placeholders": {},
        "theme_name": None,
        "style": "default"
    }


@pytest.fixture
def sample_prompt_dict():
    """Sample prompt dict for update."""
    return {
        "prompt": "a beautiful landscape",
        "negative_prompt": "low quality",
        "seed": 42,
        "variations": {"Style": "realistic", "Weather": "sunny"}
    }


@pytest.fixture
def sample_api_response():
    """Sample API response with info JSON."""
    return {
        "info": json.dumps({
            "seed": 12345,
            "steps": 20
        })
    }


# ============================================================================
# Test: initialize
# ============================================================================


class TestInitialize:
    """Test manifest initialization."""

    def test_creates_manifest_with_ongoing_status(self, manager, manifest_path, sample_snapshot):
        """Creates manifest.json with 'ongoing' status."""
        manager.initialize(sample_snapshot)

        # File should exist
        assert manifest_path.exists()

        # Check structure
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert manifest["status"] == "ongoing"
        assert manifest["snapshot"] == sample_snapshot
        assert manifest["images"] == []

    def test_emits_manifest_created_event(self, manager, sample_snapshot, mock_events):
        """Emits MANIFEST_CREATED event."""
        manager.initialize(sample_snapshot)

        mock_events.emit.assert_called_once()
        call_args = mock_events.emit.call_args
        # Should emit MANIFEST_CREATED with path
        assert "MANIFEST_CREATED" in str(call_args)

    def test_overwrites_existing_manifest(self, manager, manifest_path, sample_snapshot):
        """Overwrites existing manifest if present."""
        # Create existing manifest
        existing = {"status": "completed", "snapshot": {}, "images": [{"filename": "old.png"}]}
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f)

        # Initialize with new snapshot
        manager.initialize(sample_snapshot)

        # Should be overwritten
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert manifest["status"] == "ongoing"
        assert manifest["images"] == []
        assert manifest["snapshot"] == sample_snapshot


# ============================================================================
# Test: update_incremental
# ============================================================================


class TestUpdateIncremental:
    """Test incremental manifest updates."""

    def test_adds_image_entry_to_manifest(
        self,
        manager,
        manifest_path,
        sample_snapshot,
        sample_prompt_dict
    ):
        """Adds new image entry to manifest."""
        # Initialize manifest
        manager.initialize(sample_snapshot)

        # Update with new image
        manager.update_incremental(
            idx=0,
            filename="image_001.png",
            prompt_dict=sample_prompt_dict,
            api_response=None
        )

        # Check manifest
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert len(manifest["images"]) == 1
        image = manifest["images"][0]
        assert image["filename"] == "image_001.png"
        assert image["seed"] == 42  # From prompt_dict
        assert image["prompt"] == "a beautiful landscape"
        assert image["negative_prompt"] == "low quality"
        assert image["applied_variations"] == {"Style": "realistic", "Weather": "sunny"}

    def test_extracts_seed_from_api_response(
        self,
        manager,
        manifest_path,
        sample_snapshot,
        sample_prompt_dict,
        sample_api_response
    ):
        """Extracts real seed from API response.info."""
        manager.initialize(sample_snapshot)

        # Update with API response containing real seed
        manager.update_incremental(
            idx=0,
            filename="image_001.png",
            prompt_dict=sample_prompt_dict,
            api_response=sample_api_response
        )

        # Check that real seed was extracted
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        image = manifest["images"][0]
        assert image["seed"] == 12345  # Real seed from API, not 42 from prompt_dict

    def test_handles_corrupted_manifest_gracefully(
        self,
        manager,
        manifest_path,
        sample_snapshot,
        sample_prompt_dict
    ):
        """Recreates manifest if corrupted."""
        # Initialize manifest
        manager.initialize(sample_snapshot)

        # Corrupt manifest
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write("INVALID JSON{{{")

        # Update should recreate manifest
        manager.update_incremental(
            idx=0,
            filename="image_001.png",
            prompt_dict=sample_prompt_dict,
            api_response=None
        )

        # Should have valid manifest now
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert "snapshot" in manifest
        assert len(manifest["images"]) == 1

    def test_multiple_incremental_updates(
        self,
        manager,
        manifest_path,
        sample_snapshot,
        sample_prompt_dict
    ):
        """Multiple updates accumulate in manifest."""
        manager.initialize(sample_snapshot)

        # Add 3 images
        for i in range(3):
            manager.update_incremental(
                idx=i,
                filename=f"image_{i:03d}.png",
                prompt_dict=sample_prompt_dict,
                api_response=None
            )

        # Check manifest
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert len(manifest["images"]) == 3
        assert manifest["images"][0]["filename"] == "image_000.png"
        assert manifest["images"][1]["filename"] == "image_001.png"
        assert manifest["images"][2]["filename"] == "image_002.png"

    def test_handles_missing_api_response_info(
        self,
        manager,
        manifest_path,
        sample_snapshot,
        sample_prompt_dict
    ):
        """Handles API response without 'info' field."""
        manager.initialize(sample_snapshot)

        # API response without 'info'
        api_response = {"other_field": "value"}

        manager.update_incremental(
            idx=0,
            filename="image_001.png",
            prompt_dict=sample_prompt_dict,
            api_response=api_response
        )

        # Should use seed from prompt_dict
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        image = manifest["images"][0]
        assert image["seed"] == 42  # Fallback to prompt_dict seed


# ============================================================================
# Test: finalize
# ============================================================================


class TestFinalize:
    """Test manifest finalization."""

    def test_updates_status_to_completed(self, manager, manifest_path, sample_snapshot):
        """Updates manifest status to 'completed'."""
        # Initialize manifest
        manager.initialize(sample_snapshot)
        assert manager.get_status() == "ongoing"

        # Finalize
        manager.finalize(status="completed")

        # Check status
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert manifest["status"] == "completed"

    def test_updates_status_to_aborted(self, manager, manifest_path, sample_snapshot):
        """Updates manifest status to 'aborted'."""
        manager.initialize(sample_snapshot)

        # Finalize with aborted status
        manager.finalize(status="aborted")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert manifest["status"] == "aborted"

    def test_emits_manifest_finalized_event(self, manager, sample_snapshot, mock_events):
        """Emits MANIFEST_FINALIZED event."""
        manager.initialize(sample_snapshot)

        # Clear previous calls
        mock_events.emit.reset_mock()

        manager.finalize(status="completed")

        # Should emit MANIFEST_FINALIZED
        mock_events.emit.assert_called_once()
        call_args = mock_events.emit.call_args
        assert "MANIFEST_FINALIZED" in str(call_args)

    def test_handles_missing_manifest_gracefully(self, manager, manifest_path, mock_events):
        """Handles missing manifest file gracefully."""
        # Don't initialize, try to finalize
        manager.finalize(status="completed")

        # Should emit WARNING event
        warning_calls = [call for call in mock_events.emit.call_args_list if "WARNING" in str(call)]
        assert len(warning_calls) > 0


# ============================================================================
# Test: get_status
# ============================================================================


class TestGetStatus:
    """Test status retrieval."""

    def test_returns_current_status(self, manager, manifest_path, sample_snapshot):
        """Returns current manifest status."""
        manager.initialize(sample_snapshot)

        assert manager.get_status() == "ongoing"

        manager.finalize(status="completed")

        assert manager.get_status() == "completed"

    def test_returns_none_if_manifest_missing(self, manager):
        """Returns None if manifest doesn't exist."""
        assert manager.get_status() is None

    def test_returns_none_if_manifest_corrupted(self, manager, manifest_path):
        """Returns None if manifest is corrupted."""
        # Create corrupted manifest
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write("INVALID JSON")

        assert manager.get_status() is None
