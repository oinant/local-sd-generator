"""PromptConfigConverter - converts V2 prompts to PromptConfig list."""

import copy
import random
from pathlib import Path
from typing import Any

from ..api.sdapi_client import PromptConfig
from .session_config import SessionConfig


class PromptConfigConverter:
    """Converts V2 prompt dicts to PromptConfig objects.

    This class handles:
    - ControlNet image path resolution (dict and string variations)
    - Variations dict enrichment
    - Filename generation (with/without seed)
    - Parameters deep copying (to avoid sharing between prompts)

    Example:
        >>> converter = PromptConfigConverter(session_config, context)
        >>> prompt_configs = converter.convert_prompts(prompts)
    """

    def __init__(
        self,
        session_config: SessionConfig,
        context: Any  # ResolvedContext
    ):
        """Initialize converter.

        Args:
            session_config: Session configuration
            context: Resolved context (from V2Pipeline.resolve())
        """
        self.session_config = session_config
        self.context = context

    def convert_prompts(self, prompts: list[dict]) -> list[PromptConfig]:
        """Convert V2 prompt dicts to PromptConfig list.

        This method:
        1. Resolves ControlNet image paths (dict and string variations)
        2. Enriches variations dict with ControlNet info
        3. Generates filenames (with/without seed)
        4. Creates PromptConfig objects

        Args:
            prompts: List of prompt dicts from V2Pipeline.generate()

        Returns:
            List of PromptConfig objects ready for API
        """
        prompt_configs = []

        for idx, prompt_dict in enumerate(prompts):
            # Resolve ControlNet image variations (but don't encode yet)
            parameters = prompt_dict.get('parameters', {}).copy()
            variations = prompt_dict.get('variations', {}).copy()  # Copy for enrichment

            if 'controlnet' in parameters:
                # Deep copy controlnet config to avoid sharing between prompts
                controlnet_config = copy.deepcopy(parameters['controlnet'])
                parameters['controlnet'] = controlnet_config

                if hasattr(controlnet_config, 'units'):
                    for unit_idx, unit in enumerate(controlnet_config.units):
                        if unit.image:
                            # Handle dict variations (key → path mapping)
                            if isinstance(unit.image, dict):
                                # Find which key was used in this variation
                                # The dict has import name as key with None value
                                # We need to look in variations dict for the actual value
                                for import_name in unit.image.keys():
                                    # For ControlNet images, we need to pick a variation manually
                                    # since the generator doesn't handle parameters placeholders
                                    if import_name in self.context.imports and \
                                       isinstance(self.context.imports[import_name], dict):
                                        # Pick a random variation (or first one if already in variations)
                                        if import_name not in variations:
                                            image_path = random.choice(
                                                list(self.context.imports[import_name].values())
                                            )
                                            variations[import_name] = image_path
                                        else:
                                            image_path = variations[import_name]

                                        # Resolve path relative to template file
                                        image_path_obj = Path(image_path)
                                        if not image_path_obj.is_absolute():
                                            # Resolve relative to the template's directory
                                            template_dir = self.session_config.template_path.parent
                                            resolved_path = (template_dir / image_path).resolve()
                                            image_path = str(resolved_path)

                                        # Store resolved path (will be encoded in sdapi_client)
                                        unit.image = image_path
                                        break
                            # Handle direct string path
                            elif isinstance(unit.image, str):
                                # For direct paths, add to variations with a generated key
                                variation_key = f"ControlNetImage_{unit_idx}"
                                variations[variation_key] = unit.image

                                # Resolve path relative to template file if needed
                                image_path_obj = Path(unit.image)
                                if not image_path_obj.is_absolute():
                                    template_dir = self.session_config.template_path.parent
                                    resolved_path = (template_dir / unit.image).resolve()
                                    unit.image = str(resolved_path)

            # Update variations in prompt_dict for manifest
            prompt_dict['variations'] = variations

            # Build filename with seed if present
            seed = prompt_dict.get('seed', -1)
            if seed != -1:
                filename = f"{self.session_config.session_name}_{idx:04d}_seed-{seed}.png"
            else:
                filename = f"{self.session_config.session_name}_{idx:04d}.png"

            prompt_cfg = PromptConfig(
                prompt=prompt_dict['prompt'],
                negative_prompt=prompt_dict.get('negative_prompt', ''),
                seed=seed,
                filename=filename,
                parameters=parameters if parameters else None
            )
            prompt_configs.append(prompt_cfg)

        return prompt_configs
