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
        """
        return TemplateConfig(
            version=data.get('version', '1.0.0'),  # Default to 1.0.0 for backward compat
            name=data['name'],
            template=data['template'],
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
        """
        return ChunkConfig(
            version=data.get('version', '1.0.0'),
            type=data['type'],
            template=data['template'],
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
        """
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
            template=data['template'],
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
