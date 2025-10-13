"""
Pure HTTP client for Stable Diffusion WebUI API

This client handles ONLY API communication - no filesystem operations,
no progress reporting, no session management.
"""

import re
import requests
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class GenerationConfig:
    """Configuration for image generation"""
    steps: int = 30
    cfg_scale: float = 7.0
    width: int = 512
    height: int = 768
    sampler_name: str = "DPM++ 2M Karras"
    scheduler: Optional[str] = None  # NEW: Explicit scheduler (Karras, Exponential, etc.)
    batch_size: int = 1
    n_iter: int = 1

    # Hires Fix parameters
    enable_hr: bool = False
    hr_scale: float = 2.0
    hr_upscaler: str = "R-ESRGAN 4x+"
    denoising_strength: float = 0.5
    hr_second_pass_steps: Optional[int] = None


@dataclass
class PromptConfig:
    """Configuration for a specific prompt"""
    prompt: str
    negative_prompt: str = ""
    seed: Optional[int] = None
    filename: str = ""
    parameters: dict = field(default_factory=dict)  # Optional parameters (SD WebUI settings, extensions like ADetailer)


class SDAPIClient:
    """
    Pure HTTP client for Stable Diffusion WebUI API

    Responsibility: API communication only
    - Test connection
    - Send generation requests
    - Return raw API responses

    Does NOT handle:
    - File I/O
    - Progress reporting
    - Session management
    - Batch orchestration
    """

    def __init__(self, api_url: str = "http://127.0.0.1:7860"):
        """
        Initialize API client

        Args:
            api_url: Base URL for Stable Diffusion WebUI API
        """
        self.api_url = api_url.rstrip('/')
        self.generation_config = GenerationConfig()

    def set_generation_config(self, config: GenerationConfig):
        """
        Set default generation configuration

        Args:
            config: Generation parameters to use for subsequent requests
        """
        self.generation_config = config

    def test_connection(self, timeout: int = 5) -> bool:
        """
        Test connection to the API

        Args:
            timeout: Request timeout in seconds

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = requests.get(
                f"{self.api_url}/sdapi/v1/options",
                timeout=timeout
            )
            response.raise_for_status()
            return True
        except Exception:
            return False

    def _normalize_prompt(self, prompt: str) -> str:
        """
        Normalize prompt by replacing newlines and cleaning up commas.

        Args:
            prompt: Raw prompt string

        Returns:
            Normalized prompt with clean comma separation
        """
        # Replace newlines with ", "
        normalized = prompt.replace('\n', ', ').replace('\r', '')

        # Clean up multiple commas and spaces
        normalized = re.sub(r',(\s*,)+', ',', normalized)  # Multiple commas with optional spaces
        normalized = re.sub(r'\s+', ' ', normalized)        # Multiple spaces → single space
        normalized = re.sub(r',\s+', ', ', normalized)      # Normalize space after comma
        normalized = re.sub(r'\s+,', ',', normalized)       # Remove space before comma
        normalized = normalized.strip()                      # Trim edges

        return normalized

    def generate_image(self, prompt_config: PromptConfig, timeout: int = 300) -> dict:
        """
        Generate a single image via API

        Args:
            prompt_config: Prompt configuration
            timeout: Request timeout in seconds (default 300 = 5min)

        Returns:
            dict: Raw API response containing:
                - images: List[str] - Base64-encoded image data
                - parameters: dict - Generation parameters used
                - info: str - Generation info JSON string

        Raises:
            requests.exceptions.RequestException: If API call fails
        """
        payload = self._build_payload(prompt_config)

        response = requests.post(
            f"{self.api_url}/sdapi/v1/txt2img",
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        return response.json()

    def _build_payload(self, prompt_config: PromptConfig) -> dict:
        """
        Build API payload from prompt config

        Args:
            prompt_config: Prompt configuration

        Returns:
            dict: API payload ready to send
        """
        # Normalize prompts: replace newlines with ", " and clean up
        prompt = self._normalize_prompt(prompt_config.prompt)
        negative_prompt = self._normalize_prompt(prompt_config.negative_prompt)

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": prompt_config.seed if prompt_config.seed is not None else -1,
            "steps": self.generation_config.steps,
            "cfg_scale": self.generation_config.cfg_scale,
            "width": self.generation_config.width,
            "height": self.generation_config.height,
            "sampler_name": self.generation_config.sampler_name,
            "batch_size": self.generation_config.batch_size,
            "n_iter": self.generation_config.n_iter
        }

        # Add scheduler if specified
        if self.generation_config.scheduler is not None:
            payload["scheduler"] = self.generation_config.scheduler

        # Add Hires Fix parameters if enabled
        if self.generation_config.enable_hr:
            payload["enable_hr"] = True
            payload["hr_scale"] = self.generation_config.hr_scale
            payload["hr_upscaler"] = self.generation_config.hr_upscaler
            payload["denoising_strength"] = self.generation_config.denoising_strength

            # Calculate target resolution
            payload["hr_resize_x"] = round(
                self.generation_config.width * self.generation_config.hr_scale
            )
            payload["hr_resize_y"] = round(
                self.generation_config.height * self.generation_config.hr_scale
            )

            # Add second pass steps if specified
            if self.generation_config.hr_second_pass_steps is not None:
                payload["hr_second_pass_steps"] = self.generation_config.hr_second_pass_steps

        # Add ADetailer if configured in parameters
        if prompt_config.parameters and 'adetailer' in prompt_config.parameters:
            adetailer_config = prompt_config.parameters['adetailer']
            # adetailer_config should be an ADetailerConfig object with to_api_dict() method
            if hasattr(adetailer_config, 'to_api_dict'):
                adetailer_payload = adetailer_config.to_api_dict()
                if adetailer_payload:  # Only add if not None (i.e., enabled and has detectors)
                    payload["alwayson_scripts"] = adetailer_payload

        return payload

    def get_payload_for_config(self, prompt_config: PromptConfig) -> dict:
        """
        Build payload without sending request (useful for dry-run)

        Args:
            prompt_config: Prompt configuration

        Returns:
            dict: API payload that would be sent
        """
        return self._build_payload(prompt_config)

    # ========== API Introspection Methods ==========

    def get_samplers(self, timeout: int = 5) -> list[dict]:
        """
        Get list of available samplers from SD WebUI

        Returns:
            List of sampler dicts with keys: 'name', 'aliases', 'options'

        Example:
            [
                {"name": "Euler", "aliases": ["euler"], "options": {}},
                {"name": "DPM++ 2M Karras", "aliases": [], "options": {}}
            ]

        Raises:
            requests.exceptions.RequestException: If API call fails
        """
        response = requests.get(
            f"{self.api_url}/sdapi/v1/samplers",
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()

    def get_schedulers(self, timeout: int = 5) -> list[dict]:
        """
        Get list of available schedulers from SD WebUI

        Returns:
            List of scheduler dicts with keys: 'name', 'label', 'aliases'

        Example:
            [
                {"name": "karras", "label": "Karras", "aliases": []},
                {"name": "exponential", "label": "Exponential", "aliases": []}
            ]

        Raises:
            requests.exceptions.RequestException: If API call fails
        """
        response = requests.get(
            f"{self.api_url}/sdapi/v1/schedulers",
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()

    def get_sd_models(self, timeout: int = 5) -> list[dict]:
        """
        Get list of available Stable Diffusion models/checkpoints

        Returns:
            List of model dicts with keys: 'title', 'model_name', 'hash', 'sha256', 'filename', 'config'

        Example:
            [
                {
                    "title": "realisticVisionV60B1_v51VAE.safetensors [15012c538f]",
                    "model_name": "realisticVisionV60B1_v51VAE",
                    "hash": "15012c538f",
                    "filename": "/path/to/model.safetensors"
                }
            ]

        Raises:
            requests.exceptions.RequestException: If API call fails
        """
        response = requests.get(
            f"{self.api_url}/sdapi/v1/sd-models",
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()

    def get_upscalers(self, timeout: int = 5) -> list[dict]:
        """
        Get list of available upscalers (for Hires Fix, etc.)

        Returns:
            List of upscaler dicts with keys: 'name', 'model_name', 'model_path', 'model_url', 'scale'

        Example:
            [
                {
                    "name": "R-ESRGAN 4x+",
                    "model_name": "R-ESRGAN 4x+",
                    "scale": 4
                },
                {
                    "name": "Latent",
                    "model_name": None,
                    "scale": 2
                }
            ]

        Raises:
            requests.exceptions.RequestException: If API call fails
        """
        response = requests.get(
            f"{self.api_url}/sdapi/v1/upscalers",
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()

    def get_model_info(self, timeout: int = 5) -> dict:
        """
        Fetch current model/checkpoint information from WebUI options

        Returns:
            dict with model info:
            {
                "checkpoint": "model_name.safetensors [hash]",
                "vae": "vae_name.ckpt",
                "clip_skip": 1
            }

        Raises:
            requests.RequestException: If API call fails
        """
        response = requests.get(
            f"{self.api_url}/sdapi/v1/options",
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()

        return {
            "checkpoint": data.get("sd_model_checkpoint", "unknown"),
            "vae": data.get("sd_vae", "auto"),
            "clip_skip": data.get("CLIP_stop_at_last_layers", 1)
        }
