"""
Unit tests for SDAPIClient (pure HTTP client)
"""

import pytest
from unittest.mock import Mock, patch
import requests

from api.sdapi_client import SDAPIClient, GenerationConfig, PromptConfig


class TestSDAPIClient:
    """Test pure HTTP API client"""

    def test_init(self):
        """Test client initialization"""
        client = SDAPIClient(api_url="http://localhost:7860")
        assert client.api_url == "http://localhost:7860"
        assert isinstance(client.generation_config, GenerationConfig)

    def test_init_strips_trailing_slash(self):
        """Test URL normalization"""
        client = SDAPIClient(api_url="http://localhost:7860/")
        assert client.api_url == "http://localhost:7860"

    def test_set_generation_config(self):
        """Test setting generation configuration"""
        client = SDAPIClient()
        config = GenerationConfig(steps=50, cfg_scale=8.5)

        client.set_generation_config(config)

        assert client.generation_config.steps == 50
        assert client.generation_config.cfg_scale == 8.5

    @patch('requests.get')
    def test_test_connection_success(self, mock_get):
        """Test successful connection test"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = SDAPIClient()
        result = client.test_connection()

        assert result is True
        mock_get.assert_called_once_with(
            "http://127.0.0.1:7860/sdapi/v1/options",
            timeout=5
        )

    @patch('requests.get')
    def test_test_connection_failure(self, mock_get):
        """Test failed connection test"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        client = SDAPIClient()
        result = client.test_connection()

        assert result is False

    @patch('requests.post')
    def test_generate_image_success(self, mock_post):
        """Test successful image generation"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'images': ['base64_image_data'],
            'parameters': {},
            'info': '{}'
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SDAPIClient()
        prompt_config = PromptConfig(
            prompt="a cat",
            negative_prompt="low quality",
            seed=42,
            filename="test.png"
        )

        result = client.generate_image(prompt_config)

        assert 'images' in result
        assert result['images'][0] == 'base64_image_data'

        # Check payload was built correctly
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['prompt'] == "a cat"
        assert payload['negative_prompt'] == "low quality"
        assert payload['seed'] == 42
        assert payload['steps'] == 30  # default

    @patch('requests.post')
    def test_generate_image_with_hires_fix(self, mock_post):
        """Test image generation with Hires Fix enabled"""
        mock_response = Mock()
        mock_response.json.return_value = {'images': ['data']}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SDAPIClient()
        config = GenerationConfig(
            enable_hr=True,
            hr_scale=2.0,
            width=512,
            height=768
        )
        client.set_generation_config(config)

        prompt_config = PromptConfig(prompt="test", filename="test.png")
        client.generate_image(prompt_config)

        # Check Hires Fix params in payload
        payload = mock_post.call_args[1]['json']
        assert payload['enable_hr'] is True
        assert payload['hr_scale'] == 2.0
        assert payload['hr_resize_x'] == 1024  # 512 * 2
        assert payload['hr_resize_y'] == 1536  # 768 * 2

    @patch('requests.post')
    def test_generate_image_request_exception(self, mock_post):
        """Test image generation with request exception"""
        mock_post.side_effect = requests.exceptions.RequestException("API error")

        client = SDAPIClient()
        prompt_config = PromptConfig(prompt="test", filename="test.png")

        with pytest.raises(requests.exceptions.RequestException):
            client.generate_image(prompt_config)

    def test_get_payload_for_config(self):
        """Test payload building without sending request (dry-run)"""
        client = SDAPIClient()
        config = GenerationConfig(steps=25, cfg_scale=7.5)
        client.set_generation_config(config)

        prompt_config = PromptConfig(
            prompt="a dog",
            negative_prompt="bad quality",
            seed=123
        )

        payload = client.get_payload_for_config(prompt_config)

        assert payload['prompt'] == "a dog"
        assert payload['negative_prompt'] == "bad quality"
        assert payload['seed'] == 123
        assert payload['steps'] == 25
        assert payload['cfg_scale'] == 7.5

    def test_build_payload_with_random_seed(self):
        """Test payload building with no seed specified"""
        client = SDAPIClient()
        prompt_config = PromptConfig(prompt="test", seed=None)

        payload = client.get_payload_for_config(prompt_config)

        assert payload['seed'] == -1  # -1 means random seed


class TestGenerationConfig:
    """Test GenerationConfig dataclass"""

    def test_defaults(self):
        """Test default values"""
        config = GenerationConfig()

        assert config.steps == 30
        assert config.cfg_scale == 7.0
        assert config.width == 512
        assert config.height == 768
        assert config.sampler_name == "DPM++ 2M Karras"
        assert config.enable_hr is False

    def test_custom_values(self):
        """Test custom configuration"""
        config = GenerationConfig(
            steps=50,
            cfg_scale=9.0,
            width=768,
            height=1024,
            enable_hr=True
        )

        assert config.steps == 50
        assert config.cfg_scale == 9.0
        assert config.width == 768
        assert config.height == 1024
        assert config.enable_hr is True


class TestPromptConfig:
    """Test PromptConfig dataclass"""

    def test_minimal(self):
        """Test minimal prompt config"""
        config = PromptConfig(prompt="a cat")

        assert config.prompt == "a cat"
        assert config.negative_prompt == ""
        assert config.seed is None
        assert config.filename == ""

    def test_full(self):
        """Test full prompt config"""
        config = PromptConfig(
            prompt="a dog",
            negative_prompt="low quality",
            seed=42,
            filename="dog_001.png"
        )

        assert config.prompt == "a dog"
        assert config.negative_prompt == "low quality"
        assert config.seed == 42
        assert config.filename == "dog_001.png"
