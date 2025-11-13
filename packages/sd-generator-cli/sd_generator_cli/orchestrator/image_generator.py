"""ImageGenerator - orchestrates image generation via API."""

from typing import Any

from ..api.sdapi_client import SDAPIClient, PromptConfig
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

        # Define callback to update manifest after each image
        def update_manifest_callback(
            idx: int,
            prompt_cfg: PromptConfig,
            success: bool,
            api_response: Any
        ) -> None:
            """Update manifest after each image generation."""
            if not success:
                return  # Skip failed images

            # Update manifest with image entry
            self.manifest_manager.update_incremental(
                idx=idx,
                filename=prompt_cfg.filename,
                prompt_dict=prompts[idx],
                api_response=api_response
            )

        # Generate images with incremental manifest updates
        success_count, total_count = self.api_client.generate_batch(
            prompt_configs=prompt_configs,
            delay_between_images=2.0,
            on_image_generated=update_manifest_callback
        )

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
