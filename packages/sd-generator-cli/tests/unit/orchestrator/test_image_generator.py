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
    # Mock successful batch generation
    client.generate_batch.return_value = (3, 3)  # (success_count, total_count)
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

    def test_calls_api_generate_batch_with_prompt_configs(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Calls API generate_batch with prompt configs."""
        success, total = generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should call generate_batch with prompt_configs
        mock_api_client.generate_batch.assert_called_once()
        call_args = mock_api_client.generate_batch.call_args
        assert call_args[1]['prompt_configs'] == sample_prompt_configs

    def test_provides_callback_to_update_manifest(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Provides callback to update manifest incrementally."""
        generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should provide on_image_generated callback
        call_args = mock_api_client.generate_batch.call_args
        assert 'on_image_generated' in call_args[1]
        assert callable(call_args[1]['on_image_generated'])

    def test_returns_success_and_total_counts(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Returns success and total counts from API."""
        # Mock API returning 2 success out of 3 total
        mock_api_client.generate_batch.return_value = (2, 3)

        success, total = generator.generate_images(sample_prompt_configs, sample_prompts)

        assert success == 2
        assert total == 3

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
        mock_api_client.generate_batch.return_value = (3, 3)

        generator.generate_images(sample_prompt_configs, sample_prompts)

        # Should emit complete event with success/total counts
        complete_calls = [call for call in mock_events.emit.call_args_list if "COMPLETE" in str(call)]
        assert len(complete_calls) > 0


# ============================================================================
# Test: Manifest callback integration
# ============================================================================


class TestManifestCallbackIntegration:
    """Test manifest update callback."""

    def test_callback_updates_manifest_on_success(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client,
        mock_manifest_manager
    ):
        """Callback updates manifest when image succeeds."""
        # Capture the callback
        generator.generate_images(sample_prompt_configs, sample_prompts)
        callback = mock_api_client.generate_batch.call_args[1]['on_image_generated']

        # Simulate successful image generation
        api_response = {"info": '{"seed": 12345}'}
        callback(idx=0, prompt_cfg=sample_prompt_configs[0], success=True, api_response=api_response)

        # Should call manifest_manager.update_incremental
        mock_manifest_manager.update_incremental.assert_called_once()
        call_args = mock_manifest_manager.update_incremental.call_args
        assert call_args[1]['idx'] == 0
        assert call_args[1]['filename'] == "test_0000_seed-42.png"
        assert call_args[1]['api_response'] == api_response

    def test_callback_skips_manifest_update_on_failure(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client,
        mock_manifest_manager
    ):
        """Callback skips manifest update when image fails."""
        generator.generate_images(sample_prompt_configs, sample_prompts)
        callback = mock_api_client.generate_batch.call_args[1]['on_image_generated']

        # Simulate failed image generation
        callback(idx=0, prompt_cfg=sample_prompt_configs[0], success=False, api_response=None)

        # Should NOT call manifest_manager.update_incremental
        mock_manifest_manager.update_incremental.assert_not_called()

    def test_callback_passes_prompt_dict_to_manifest(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client,
        mock_manifest_manager
    ):
        """Callback passes original prompt dict (with variations) to manifest."""
        generator.generate_images(sample_prompt_configs, sample_prompts)
        callback = mock_api_client.generate_batch.call_args[1]['on_image_generated']

        # Simulate successful image
        callback(idx=1, prompt_cfg=sample_prompt_configs[1], success=True, api_response=None)

        # Should pass prompt dict with variations
        call_args = mock_manifest_manager.update_incremental.call_args
        prompt_dict = call_args[1]['prompt_dict']
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

        # Should still call API (which may return 0, 0)
        mock_api_client.generate_batch.assert_called_once()
        # Should emit events
        assert mock_events.emit.call_count >= 1

    def test_handles_api_failure_gracefully(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Handles API failure (all images fail)."""
        # Mock API returning 0 success
        mock_api_client.generate_batch.return_value = (0, 3)

        success, total = generator.generate_images(sample_prompt_configs, sample_prompts)

        assert success == 0
        assert total == 3

    def test_handles_partial_success(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Handles partial success (some images fail)."""
        mock_api_client.generate_batch.return_value = (2, 3)

        success, total = generator.generate_images(sample_prompt_configs, sample_prompts)

        assert success == 2
        assert total == 3

    def test_delay_between_images_passed_to_api(
        self,
        generator,
        sample_prompt_configs,
        sample_prompts,
        mock_api_client
    ):
        """Passes delay_between_images to API client."""
        generator.generate_images(sample_prompt_configs, sample_prompts)

        call_args = mock_api_client.generate_batch.call_args
        # Should have delay parameter (default 2.0)
        assert 'delay_between_images' in call_args[1]
        assert call_args[1]['delay_between_images'] == 2.0
