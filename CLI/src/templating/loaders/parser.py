"""
Configuration parser for Template System V2.0.

This module converts raw YAML data dictionaries into typed config model objects.
It handles parsing of templates, chunks, prompts, and variation files.
"""

from pathlib import Path
from typing import Dict, Any
from ..models.config_models import (
    TemplateConfig,
    ChunkConfig,
    PromptConfig,
    GenerationConfig
)


class ConfigParser:
    """
    Parser for converting YAML dictionaries into config model objects.

    This class handles the parsing of all V2.0 configuration file types:
    - .template.yaml → TemplateConfig
    - .chunk.yaml → ChunkConfig
    - .prompt.yaml → PromptConfig
    - .yaml (variations) → Dict[str, str]
    """

    def parse_template(self, data: Dict[str, Any], source_file: Path) -> TemplateConfig:
        """
        Parse a .template.yaml file.

        Args:
            data: Raw YAML dictionary
            source_file: Absolute path to the source YAML file

        Returns:
            TemplateConfig object

        Raises:
            KeyError: If required fields are missing
            ValueError: If template field is not a string
        """
        # Validate template field type
        template = data['template']
        if not isinstance(template, str):
            raise ValueError(
                f"Invalid 'template' field in {source_file.name}: "
                f"Expected string, got {type(template).__name__}.\n"
                f"Hint: If you're using placeholders like {{prompt}}, you need to quote them:\n"
                f"  ✗ Wrong:   template: {{prompt}}\n"
                f"  ✓ Correct: template: \"{{prompt}}\"\n"
                f"  ✓ Or use:  template: |\n"
                f"               {{prompt}}"
            )

        # Validate {prompt} placeholder is present (Template Method Pattern)
        if '{prompt}' not in template:
            raise ValueError(
                f"Invalid template in {source_file.name}: "
                f"Template files must contain {{prompt}} placeholder. "
                f"This is the injection point for child content (Template Method Pattern).\n"
                f"Example:\n"
                f"  template: |\n"
                f"    masterpiece, {{prompt}}, detailed"
            )

        return TemplateConfig(
            version=data.get('version', '1.0.0'),  # Default to 1.0.0 for backward compat
            name=data['name'],
            template=template,
            source_file=source_file,
            implements=data.get('implements'),
            parameters=data.get('parameters') or {},  # Handle None explicitly
            imports=data.get('imports') or {},
            negative_prompt=data.get('negative_prompt') or ''
        )

    def parse_chunk(self, data: Dict[str, Any], source_file: Path) -> ChunkConfig:
        """
        Parse a .chunk.yaml file.

        Args:
            data: Raw YAML dictionary
            source_file: Absolute path to the source YAML file

        Returns:
            ChunkConfig object

        Raises:
            KeyError: If required fields are missing
            ValueError: If template field is not a string
        """
        # Validate template field type
        template = data['template']
        if not isinstance(template, str):
            raise ValueError(
                f"Invalid 'template' field in {source_file.name}: "
                f"Expected string, got {type(template).__name__}.\n"
                f"Hint: If you're using placeholders like {{Expression}}, you need to quote them:\n"
                f"  ✗ Wrong:   template: {{Expression}}\n"
                f"  ✓ Correct: template: \"{{Expression}}\"\n"
                f"  ✓ Or use:  template: |\n"
                f"               {{Expression}}"
            )

        # Validate reserved placeholders are NOT used in chunks
        reserved_placeholders = ['{prompt}', '{negprompt}', '{loras}']
        found_reserved = [p for p in reserved_placeholders if p in template]
        if found_reserved:
            raise ValueError(
                f"Invalid template in {source_file.name}: "
                f"Chunks cannot use reserved placeholders: {', '.join(found_reserved)}. "
                f"Reserved placeholders are only allowed in template files.\n"
                f"Chunks are reusable blocks composed into templates, not templates themselves."
            )

        return ChunkConfig(
            version=data.get('version', '1.0.0'),
            type=data['type'],
            template=template,
            source_file=source_file,
            implements=data.get('implements'),
            imports=data.get('imports') or {},
            defaults=data.get('defaults') or {},
            chunks=data.get('chunks') or {}
        )

    def parse_prompt(self, data: Dict[str, Any], source_file: Path) -> PromptConfig:
        """
        Parse a .prompt.yaml file.

        Supports both:
        - Standalone prompts (no implements field)
        - Inherited prompts (with implements field)

        Args:
            data: Raw YAML dictionary
            source_file: Absolute path to the source YAML file

        Returns:
            PromptConfig object

        Raises:
            KeyError: If required fields are missing
            ValueError: If prompt field is not a string or template field is used
        """
        # Validation: prompt.yaml files use 'prompt:' not 'template:'
        if 'template' in data:
            raise ValueError(
                f"Invalid field in {source_file.name}: "
                f"Prompt files must use 'prompt:' field, not 'template:'. "
                f"Please rename 'template:' to 'prompt:' in your file."
            )

        # Validate prompt field type
        prompt = data['prompt']
        if not isinstance(prompt, str):
            raise ValueError(
                f"Invalid 'prompt' field in {source_file.name}: "
                f"Expected string, got {type(prompt).__name__}.\n"
                f"Hint: If you're using placeholders like {{Angle}}, you need to quote them:\n"
                f"  ✗ Wrong:   prompt: {{Angle}}\n"
                f"  ✓ Correct: prompt: \"{{Angle}}\"\n"
                f"  ✓ Or use:  prompt: |\n"
                f"               {{Angle}}"
            )

        # Parse generation config
        gen_data = data['generation']
        generation = GenerationConfig(
            mode=gen_data['mode'],
            seed=gen_data['seed'],
            seed_mode=gen_data['seed_mode'],
            max_images=gen_data['max_images']
        )

        return PromptConfig(
            version=data.get('version', '1.0.0'),
            name=data['name'],
            generation=generation,
            prompt=prompt,
            source_file=source_file,
            implements=data.get('implements'),  # Optional: supports standalone prompts
            imports=data.get('imports') or {},
            parameters=data.get('parameters') or {},  # Parse SD WebUI parameters
            negative_prompt=data.get('negative_prompt')
        )

    def parse_variations(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Parse a variations file (.yaml).

        V2.0 format supports two structures:
        1. Structured (with metadata):
           {
               "type": "variations",
               "name": "HairColors",
               "version": "1.0",
               "variations": {
                   "BobCut": "bob cut, chin-length hair",
                   "LongHair": "long flowing hair"
               }
           }
        2. Flat (direct dictionary):
           {
               "BobCut": "bob cut, chin-length hair",
               "LongHair": "long flowing hair"
           }

        Args:
            data: Raw YAML dictionary

        Returns:
            Dictionary mapping keys to prompt strings

        Raises:
            ValueError: If data is not a dictionary or variations key is missing
        """
        if not isinstance(data, dict):
            raise ValueError("Variations file must be a YAML dictionary")

        # Check if structured format (has 'variations' key)
        if 'variations' in data:
            variations = data['variations']
            if not isinstance(variations, dict):
                raise ValueError(
                    f"'variations' field must be a dictionary, got {type(variations).__name__}"
                )
            return {str(key): str(value) for key, value in variations.items()}

        # Flat format: entire dict is variations
        # Ensure all values are strings
        return {str(key): str(value) for key, value in data.items()}
