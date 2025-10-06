"""
Pure HTTP client for Stable Diffusion WebUI API

This client handles ONLY API communication - no filesystem operations,
no progress reporting, no session management.
"""

import requests
from typing import Optional
from dataclasses import dataclass


@dataclass
class GenerationConfig:
    """Configuration for image generation"""
    steps: int = 30
    cfg_scale: float = 7.0
    width: int = 512
    height: int = 768
    sampler_name: str = "DPM++ 2M Karras"
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
        payload = {
            "prompt": prompt_config.prompt,
            "negative_prompt": prompt_config.negative_prompt,
            "seed": prompt_config.seed if prompt_config.seed is not None else -1,
            "steps": self.generation_config.steps,
            "cfg_scale": self.generation_config.cfg_scale,
            "width": self.generation_config.width,
            "height": self.generation_config.height,
            "sampler_name": self.generation_config.sampler_name,
            "batch_size": self.generation_config.batch_size,
            "n_iter": self.generation_config.n_iter
        }

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
