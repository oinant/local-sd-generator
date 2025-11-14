"""Unit tests for ImageGenerator (TDD approach)."""

from pathlib import Path
from unittest.mock import Mock, MagicMock, call
import pytest

from sd_generator_cli.orchestrator.image_generator import ImageGenerator
from sd_generator_cli.orchestrator.session_config import SessionConfig
from sd_generator_cli.orchestrator.session_event_collector import SessionEventCollector
from sd_generator_cli.orchestrator.manifest_manager import ManifestManager
from sd_generator_cli.api.sdapi_client import PromptConfig
from sd_generator_cli.templating.models.config_models import PromptConfig as TemplatePromptConfig, GenerationConfig


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_events():
    """Mock SessionEventCollector."""
    return Mock(spec=SessionEventCollector)


@pytest.fixture
def mock_api_client():
    """Mock SDAPIClient."""
    client = MagicMock()
    # Mock successful image generation (returns API response dict)
    client.generate_image.return_value = {"images": ["base64data"], "info": "test"}
    return client


@pytest.fixture
def mock_manifest_manager():
    """Mock ManifestManager."""
    return Mock(spec=ManifestManager)


@pytest.fixture
def minimal_session_config(tmp_path):
    """Minimal SessionConfig for testing."""
    prompt_config = TemplatePromptConfig(
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
        api_url="http://localhost:7860"
    )


@pytest.fixture
def sample_prompt_configs():
    """Sample PromptConfig list."""
    return [
        PromptConfig(
            prompt="test prompt 1",
            negative_prompt="low quality",
            seed=42,
            filename="test_0000_seed-42.png",
            parameters={}
        ),
        PromptConfig(
            prompt="test prompt 2",
            negative_prompt="low quality",
            seed=43,
            filename="test_0001_seed-43.png",
            parameters={}
        ),
        PromptConfig(
            prompt="test prompt 3",
            negative_prompt="low quality",
            seed=44,
            filename="test_0002_seed-44.png",
            parameters={}
        )
    ]


@pytest.fixture
def sample_prompts():
    """Sample V2 prompt dicts (with variations)."""
    return [
        {
            "prompt": "test prompt 1",
            "negative_prompt": "low quality",
            "seed": 42,
            "variations": {"Hair": "blonde", "Eyes": "blue"}
        },
        {
            "prompt": "test prompt 2",
            "negative_prompt": "low quality",
            "seed": 43,
            "variations": {"Hair": "brunette", "Eyes": "green"}
        },
        {
            "prompt": "test prompt 3",
            "negative_prompt": "low quality",
            "seed": 44,
            "variations": {"Hair": "red", "Eyes": "blue"}
        }
    ]


@pytest.fixture
def generator(mock_api_client, mock_manifest_manager, mock_events, minimal_session_config):
    """ImageGenerator instance."""
    return ImageGenerator(
        api_client=mock_api_client,
        manifest_manager=mock_manifest_manager,
        events=mock_events,
        session_config=minimal_session_config
    )


# ============================================================================
# Test: generate_images
# ============================================================================


class TestGenerateImages:
    """Test image generation workflow."""

    def test_calls_api_generate_image_for_each_prompt(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Calls API generate_image for each prompt config."""
        success, total = generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should call generate_image once per prompt config
        assert mock_api_client.generate_image.call_count == len(sample_prompt_configs)
        # First call should be with first prompt config
        first_call = mock_api_client.generate_image.call_args_list[0]
        assert first_call[0][0] == sample_prompt_configs[0]

    def test_updates_manifest_after_each_success(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_manifest_manager
    ):
        """Updates manifest incrementally after each successful generation."""
        generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should call update_incremental once per successful image
        assert mock_manifest_manager.update_incremental.call_count == len(sample_prompt_configs)

    def test_returns_success_and_total_counts(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Returns success and total counts."""
        # All generations succeed by default
        success, total = generator.generate_images(sample_prompt_configs, sample_prompts)

        assert success == len(sample_prompt_configs)
        assert total == len(sample_prompt_configs)

    def test_emits_generation_start_event(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_events
    ):
        """Emits IMAGE_GENERATION_START event."""
        generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should emit start event with count
        start_calls = [call for call in mock_events.emit.call_args_list if "START" in str(call)]
        assert len(start_calls) > 0

    def test_emits_generation_complete_event(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_events,
        mock_api_client
    ):
        """Emits IMAGE_GENERATION_COMPLETE event with counts."""
        generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should emit complete event with success/total counts
        complete_calls = [call for call in mock_events.emit.call_args_list if "COMPLETE" in str(call)]
        assert len(complete_calls) > 0


# ============================================================================
# Test: Manifest integration
# ============================================================================


class TestManifestCallbackIntegration:
    """Test manifest update integration."""

    def test_callback_updates_manifest_on_success(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_manifest_manager
    ):
        """Updates manifest when image generation succeeds."""
        generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should call manifest_manager.update_incremental for each success
        assert mock_manifest_manager.update_incremental.call_count == len(sample_prompt_configs)

        # Check first call args
        first_call = mock_manifest_manager.update_incremental.call_args_list[0]
        assert first_call[1]['idx'] == 0
        assert first_call[1]['filename'] == "test_0000_seed-42.png"

    def test_callback_skips_manifest_update_on_failure(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client,
        mock_manifest_manager
    ):
        """Skips manifest update when image generation fails."""
        # Mock API to fail on all calls
        mock_api_client.generate_image.side_effect = Exception("API error")

        generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should NOT call manifest_manager.update_incremental
        mock_manifest_manager.update_incremental.assert_not_called()

    def test_callback_passes_prompt_dict_to_manifest(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_manifest_manager
    ):
        """Passes original prompt dict (with variations) to manifest."""
        generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should pass prompt dict with variations (check second call)
        second_call = mock_manifest_manager.update_incremental.call_args_list[1]
        prompt_dict = second_call[1]['prompt_dict']
        assert prompt_dict['variations'] == {"Hair": "brunette", "Eyes": "green"}


# ============================================================================
# Test: Edge cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_empty_prompt_configs(
        self,
        generator,
        mock_api_client,
        mock_events
    ):
        """Handles empty prompt configs list."""
        success, total = generator.generate_images([], [])

        # Should not call API (no prompts)
        mock_api_client.generate_image.assert_not_called()
        # Should emit start/complete events
        assert mock_events.emit.call_count >= 2
        assert success == 0
        assert total == 0

    def test_handles_api_failure_gracefully(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Handles API failure (all images fail)."""
        # Mock API to fail on all calls
        mock_api_client.generate_image.side_effect = Exception("API error")

        success, total = generator.generate_images(sample_prompt_configs, sample_prompts)

        assert success == 0
        assert total == len(sample_prompt_configs)

    def test_handles_partial_success(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Handles partial success (some images fail)."""
        # Mock API to fail on second call only
        mock_api_client.generate_image.side_effect = [
            {"images": ["data1"]},  # Success
            Exception("API error"),  # Fail
            {"images": ["data3"]}   # Success
        ]

        success, total = generator.generate_images(sample_prompt_configs, sample_prompts)

        assert success == 2
        assert total == 3

    def test_delay_between_images_is_applied(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Applies delay between image generations."""
        # This test just verifies the loop completes
        # (actual time.sleep is mocked in real tests if needed)
        success, total = generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should call API for each prompt
        assert mock_api_client.generate_image.call_count == len(sample_prompt_configs)
        assert success == len(sample_prompt_configs)
        assert total == len(sample_prompt_configs)
