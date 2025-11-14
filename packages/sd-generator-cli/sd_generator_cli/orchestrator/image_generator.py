"""ImageGenerator - orchestrates image generation via API."""

import time
from typing import Any

from ..api.sdapi_client import SDAPIClient, PromptConfig, GenerationConfig
from ..api.image_writer import ImageWriter
from .session_config import SessionConfig
from .session_event_collector import SessionEventCollector
from .manifest_manager import ManifestManager
from .event_types import EventType


class ImageGenerator:
    """Orchestrates image generation via SD WebUI API.

    This class handles:
    - Calling API generate_batch with prompt configs
    - Providing callback for incremental manifest updates
    - Event emission for progress tracking
    - Success/failure counting

    Example:
        >>> generator = ImageGenerator(api_client, manifest_manager, events, session_config)
        >>> success, total = generator.generate_images(prompt_configs, prompts)
    """

    def __init__(
        self,
        api_client: SDAPIClient,
        manifest_manager: ManifestManager,
        events: SessionEventCollector,
        session_config: SessionConfig
    ):
        """Initialize image generator.

        Args:
            api_client: SD WebUI API client
            manifest_manager: Manifest manager for incremental updates
            events: Event collector for output management
            session_config: Session configuration
        """
        self.api_client = api_client
        self.manifest_manager = manifest_manager
        self.events = events
        self.session_config = session_config
        # Create ImageWriter for saving images to disk
        self.image_writer = ImageWriter(output_dir=str(session_config.session_path))

    def generate_images(
        self,
        prompt_configs: list[PromptConfig],
        prompts: list[dict]
    ) -> tuple[int, int]:
        """Generate images via API with incremental manifest updates.

        This method:
        1. Emits IMAGE_GENERATION_START event
        2. Calls API generate_batch with callback
        3. Callback updates manifest incrementally
        4. Emits IMAGE_GENERATION_COMPLETE event
        5. Returns success/total counts

        Args:
            prompt_configs: List of PromptConfig for API
            prompts: Original V2 prompt dicts (with variations)

        Returns:
            Tuple of (success_count, total_count)
        """
        # Emit start event
        self.events.emit(
            EventType.IMAGE_GENERATION_START,
            {"total_images": len(prompt_configs)}
        )

        # Generate images one by one with incremental manifest updates
        success_count = 0
        total_count = len(prompt_configs)
        delay_between_images = 2.0

        for idx, prompt_cfg in enumerate(prompt_configs):
            try:
                # Apply parameters to API client before generation (like legacy V2Executor)
                if prompt_cfg.parameters:
                    self._apply_parameters(prompt_cfg.parameters)

                # Generate image via API
                api_response = self.api_client.generate_image(prompt_cfg)

                # Save image to disk
                self.image_writer.save_images_from_response(
                    api_response=api_response,
                    filename=prompt_cfg.filename
                )

                success = True
                success_count += 1

                # Update manifest incrementally on success
                self.manifest_manager.update_incremental(
                    idx=idx,
                    filename=prompt_cfg.filename,
                    prompt_dict=prompts[idx],
                    api_response=api_response
                )

                # Emit success event to update progress bar
                self.events.emit(
                    EventType.IMAGE_SUCCESS,
                    {
                        "index": idx,
                        "path": prompt_cfg.filename,
                        "seed": prompt_cfg.seed
                    }
                )

            except Exception as e:
                # Generation failed - log but continue
                success = False
                self.events.emit(
                    EventType.IMAGE_ERROR,
                    {
                        "index": idx,
                        "error": str(e)
                    }
                )

            # Delay before next image (except for last one)
            if idx < total_count - 1 and delay_between_images > 0:
                time.sleep(delay_between_images)

        # Emit complete event
        self.events.emit(
            EventType.IMAGE_GENERATION_COMPLETE,
            {
                "success_count": success_count,
                "total_count": total_count,
                "failed_count": total_count - success_count
            }
        )

        return success_count, total_count

    def _apply_parameters(self, parameters: dict[str, Any]) -> None:
        """Apply generation parameters to API client.

        This method replicates the legacy V2Executor._apply_parameters() behavior:
        - Creates a GenerationConfig with defaults
        - Overrides with template parameters
        - Configures the API client via set_generation_config()

        Args:
            parameters: Parameters dict from prompt config
        """
        config = GenerationConfig()

        # Map parameters to GenerationConfig fields
        # Note: 'sampler' in template becomes 'sampler_name' in GenerationConfig
        param_mapping = {
            'steps': 'steps',
            'cfg_scale': 'cfg_scale',
            'width': 'width',
            'height': 'height',
            'sampler': 'sampler_name',
            'scheduler': 'scheduler',
            'batch_size': 'batch_size',
            'batch_count': 'n_iter',
            'enable_hr': 'enable_hr',
            'hr_scale': 'hr_scale',
            'hr_upscaler': 'hr_upscaler',
            'denoising_strength': 'denoising_strength',
            'hr_second_pass_steps': 'hr_second_pass_steps'
        }

        for param_key, config_key in param_mapping.items():
            if param_key in parameters:
                setattr(config, config_key, parameters[param_key])

        self.api_client.set_generation_config(config)
