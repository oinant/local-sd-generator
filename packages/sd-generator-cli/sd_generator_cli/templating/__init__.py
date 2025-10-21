"""
Template System V2.0 for Stable Diffusion Prompt Generation

This module provides an advanced hierarchical templating system with:
- Template inheritance with implements:
- Modular imports with imports:
- Reusable chunks with multi-field expansion
- Advanced variation selectors and weights
- YAML-based configuration
"""

from .orchestrator import V2Pipeline
from .models.config_models import (
    TemplateConfig,
    ChunkConfig,
    PromptConfig,
    GenerationConfig,
    OutputConfig,
    ResolvedContext
)

__all__ = [
    'V2Pipeline',
    'TemplateConfig',
    'ChunkConfig',
    'PromptConfig',
    'GenerationConfig',
    'OutputConfig',
    'ResolvedContext',
]
