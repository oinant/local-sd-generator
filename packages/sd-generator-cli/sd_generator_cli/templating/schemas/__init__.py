"""
Schema validation module for YAML configuration files.

This module provides Pydantic schemas for explicit validation of all
YAML configuration file types used in the template system.

Schemas:
- TemplateFileSchema: .template.yaml files
- PromptFileSchema: .prompt.yaml files
- ChunkFileSchema: .chunk.yaml files
- VariationsFileSchema: .yaml variation files
- ThemeFileSchema: theme.yaml files

Usage:
    from sd_generator_cli.templating.schemas import TemplateFileSchema

    # Validate YAML data
    try:
        schema = TemplateFileSchema(**yaml_data)
    except ValidationError as e:
        print(f"Validation failed: {e}")
"""

from .base import BaseFileSchema, ImplementableSchema
from .template_schema import TemplateFileSchema
from .prompt_schema import PromptFileSchema
from .chunk_schema import ChunkFileSchema
from .variations_schema import VariationsFileSchema
from .theme_schema import ThemeFileSchema

__all__ = [
    'BaseFileSchema',
    'ImplementableSchema',
    'TemplateFileSchema',
    'PromptFileSchema',
    'ChunkFileSchema',
    'VariationsFileSchema',
    'ThemeFileSchema',
]
