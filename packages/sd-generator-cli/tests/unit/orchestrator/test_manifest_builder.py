"""Unit tests for ManifestBuilder (TDD approach)."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest

from sd_generator_cli.orchestrator.manifest_builder import ManifestBuilder
from sd_generator_cli.orchestrator.session_config import SessionConfig
from sd_generator_cli.orchestrator.session_event_collector import SessionEventCollector
from sd_generator_cli.templating.models.config_models import PromptConfig, GenerationConfig
from sd_generator_cli.api.sdapi_client import SDAPIClient


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_api_client():
    """Mock SDAPIClient."""
    client = Mock(spec=SDAPIClient)
    client.get_model_checkpoint.return_value = "model_xyz.safetensors"
    return client


@pytest.fixture
def mock_events():
    """Mock SessionEventCollector."""
    return Mock(spec=SessionEventCollector)


@pytest.fixture
def builder(mock_api_client, mock_events):
    """ManifestBuilder instance with mocked dependencies."""
    return ManifestBuilder(mock_api_client, mock_events)


@pytest.fixture
def minimal_session_config(tmp_path):
    """Minimal SessionConfig for testing."""
    prompt_config = PromptConfig(
        version="2.0",
        source_file=Path("test.yaml"),
        name="test",
        prompt="test prompt",
        generation=GenerationConfig(mode="combinatorial", seed_mode="fixed", seed=42, max_images=10)
    )
    return SessionConfig(
        session_name="test_session",
        output_dir=tmp_path,
        template_path=Path("test.yaml"),
        prompt_config=prompt_config,
        total_images=10,
        generation_mode="combinatorial",
        seed_mode="fixed",
        base_seed=42,
        api_url="http://localhost:7860",
        fixed_placeholders={"Hair": "blue"},
        theme_name="cyberpunk",
        style="default"
    )


@pytest.fixture
def minimal_prompt_config():
    """Minimal PromptConfig for testing."""
    return PromptConfig(
        version="2.0",
        source_file=Path("test.yaml"),
        name="test",
        prompt="test prompt {Placeholder}",
        generation=GenerationConfig(mode="combinatorial", seed_mode="fixed", seed=42, max_images=10)
    )


@pytest.fixture
def mock_context():
    """Mock ResolvedContext."""
    context = MagicMock()
    context.imports = {
        "Hair": {"key1": "blonde", "key2": "brunette", "key3": "red"},
        "Eyes": {"key1": "blue", "key2": "green"}
    }
    return context


@pytest.fixture
def mock_resolved_config():
    """Mock ResolvedConfig."""
    config = MagicMock()
    config.template = "a person with {Hair} hair and {Eyes} eyes"
    config.negative_prompt = "low quality"
    config.parameters = {}
    config.generation = MagicMock()
    config.generation.seed_list = None
    return config


@pytest.fixture
def sample_prompts():
    """Sample generated prompts."""
    return [
        {
            "prompt": "a person with blonde hair and blue eyes",
            "variations": {"Hair": "blonde", "Eyes": "blue"},
            "parameters": {
                "steps": 20,
                "cfg_scale": 7.0
            }
        },
        {
            "prompt": "a person with brunette hair and green eyes",
            "variations": {"Hair": "brunette", "Eyes": "green"},
            "parameters": {
                "steps": 20,
                "cfg_scale": 7.0
            }
        }
    ]


@pytest.fixture
def sample_stats():
    """Sample prompt generation stats."""
    return {
        "total_combinations": 6,
        "total_placeholders": 2,
        "variations_count": 5
    }


# ============================================================================
# Test: fetch_runtime_info
# ============================================================================


class TestFetchRuntimeInfo:
    """Test runtime info fetching from API."""

    def test_success_returns_checkpoint_name(self, builder, mock_api_client):
        """Successful API call returns checkpoint name."""
        runtime_info = builder.fetch_runtime_info()

        assert runtime_info == {"sd_model_checkpoint": "model_xyz.safetensors"}
        mock_api_client.get_model_checkpoint.assert_called_once()

    def test_api_failure_returns_unknown_and_emits_warning(self, builder, mock_api_client, mock_events):
        """API failure returns 'unknown' and emits WARNING event."""
        mock_api_client.get_model_checkpoint.side_effect = Exception("API error")

        runtime_info = builder.fetch_runtime_info()

        assert runtime_info == {"sd_model_checkpoint": "unknown"}
        # Should emit WARNING event
        mock_events.emit.assert_called_once()
        call_args = mock_events.emit.call_args
        assert "WARNING" in str(call_args)


# ============================================================================
# Test: extract_variations
# ============================================================================


class TestExtractVariations:
    """Test variations extraction from context and prompts."""

    def test_extracts_available_and_used_values(
        self,
        builder,
        mock_context,
        mock_resolved_config,
        sample_prompts
    ):
        """Extracts both available (pool) and used (actual) values."""
        variations_map = builder.extract_variations(
            context=mock_context,
            resolved_config=mock_resolved_config,
            prompts=sample_prompts
        )

        # Should have both Hair and Eyes
        assert "Hair" in variations_map
        assert "Eyes" in variations_map

        # Hair: 3 available, 2 used
        assert variations_map["Hair"]["count"] == 3
        assert set(variations_map["Hair"]["available"]) == {"blonde", "brunette", "red"}
        assert set(variations_map["Hair"]["used"]) == {"blonde", "brunette"}

        # Eyes: 2 available, 2 used
        assert variations_map["Eyes"]["count"] == 2
        assert set(variations_map["Eyes"]["available"]) == {"blue", "green"}
        assert set(variations_map["Eyes"]["used"]) == {"blue", "green"}

    def test_ignores_placeholders_not_in_template(
        self,
        builder,
        mock_context,
        mock_resolved_config,
        sample_prompts
    ):
        """Ignores placeholders that don't appear in template."""
        # Add a placeholder that's not in template
        mock_context.imports["UnusedPlaceholder"] = {"key1": "value1"}

        variations_map = builder.extract_variations(
            context=mock_context,
            resolved_config=mock_resolved_config,
            prompts=sample_prompts
        )

        # Should NOT include UnusedPlaceholder
        assert "UnusedPlaceholder" not in variations_map

    def test_handles_controlnet_image_placeholders(self, builder, mock_context, sample_prompts):
        """Handles placeholders in ControlNet image variations."""
        # Mock resolved_config with ControlNet
        config = MagicMock()
        config.template = "a person"
        config.negative_prompt = ""
        config.parameters = {
            "controlnet": MagicMock()
        }

        # Mock ControlNet unit with image dict
        unit = MagicMock()
        unit.image = {"PoseImage": "some_path"}
        config.parameters["controlnet"].units = [unit]

        # Add PoseImage to context
        mock_context.imports["PoseImage"] = {"key1": "pose1.png", "key2": "pose2.png"}

        variations_map = builder.extract_variations(
            context=mock_context,
            resolved_config=config,
            prompts=[]
        )

        # Should include PoseImage from ControlNet
        assert "PoseImage" in variations_map
        assert variations_map["PoseImage"]["count"] == 2


