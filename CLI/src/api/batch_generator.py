"""
Batch generation orchestrator

Coordinates API client, session manager, file I/O, and progress reporting
to execute batch image generation workflows.
"""

import time
from typing import List, Tuple, Optional, Dict, Callable
from pathlib import Path

from .sdapi_client import SDAPIClient, PromptConfig, GenerationConfig
from .session_manager import SessionManager
from .image_writer import ImageWriter
from .progress_reporter import ProgressReporter


class BatchGenerator:
    """
    Orchestrates batch image generation workflow

    Responsibility: Coordination and workflow orchestration
    - Coordinate API calls, file writes, and progress reporting
    - Implement delay logic between generations
    - Handle dry-run vs production mode
    - Provide high-level batch generation interface

    Does NOT handle:
    - Low-level API communication (SDAPIClient)
    - File I/O operations (ImageWriter)
    - Directory management (SessionManager)
    - Console output (ProgressReporter)
    """

    def __init__(self,
                 api_client: SDAPIClient,
                 session_manager: SessionManager,
                 image_writer: ImageWriter,
                 progress_reporter: ProgressReporter,
                 dry_run: bool = False):
        """
        Initialize batch generator

        Args:
            api_client: API client for generation requests
            session_manager: Session directory manager
            image_writer: Image file writer
            progress_reporter: Progress reporter
            dry_run: If True, save JSON instead of generating images
        """
        self.api_client = api_client
        self.session_manager = session_manager
        self.image_writer = image_writer
        self.progress = progress_reporter
        self.dry_run = dry_run

    def generate_batch(self,
                      prompt_configs: List[PromptConfig],
                      delay_between_images: float = 2.0,
                      on_image_generated: Optional[Callable[[int, PromptConfig, bool, Optional[Dict]], None]] = None) -> Tuple[int, int]:
        """
        Generate a batch of images

        Args:
            prompt_configs: List of prompt configurations
            delay_between_images: Delay in seconds between each generation
            on_image_generated: Optional callback(index, prompt_config, success, api_response)
                               Called after each image generation attempt
                               api_response is None on failure, contains API response dict on success

        Returns:
            Tuple[int, int]: (success_count, total_count)
        """
        # Ensure output directory exists
        self.session_manager.create_session_dir()

        # Test API connection (skip in dry-run mode)
        if not self.dry_run:
            if not self.api_client.test_connection():
                print("❌ Impossible de se connecter à l'API WebUI")
                return 0, len(prompt_configs)

        # Start batch
        self.progress.report_batch_start()

        success_count = 0
        total_images = len(prompt_configs)

        # Process each image
        for i, prompt_config in enumerate(prompt_configs, 1):
            self.progress.report_image_start(i, prompt_config.filename)

            success, api_response = self._generate_single_image(prompt_config)

            if success:
                success_count += 1
                self.progress.report_image_success(prompt_config.filename)
            else:
                self.progress.report_image_failure(
                    prompt_config.filename,
                    "Voir logs pour détails"
                )

            # Update progress
            self.progress.increment_completed()
            if success:
                self.progress.increment_success()

            # Call callback after each image (success or failure)
            if on_image_generated:
                on_image_generated(i - 1, prompt_config, success, api_response)

            # Delay between images (except after last)
            if i < total_images:
                time.sleep(delay_between_images)

            # Periodic progress update
            self.progress.report_progress_update(i, update_interval=10)

        # Final summary
        self.progress.report_batch_complete()

        return success_count, total_images

    def _generate_single_image(self, prompt_config: PromptConfig) -> Tuple[bool, Optional[Dict]]:
        """
        Generate a single image

        Args:
            prompt_config: Prompt configuration

        Returns:
            Tuple[bool, Optional[Dict]]: (success, api_response)
                - success: True if successful, False otherwise
                - api_response: API response dict on success (contains 'info' with real seed), None on failure or dry-run
        """
        try:
            if self.dry_run:
                # Dry-run mode: save JSON payload instead of generating
                payload = self.api_client.get_payload_for_config(prompt_config)
                self.image_writer.save_json_request(payload, prompt_config.filename)
                return True, None
            else:
                # Production mode: generate via API and save image
                response = self.api_client.generate_image(prompt_config)
                self.image_writer.save_image(response['images'][0], prompt_config.filename)
                return True, response

        except Exception as e:
            print(f"❌ Erreur génération {prompt_config.filename}: {e}")
            return False, None

    def save_batch_config(self,
                         base_prompt: str = "",
                         negative_prompt: str = "",
                         additional_info: Optional[Dict] = None):
        """
        Save session configuration file

        Args:
            base_prompt: Base prompt template
            negative_prompt: Negative prompt
            additional_info: Additional metadata to save
        """
        info = additional_info or {}
        info["dry_run"] = self.dry_run

        self.session_manager.save_session_config(
            self.api_client.generation_config,
            base_prompt,
            negative_prompt,
            info
        )


def create_batch_generator(
    api_url: str = "http://127.0.0.1:7860",
    base_output_dir: str = "apioutput",
    session_name: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = True,
    total_images: int = 0
) -> BatchGenerator:
    """
    Factory function to create a fully-configured BatchGenerator

    This is a convenience function that creates all the necessary components
    and wires them together.

    Args:
        api_url: Stable Diffusion API URL
        base_output_dir: Base directory for output
        session_name: Optional session name suffix
        dry_run: If True, save JSON instead of generating
        verbose: If False, suppress progress output
        total_images: Total number of images (for progress reporting)

    Returns:
        BatchGenerator: Configured batch generator

    Example:
        >>> generator = create_batch_generator(
        ...     session_name="my_batch",
        ...     dry_run=True,
        ...     total_images=10
        ... )
        >>> generator.generate_batch(prompt_configs)
    """
    # Create components
    api_client = SDAPIClient(api_url=api_url)
    session_manager = SessionManager(
        base_output_dir=base_output_dir,
        session_name=session_name,
        dry_run=dry_run
    )

    # ImageWriter needs the session directory
    image_writer = ImageWriter(session_manager.output_dir)

    # ProgressReporter
    progress_reporter = ProgressReporter(
        total_images=total_images,
        output_dir=session_manager.output_dir,
        verbose=verbose
    )

    # Create orchestrator
    return BatchGenerator(
        api_client=api_client,
        session_manager=session_manager,
        image_writer=image_writer,
        progress_reporter=progress_reporter,
        dry_run=dry_run
    )
