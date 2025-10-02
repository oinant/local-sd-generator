"""
Next-Gen Templating System for Stable Diffusion Prompt Generation

This module provides a hierarchical templating system with:
- YAML-based variation files with backward compatibility for .txt files
- Advanced variation selectors ([happy,sad], [random:5], [range:1-10])
- Prompt configuration files (.prompt.yaml)
- Combinatorial and random generation modes
- Reusable text chunks with multi-field expansion (Phase 2)
"""

from .loaders import load_variations
from .prompt_config import load_prompt_config, PromptConfig
from .resolver import resolve_prompt, ResolvedVariation
from .chunk import load_chunk_template, load_chunk, resolve_chunk_fields, render_chunk
from .multi_field import (
    is_multi_field_variation,
    load_multi_field_variations,
    expand_multi_field,
    merge_multi_field_into_chunk,
)

__all__ = [
    'load_variations',
    'load_prompt_config',
    'PromptConfig',
    'resolve_prompt',
    'ResolvedVariation',
    'load_chunk_template',
    'load_chunk',
    'resolve_chunk_fields',
    'render_chunk',
    'is_multi_field_variation',
    'load_multi_field_variations',
    'expand_multi_field',
    'merge_multi_field_into_chunk',
]
