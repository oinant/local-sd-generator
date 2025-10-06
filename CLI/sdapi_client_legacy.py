"""
DEPRECATED: Legacy StableDiffusionAPIClient (kept for backward compatibility)

This file contains the old monolithic implementation.
New code should use the refactored API module (CLI/api/).

Migration path:
- Old: StableDiffusionAPIClient (this file)
- New: cli.api.SDAPIClient, SessionManager, ImageWriter, ProgressReporter, BatchGenerator
"""

import warnings
import requests
import json
import base64
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Import from new API module
from api.sdapi_client import GenerationConfig, PromptConfig
from api.batch_generator import create_batch_generator


class StableDiffusionAPIClient:
    """
    DEPRECATED: Legacy compatibility wrapper

    This class is deprecated and will be removed in a future version.
    Use the new API module instead:

    Old way:
        client = StableDiffusionAPIClient(api_url, base_output_dir, session_name)
        client.generate_batch(prompt_configs)

    New way:
        from api.batch_generator import create_batch_generator
        generator = create_batch_generator(api_url, base_output_dir, session_name, total_images=len(configs))
        generator.generate_batch(prompt_configs)
    """

    def __init__(self, api_url: str = "http://127.0.0.1:7860",
                 base_output_dir: str = "apioutput",
                 session_name: str = None,
                 dry_run: bool = False):
        warnings.warn(
            "StableDiffusionAPIClient is deprecated. Use api.BatchGenerator instead.",
            DeprecationWarning,
            stacklevel=2
        )

        self.api_url = api_url
        self.base_output_dir = base_output_dir
        self.session_name = session_name
        self.dry_run = dry_run
        self.session_start_time = datetime.now()
        self.generation_config = GenerationConfig()

        # Internal: will create batch generator on demand
        self._batch_generator = None

    def _get_batch_generator(self, total_images: int = 0):
        """Lazy-create batch generator"""
        if self._batch_generator is None:
            self._batch_generator = create_batch_generator(
                api_url=self.api_url,
                base_output_dir=self.base_output_dir,
                session_name=self.session_name,
                dry_run=self.dry_run,
                total_images=total_images
            )
            # Sync generation config
            self._batch_generator.api_client.set_generation_config(self.generation_config)

        return self._batch_generator

    @property
    def output_dir(self) -> str:
        """Get output directory path"""
        if self._batch_generator is None:
            # Create temporary one to get the path
            temp = self._get_batch_generator(0)
            return str(temp.session_manager.output_dir)
        return str(self._batch_generator.session_manager.output_dir)

    def _create_session_dir(self) -> str:
        """DEPRECATED: Use session_manager.create_session_dir()"""
        gen = self._get_batch_generator(0)
        return str(gen.session_manager.create_session_dir())

    def set_generation_config(self, config: GenerationConfig):
        """Set generation configuration"""
        self.generation_config = config
        if self._batch_generator:
            self._batch_generator.api_client.set_generation_config(config)

    def test_connection(self) -> bool:
        """Test API connection"""
        gen = self._get_batch_generator(0)
        return gen.api_client.test_connection()

    def create_output_dir(self):
        """Create output directory"""
        gen = self._get_batch_generator(0)
        path = gen.session_manager.create_session_dir()
        print(f"📁 Dossier créé: {path}")

    def save_session_config(self, base_prompt: str = "", negative_prompt: str = "",
                           additional_info: Dict = None):
        """Save session configuration"""
        gen = self._get_batch_generator(0)
        info = additional_info or {}
        gen.session_manager.save_session_config(
            self.generation_config,
            base_prompt,
            negative_prompt,
            info
        )
        print(f"📄 Configuration sauvée: {gen.session_manager.output_dir}/session_config.txt")

    def generate_single_image(self, prompt_config: PromptConfig) -> bool:
        """Generate a single image"""
        gen = self._get_batch_generator(1)

        try:
            if self.dry_run:
                payload = gen.api_client.get_payload_for_config(prompt_config)
                gen.image_writer.save_json_request(payload, prompt_config.filename)
            else:
                response = gen.api_client.generate_image(prompt_config)
                gen.image_writer.save_image(response['images'][0], prompt_config.filename)
            return True
        except Exception as e:
            print(f"❌ Erreur génération {prompt_config.filename}: {e}")
            return False

    def generate_batch(self, prompt_configs: List[PromptConfig],
                      delay_between_images: float = 2.0,
                      progress_callback: Optional[callable] = None,
                      base_prompt: str = "",
                      negative_prompt: str = "",
                      additional_info: Dict = None) -> Tuple[int, int]:
        """
        Generate a batch of images

        Args:
            prompt_configs: List of prompt configurations
            delay_between_images: Delay in seconds between generations
            progress_callback: DEPRECATED - not used in new implementation
            base_prompt: Base prompt for config file
            negative_prompt: Negative prompt for config file
            additional_info: Additional metadata

        Returns:
            Tuple[int, int]: (success_count, total_count)
        """
        # Create batch generator with correct total
        gen = self._get_batch_generator(len(prompt_configs))

        # Save config before starting
        if base_prompt or negative_prompt:
            info = additional_info or {}
            info["nombre_images_demandees"] = len(prompt_configs)
            gen.save_batch_config(base_prompt, negative_prompt, info)

        # Run batch
        return gen.generate_batch(prompt_configs, delay_between_images)