# ============================================================================
# Test: build_generation_params
# ============================================================================


class TestBuildGenerationParams:
    """Test generation parameters building."""

    def test_builds_params_with_all_fields(
        self,
        builder,
        minimal_prompt_config,
        mock_resolved_config,
        sample_prompts,
        sample_stats
    ):
        """Builds generation params with all standard fields."""
        params = builder.build_generation_params(
            prompt_config=minimal_prompt_config,
            resolved_config=mock_resolved_config,
            prompts=sample_prompts,
            stats=sample_stats
        )

        assert params["mode"] == "combinatorial"
        assert params["seed_mode"] == "fixed"
        assert params["base_seed"] == 42
        assert params["num_images"] == 2
        assert params["total_combinations"] == 6

    def test_handles_seed_minus_one_as_none(
        self,
        builder,
        mock_resolved_config,
        sample_prompts,
        sample_stats
    ):
        """Converts seed=-1 to base_seed=None."""
        prompt_config = PromptConfig(
            version="2.0",
            source_file=Path("test.yaml"),
            name="test",
            prompt="test",
            generation=GenerationConfig(mode="random", seed_mode="random", seed=-1, max_images=10)
        )

        params = builder.build_generation_params(
            prompt_config=prompt_config,
            resolved_config=mock_resolved_config,
            prompts=sample_prompts,
            stats=sample_stats
        )

        assert params["base_seed"] is None
        assert params["seed_mode"] == "random"

    def test_includes_seed_list_when_present(
        self,
        builder,
        minimal_prompt_config,
        mock_resolved_config,
        sample_prompts,
        sample_stats
    ):
        """Includes seed_list in params when present (seed-sweep mode)."""
        mock_resolved_config.generation.seed_list = [100, 200, 300]

        params = builder.build_generation_params(
            prompt_config=minimal_prompt_config,
            resolved_config=mock_resolved_config,
            prompts=sample_prompts,
            stats=sample_stats
        )

        assert "seed_list" in params
        assert params["seed_list"] == [100, 200, 300]


