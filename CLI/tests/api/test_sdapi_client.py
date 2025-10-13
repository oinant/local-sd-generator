"""
Unit tests for SDAPIClient (pure HTTP client)
"""

import pytest
from unittest.mock import Mock, patch
import requests

from api import SDAPIClient, GenerationConfig, PromptConfig


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

    def test_build_payload_normalizes_newlines_in_prompt(self):
        """Test that newlines in prompt are replaced with ', '"""
        client = SDAPIClient()
        prompt_config = PromptConfig(
            prompt="masterpiece\nbest quality\n1girl",
            negative_prompt="low quality\nblurry"
        )

        payload = client.get_payload_for_config(prompt_config)

        assert payload['prompt'] == "masterpiece, best quality, 1girl"
        assert payload['negative_prompt'] == "low quality, blurry"

    def test_build_payload_handles_windows_newlines(self):
        """Test that Windows-style CRLF newlines are handled correctly"""
        client = SDAPIClient()
        prompt_config = PromptConfig(
            prompt="line1\r\nline2\r\nline3",
            negative_prompt="bad\r\nugly"
        )

        payload = client.get_payload_for_config(prompt_config)

        assert payload['prompt'] == "line1, line2, line3"
        assert payload['negative_prompt'] == "bad, ugly"

    def test_build_payload_with_no_newlines(self):
        """Test that prompts without newlines are unchanged"""
        client = SDAPIClient()
        prompt_config = PromptConfig(
            prompt="simple prompt",
            negative_prompt="simple negative"
        )

        payload = client.get_payload_for_config(prompt_config)

        assert payload['prompt'] == "simple prompt"
        assert payload['negative_prompt'] == "simple negative"

    def test_build_payload_cleans_multiple_commas(self):
        """Test that multiple commas from newline replacement are cleaned up"""
        client = SDAPIClient()
        prompt_config = PromptConfig(
            prompt="tag1,\ntag2,\n\ntag3",  # Will create ,, after replacement
            negative_prompt="bad1,\n\nbad2"
        )

        payload = client.get_payload_for_config(prompt_config)

        # Should clean up ,, to single ,
        assert payload['prompt'] == "tag1, tag2, tag3"
        assert payload['negative_prompt'] == "bad1, bad2"
        # Verify no double commas
        assert ',,' not in payload['prompt']
        assert ',,' not in payload['negative_prompt']

    @patch('requests.post')
    def test_generate_image_with_scheduler(self, mock_post):
        """Test image generation with explicit scheduler"""
        mock_response = Mock()
        mock_response.json.return_value = {'images': ['data']}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SDAPIClient()
        config = GenerationConfig(
            sampler_name="DPM++ 2M",
            scheduler="Karras"
        )
        client.set_generation_config(config)

        prompt_config = PromptConfig(prompt="test", filename="test.png")
        client.generate_image(prompt_config)

        # Check scheduler in payload
        payload = mock_post.call_args[1]['json']
        assert payload['sampler_name'] == "DPM++ 2M"
        assert payload['scheduler'] == "Karras"

    def test_build_payload_without_scheduler(self):
        """Test payload building without scheduler (backward compatible)"""
        client = SDAPIClient()
        config = GenerationConfig(sampler_name="Euler a")
        client.set_generation_config(config)

        prompt_config = PromptConfig(prompt="test")
        payload = client.get_payload_for_config(prompt_config)

        assert payload['sampler_name'] == "Euler a"
        assert 'scheduler' not in payload  # Should not include if None

    @patch('requests.get')
    def test_get_samplers(self, mock_get):
        """Test fetching samplers list"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"name": "Euler", "aliases": ["euler"], "options": {}},
            {"name": "DPM++ 2M Karras", "aliases": [], "options": {}}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = SDAPIClient()
        samplers = client.get_samplers()

        assert len(samplers) == 2
        assert samplers[0]['name'] == "Euler"
        mock_get.assert_called_once_with(
            "http://127.0.0.1:7860/sdapi/v1/samplers",
            timeout=5
        )

    @patch('requests.get')
    def test_get_schedulers(self, mock_get):
        """Test fetching schedulers list"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"name": "karras", "label": "Karras", "aliases": []},
            {"name": "exponential", "label": "Exponential", "aliases": []}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = SDAPIClient()
        schedulers = client.get_schedulers()

        assert len(schedulers) == 2
        assert schedulers[0]['label'] == "Karras"
        mock_get.assert_called_once_with(
            "http://127.0.0.1:7860/sdapi/v1/schedulers",
            timeout=5
        )

    @patch('requests.get')
    def test_get_sd_models(self, mock_get):
        """Test fetching SD models list"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "title": "model_v1.safetensors [abc123]",
                "model_name": "model_v1",
                "hash": "abc123",
                "filename": "/path/to/model.safetensors"
            }
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = SDAPIClient()
        models = client.get_sd_models()

        assert len(models) == 1
        assert models[0]['model_name'] == "model_v1"
        mock_get.assert_called_once_with(
            "http://127.0.0.1:7860/sdapi/v1/sd-models",
            timeout=5
        )

    @patch('requests.get')
    def test_get_upscalers(self, mock_get):
        """Test fetching upscalers list"""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"name": "R-ESRGAN 4x+", "model_name": "R-ESRGAN 4x+", "scale": 4},
            {"name": "Latent", "model_name": None, "scale": 2}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = SDAPIClient()
        upscalers = client.get_upscalers()

        assert len(upscalers) == 2
        assert upscalers[0]['name'] == "R-ESRGAN 4x+"
        mock_get.assert_called_once_with(
            "http://127.0.0.1:7860/sdapi/v1/upscalers",
            timeout=5
        )

    @patch('requests.get')
    def test_get_model_info(self, mock_get):
        """Test fetching current model info"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "sd_model_checkpoint": "realisticVision_v51.safetensors [hash]",
            "sd_vae": "vae-ft-mse.ckpt",
            "CLIP_stop_at_last_layers": 2
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = SDAPIClient()
        info = client.get_model_info()

        assert info['checkpoint'] == "realisticVision_v51.safetensors [hash]"
        assert info['vae'] == "vae-ft-mse.ckpt"
        assert info['clip_skip'] == 2
        mock_get.assert_called_once_with(
            "http://127.0.0.1:7860/sdapi/v1/options",
            timeout=5
        )

    @patch('requests.get')
    def test_get_adetailer_models(self, mock_get):
        """Test fetching ADetailer models list"""
        mock_response = Mock()
        mock_response.json.return_value = [
            "face_yolov9c.pt",
            "face_yolov8n.pt",
            "hand_yolov8n.pt",
            "person_yolov8n-seg.pt",
            "mediapipe_face_full"
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = SDAPIClient()
        models = client.get_adetailer_models()

        assert len(models) == 5
        assert "face_yolov9c.pt" in models
        assert "hand_yolov8n.pt" in models
        mock_get.assert_called_once_with(
            "http://127.0.0.1:7860/adetailer/v1/ad_model",
            timeout=5
        )

    @patch('requests.post')
    def test_generate_image_with_adetailer(self, mock_post):
        """Test image generation with ADetailer config"""
        from templating.models.config_models import ADetailerConfig, ADetailerDetector

        mock_response = Mock()
        mock_response.json.return_value = {'images': ['data']}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Create ADetailer config
        detector = ADetailerDetector(
            ad_model="face_yolov9c.pt",
            ad_denoising_strength=0.5,
            ad_steps=40,
            ad_mask_k_largest=1
        )
        adetailer_config = ADetailerConfig(enabled=True, detectors=[detector])

        client = SDAPIClient()
        prompt_config = PromptConfig(
            prompt="test portrait",
            filename="test.png",
            parameters={"adetailer": adetailer_config}
        )

        client.generate_image(prompt_config)

        # Check ADetailer in payload
        payload = mock_post.call_args[1]['json']
        assert 'alwayson_scripts' in payload
        assert 'ADetailer' in payload['alwayson_scripts']
        adetailer_payload = payload['alwayson_scripts']['ADetailer']
        assert 'args' in adetailer_payload
        # Format: [enable, skip_img2img, detector_dict]
        assert len(adetailer_payload['args']) == 3
        assert adetailer_payload['args'][0] is True  # Enable ADetailer
        assert adetailer_payload['args'][1] is False  # Skip img2img
        # Check first detector config at index 2
        detector_dict = adetailer_payload['args'][2]
        assert detector_dict['ad_model'] == "face_yolov9c.pt"
        assert detector_dict['ad_denoising_strength'] == 0.5

    @patch('requests.post')
    def test_generate_image_without_adetailer(self, mock_post):
        """Test image generation without ADetailer (no alwayson_scripts)"""
        mock_response = Mock()
        mock_response.json.return_value = {'images': ['data']}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = SDAPIClient()
        prompt_config = PromptConfig(prompt="test", filename="test.png")

        client.generate_image(prompt_config)

        # Check no alwayson_scripts in payload
        payload = mock_post.call_args[1]['json']
        assert 'alwayson_scripts' not in payload


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
        assert config.scheduler is None  # NEW: scheduler defaults to None
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
