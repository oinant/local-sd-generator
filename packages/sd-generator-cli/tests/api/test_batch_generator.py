"""
Unit tests for BatchGenerator (orchestrator)
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from sd_generator_cli.api import BatchGenerator, create_batch_generator
from sd_generator_cli.api import SDAPIClient, PromptConfig, GenerationConfig
from sd_generator_cli.api import SessionManager
from sd_generator_cli.api import ImageWriter
from sd_generator_cli.api import SilentProgressReporter


class TestBatchGenerator:
    """Test batch generation orchestrator"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    @pytest.fixture
    def mock_components(self, temp_dir):
        """Create mocked components"""
        api_client = Mock(spec=SDAPIClient)
        api_client.generation_config = GenerationConfig()
        api_client.test_connection.return_value = True
        api_client.generate_image.return_value = {
            'images': ['base64_data'],
            'parameters': {},
            'info': '{}'
        }
        api_client.get_payload_for_config.return_value = {'prompt': 'test'}

        session_mgr = SessionManager(base_output_dir=temp_dir)
        image_writer = ImageWriter(session_mgr.output_dir)
        progress = SilentProgressReporter(total_images=1)

        return {
            'api_client': api_client,
            'session_mgr': session_mgr,
            'image_writer': image_writer,
            'progress': progress
        }

    def test_init(self, mock_components):
        """Test batch generator initialization"""
        generator = BatchGenerator(
            api_client=mock_components['api_client'],
            session_manager=mock_components['session_mgr'],
            image_writer=mock_components['image_writer'],
            progress_reporter=mock_components['progress'],
            dry_run=False
        )

        assert generator.api_client is not None
        assert generator.session_manager is not None
        assert generator.image_writer is not None
        assert generator.progress is not None
        assert generator.dry_run is False

    def test_generate_batch_production_mode(self, mock_components, temp_dir):
        """Test batch generation in production mode"""
        # Mock image writer to avoid actual file I/O
        mock_writer = Mock(spec=ImageWriter)
        mock_writer.save_image.return_value = Path(temp_dir) / "test.png"

        generator = BatchGenerator(
            api_client=mock_components['api_client'],
            session_manager=mock_components['session_mgr'],
            image_writer=mock_writer,
            progress_reporter=mock_components['progress'],
            dry_run=False
        )

        prompts = [
            PromptConfig(prompt="a cat", filename="cat.png"),
            PromptConfig(prompt="a dog", filename="dog.png")
        ]

        success, total = generator.generate_batch(prompts, delay_between_images=0)

        assert success == 2
        assert total == 2

        # API should be called twice
        assert mock_components['api_client'].generate_image.call_count == 2
        # Image writer should be called twice
        assert mock_writer.save_image.call_count == 2

    def test_generate_batch_dry_run_mode(self, mock_components, temp_dir):
        """Test batch generation in dry-run mode"""
        generator = BatchGenerator(
            api_client=mock_components['api_client'],
            session_manager=mock_components['session_mgr'],
            image_writer=mock_components['image_writer'],
            progress_reporter=mock_components['progress'],
            dry_run=True
        )

        prompts = [
            PromptConfig(prompt="test", filename="test.png")
        ]

        success, total = generator.generate_batch(prompts, delay_between_images=0)

        assert success == 1
        assert total == 1

        # API should NOT be called in dry-run
        mock_components['api_client'].generate_image.assert_not_called()

        # Payload getter should be called instead
        mock_components['api_client'].get_payload_for_config.assert_called_once()

        # JSON file should exist
        json_file = mock_components['session_mgr'].output_dir / "test.json"
        assert json_file.exists()

    def test_generate_batch_api_connection_failure(self, mock_components):
        """Test batch generation when API connection fails"""
        mock_components['api_client'].test_connection.return_value = False

        generator = BatchGenerator(
            api_client=mock_components['api_client'],
            session_manager=mock_components['session_mgr'],
            image_writer=mock_components['image_writer'],
            progress_reporter=mock_components['progress'],
            dry_run=False
        )

        prompts = [PromptConfig(prompt="test", filename="test.png")]

        success, total = generator.generate_batch(prompts)

        assert success == 0
        assert total == 1

        # Should not attempt generation
        mock_components['api_client'].generate_image.assert_not_called()

    def test_generate_batch_partial_failure(self, mock_components):
        """Test batch with some images failing"""
        # First call succeeds, second fails
        mock_components['api_client'].generate_image.side_effect = [
            {'images': ['data']},
            Exception("API error")
        ]

        generator = BatchGenerator(
            api_client=mock_components['api_client'],
            session_manager=mock_components['session_mgr'],
            image_writer=mock_components['image_writer'],
            progress_reporter=mock_components['progress'],
            dry_run=False
        )

        prompts = [
            PromptConfig(prompt="success", filename="success.png"),
            PromptConfig(prompt="fail", filename="fail.png")
        ]

        success, total = generator.generate_batch(prompts, delay_between_images=0)

        assert success == 1
        assert total == 2

    def test_save_batch_config(self, mock_components):
        """Test saving batch configuration"""
        generator = BatchGenerator(
            api_client=mock_components['api_client'],
            session_manager=mock_components['session_mgr'],
            image_writer=mock_components['image_writer'],
            progress_reporter=mock_components['progress'],
            dry_run=True
        )

        generator.save_batch_config(
            base_prompt="base prompt",
            negative_prompt="negative",
            additional_info={"test": "value"}
        )

        config_file = mock_components['session_mgr'].output_dir / "session_config.txt"
        assert config_file.exists()

        content = config_file.read_text(encoding='utf-8')
        assert "base prompt" in content
        assert "negative" in content
        assert "test: value" in content
        assert "dry_run: True" in content

    def test_generate_batch_creates_output_dir(self, mock_components, temp_dir):
        """Test batch generation creates output directory"""
        session_dir = Path(temp_dir) / "test_session"
        assert not session_dir.exists()

        generator = BatchGenerator(
            api_client=mock_components['api_client'],
            session_manager=mock_components['session_mgr'],
            image_writer=mock_components['image_writer'],
            progress_reporter=mock_components['progress'],
            dry_run=True
        )

        prompts = [PromptConfig(prompt="test", filename="test.png")]
        generator.generate_batch(prompts, delay_between_images=0)

        # Output directory should be created
        assert mock_components['session_mgr'].output_dir.exists()

    @patch('time.sleep')
    def test_delay_between_images(self, mock_sleep, mock_components):
        """Test delay is applied between images"""
        generator = BatchGenerator(
            api_client=mock_components['api_client'],
            session_manager=mock_components['session_mgr'],
            image_writer=mock_components['image_writer'],
            progress_reporter=mock_components['progress'],
            dry_run=True
        )

        prompts = [
            PromptConfig(prompt="1", filename="1.png"),
            PromptConfig(prompt="2", filename="2.png"),
            PromptConfig(prompt="3", filename="3.png")
        ]

        generator.generate_batch(prompts, delay_between_images=1.5)

        # Should sleep twice (not after last image)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(1.5)