# ============================================================================
# Test: build_api_params
# ============================================================================


class TestBuildAPIParams:
    """Test API parameters building."""

    def test_extracts_params_from_first_prompt(self, builder, sample_prompts):
        """Extracts parameters from first prompt."""
        api_params = builder.build_api_params(sample_prompts)

        assert api_params["steps"] == 20
        assert api_params["cfg_scale"] == 7.0

    def test_converts_extension_configs_to_dicts(self, builder):
        """Converts ADetailer and ControlNet configs to dicts."""
        # Mock prompt with extension configs
        mock_adetailer = MagicMock()
        mock_adetailer.to_dict.return_value = {"enabled": True}

        mock_controlnet = MagicMock()
        mock_controlnet.to_dict.return_value = {"units": []}

        prompts = [{
            "parameters": {
                "steps": 20,
                "adetailer": mock_adetailer,
                "controlnet": mock_controlnet
            }
        }]

        api_params = builder.build_api_params(prompts)

        assert api_params["adetailer"] == {"enabled": True}
        assert api_params["controlnet"] == {"units": []}

    def test_empty_prompts_returns_empty_dict(self, builder):
        """Empty prompts list returns empty dict."""
        api_params = builder.build_api_params([])

        assert api_params == {}


# ============================================================================
# Test: build_snapshot (Integration)
# ============================================================================


class TestBuildSnapshot:
    """Test complete snapshot building (integration test)."""

    def test_builds_complete_snapshot_with_all_sections(
        self,
        builder,
        minimal_session_config,
        minimal_prompt_config,
        mock_context,
        mock_resolved_config,
        sample_prompts,
        sample_stats
    ):
        """Builds complete snapshot with all required sections."""
        snapshot = builder.build_snapshot(
            session_config=minimal_session_config,
            context=mock_context,
            resolved_config=mock_resolved_config,
            prompts=sample_prompts,
            stats=sample_stats
        )

        # Check structure
        assert snapshot["version"] == "2.0"
        assert "timestamp" in snapshot
        assert "runtime_info" in snapshot
        assert "resolved_template" in snapshot
        assert "generation_params" in snapshot
        assert "api_params" in snapshot
        assert "variations" in snapshot
        assert "fixed_placeholders" in snapshot
        assert "theme_name" in snapshot
        assert "style" in snapshot

        # Check values from session_config
        assert snapshot["fixed_placeholders"] == {"Hair": "blue"}
        assert snapshot["theme_name"] == "cyberpunk"
        assert snapshot["style"] == "default"

        # Check resolved template
        assert snapshot["resolved_template"]["prompt"] == mock_resolved_config.template
        assert snapshot["resolved_template"]["negative"] == "low quality"

    def test_timestamp_is_iso_format(
        self,
        builder,
        minimal_session_config,
        minimal_prompt_config,
        mock_context,
        mock_resolved_config,
        sample_prompts,
        sample_stats
    ):
        """Timestamp is in ISO format."""
        snapshot = builder.build_snapshot(
            session_config=minimal_session_config,
            context=mock_context,
            resolved_config=mock_resolved_config,
            prompts=sample_prompts,
            stats=sample_stats
        )

        # Should be parseable as ISO format
        timestamp_str = snapshot["timestamp"]
        parsed = datetime.fromisoformat(timestamp_str)
        assert isinstance(parsed, datetime)