# Re-export helper functions for backward compatibility
def generate_all_combinations(variations: Dict[str, Dict[str, str]],
                            placeholder_order: List[str] = None) -> List[Dict[str, str]]:
    """
    DEPRECATED: Kept for backward compatibility

    Generate all combinations of variations.
    """
    return list(generate_combinations_lazy(variations, placeholder_order))


def generate_combinations_lazy(variations: Dict[str, Dict[str, str]],
                                placeholder_order: List[str] = None):
    """
    Generate combinations lazily

    This is a utility function, not part of the API client refactoring.
    """
    if placeholder_order:
        ordered_keys = [p for p in placeholder_order if p in variations]
        for key in variations:
            if key not in ordered_keys:
                ordered_keys.append(key)
    else:
        ordered_keys = list(variations.keys())

    def generate(remaining_keys, current_combination=None):
        if current_combination is None:
            current_combination = {}

        if not remaining_keys:
            yield current_combination.copy()
            return

        category_name = remaining_keys[0]
        category_variations = variations[category_name]
        remaining = remaining_keys[1:]

        for key, value in category_variations.items():
            current_combination[category_name] = value
            yield from generate(remaining, current_combination)
            del current_combination[category_name]

    yield from generate(ordered_keys)


def create_prompt_configs_from_combinations(base_prompt: str,
                                          negative_prompt: str,
                                          seed: Optional[int],
                                          variations: Dict[str, Dict[str, str]],
                                          filename_pattern: str = "{counter:03d}_{keys}.png") -> List[PromptConfig]:
    """
    DEPRECATED: Kept for backward compatibility

    Create PromptConfig list from variation combinations
    """
    prompt_configs = []
    counter = 1

    def generate_combinations(categories, current_combination=None, current_keys=None):
        nonlocal counter

        if current_combination is None:
            current_combination = []
            current_keys = []

        if not categories:
            non_empty_combinations = [desc for desc in current_combination if desc]
            if non_empty_combinations:
                full_prompt = f"{base_prompt}, {', '.join(non_empty_combinations)}"
            else:
                full_prompt = base_prompt

            non_empty_keys = [key for key in current_keys if key]
            keys_str = "_".join(non_empty_keys) if non_empty_keys else "default"
            filename = filename_pattern.format(counter=counter, keys=keys_str)

            prompt_configs.append(PromptConfig(
                prompt=full_prompt,
                negative_prompt=negative_prompt,
                seed=seed,
                filename=filename
            ))
            counter += 1
            return

        category_name, category_variations = list(categories.items())[0]
        remaining_categories = {k: v for k, v in categories.items() if k != category_name}

        for key, description in category_variations.items():
            generate_combinations(
                remaining_categories,
                current_combination + [description],
                current_keys + [key]
            )

    generate_combinations(variations)
    return prompt_configs
