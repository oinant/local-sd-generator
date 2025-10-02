"""
Next-Gen Templating System for Stable Diffusion Prompt Generation

This module provides a hierarchical templating system with:
- YAML-based variation files with backward compatibility for .txt files
- Advanced variation selectors ([happy,sad], [random:5], [range:1-10])
- Prompt configuration files (.prompt.yaml)
- Combinatorial and random generation modes
"""

from .loaders import load_variations
from .prompt_config import load_prompt_config, PromptConfig
from .resolver import resolve_prompt, ResolvedVariation

__all__ = [
    'load_variations',
    'load_prompt_config',
    'PromptConfig',
    'resolve_prompt',
    'ResolvedVariation',
]