class TestCreateBatchGenerator:
    """Test factory function"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_create_batch_generator_minimal(self, temp_dir):
        """Test factory with minimal parameters"""
        generator = create_batch_generator(
            base_output_dir=temp_dir,
            total_images=5
        )

        assert isinstance(generator, BatchGenerator)
        assert isinstance(generator.api_client, SDAPIClient)
        assert isinstance(generator.session_manager, SessionManager)
        assert isinstance(generator.image_writer, ImageWriter)

    def test_create_batch_generator_full(self, temp_dir):
        """Test factory with all parameters"""
        generator = create_batch_generator(
            api_url="http://localhost:8000",
            base_output_dir=temp_dir,
            session_name="test_session",
            dry_run=True,
            verbose=False,
            total_images=10
        )

        assert generator.api_client.api_url == "http://localhost:8000"
        assert generator.session_manager.session_name == "test_session"
        assert generator.session_manager.dry_run is True
        assert generator.dry_run is True
        assert generator.progress.verbose is False
        assert generator.progress.total == 10

    def test_create_batch_generator_components_wired(self, temp_dir):
        """Test factory correctly wires components together"""
        generator = create_batch_generator(
            base_output_dir=temp_dir,
            session_name="wiring_test",
            total_images=1
        )

        # Session manager and image writer should share same output dir
        assert generator.session_manager.output_dir == generator.image_writer.output_dir

        # Progress reporter should have correct total
        assert generator.progress.total == 1
