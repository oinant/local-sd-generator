"""
Data models for Template System V2.0.

This module defines the core configuration models for templates, chunks, and prompts.
Each model corresponds to a specific YAML file type in the V2.0 system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Any


@dataclass
class TemplateConfig:
    """
    Configuration for a .template.yaml file.

    A template defines base parameters and structure for prompt generation.
    It can be inherited by other templates or prompts using implements:.

    Required fields: version, name, template
    Optional fields: implements, parameters, imports, negative_prompt
    """
    version: str
    name: str
    template: str
    source_file: Path
    implements: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    imports: Dict[str, Any] = field(default_factory=dict)
    negative_prompt: str = ''


@dataclass
class ChunkConfig:
    """
    Configuration for a .chunk.yaml file.

    A chunk is a reusable template block (e.g., character, scene, style).
    It can define default values and be injected into templates using @Chunk syntax.

    Required fields: version, type, template
    Optional fields: implements, imports, defaults, chunks
    """
    version: str
    type: str
    template: str
    source_file: Path
    implements: Optional[str] = None
    imports: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, str] = field(default_factory=dict)
    chunks: Dict[str, str] = field(default_factory=dict)


@dataclass
class GenerationConfig:
    """
    Configuration for image generation settings.

    Defines how variations are generated (random vs combinatorial),
    seed management, and the number of images to generate.
    """
    mode: str  # 'random' | 'combinatorial'
    seed: int
    seed_mode: str  # 'fixed' | 'progressive' | 'random'
    max_images: int


@dataclass
class PromptConfig:
    """
    Configuration for a .prompt.yaml file.

    A prompt is the final configuration that combines a template with specific
    variations and generation settings to produce images.

    Required fields: version, name, generation, prompt
    Optional fields: implements, imports, parameters, negative_prompt

    Note: implements is optional to support standalone prompts.
    Note: The 'prompt' field contains the content to inject into the parent template's {prompt} placeholder.
    """
    version: str
    name: str
    generation: GenerationConfig
    prompt: str
    source_file: Path
    implements: Optional[str] = None
    imports: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    negative_prompt: Optional[str] = None
    # After inheritance resolution, template will contain the fully resolved template
    template: Optional[str] = None


@dataclass
class ResolvedContext:
    """
    Context for template resolution with all variations loaded.

    This context is used during template resolution to inject chunks,
    apply selectors, and resolve placeholders.

    Attributes:
        imports: Dict mapping import names to their key-value variations
        chunks: Dict mapping chunk names to their ChunkConfig objects
        parameters: Merged SD WebUI parameters from inheritance chain
        variation_state: Current values for placeholders during generation
    """
    imports: Dict[str, Dict[str, str]]  # {import_name: {key: value}}
    chunks: Dict[str, ChunkConfig]      # {chunk_name: ChunkConfig}
    parameters: Dict[str, Any]
    variation_state: Dict[str, str] = field(default_factory=dict)
