"""
Type definitions for the templating system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Variation:
    """A single variation entry."""
    key: str
    value: str
    weight: float = 1.0


@dataclass
class Selector:
    """A variation selector parsed from syntax like [happy,sad,random:3]."""
    type: str  # "keys", "random", "range", "indices", "all"
    keys: List[str] = field(default_factory=list)
    indices: List[int] = field(default_factory=list)
    count: Optional[int] = None
    start: Optional[int] = None
    end: Optional[int] = None


@dataclass
class PromptConfig:
    """Configuration loaded from a .prompt.yaml file."""
    name: str
    imports: Dict[str, str]  # {EXPRESSIONS: "path/to/file.yaml"}
    prompt_template: str
    negative_prompt: str = ""
    generation_mode: str = "combinatorial"
    seed_mode: str = "progressive"
    seed: int = 42
    max_images: Optional[int] = None
    base_path: Optional[str] = None  # Relative base path for imports (from YAML)

    # Selector configuration
    index_base: int = 0  # 0-indexed or 1-indexed
    strict_mode: bool = True
    allow_duplicates: bool = False
    random_seed: Optional[int] = None

    # SD API parameters
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg_scale: float = 7.0
    sampler: str = "Euler a"
    scheduler: Optional[str] = None  # Explicit scheduler (Karras, Exponential, etc.)
    batch_size: int = 1
    batch_count: int = 1

    # Hires Fix parameters
    enable_hr: bool = False
    hr_scale: float = 2.0
    hr_upscaler: str = "R-ESRGAN 4x+"
    denoising_strength: float = 0.5
    hr_second_pass_steps: Optional[int] = None


@dataclass
class ResolvedVariation:
    """A single resolved prompt variation ready for generation."""
    index: int
    seed: int
    placeholders: Dict[str, str]  # {EXPRESSIONS: "happy", POSES: "standing"}
    final_prompt: str
    negative_prompt: str = ""


@dataclass
class FieldDefinition:
    """Definition of a field in a text chunk template."""
    type: str  # "text"
    description: str
    required: bool = False
    default: Optional[str] = None
    example: Optional[str] = None


@dataclass
class ChunkTemplate:
    """A reusable text chunk template with parameterizable fields."""
    name: str
    type: str  # "chunk_template"
    version: str
    description: str
    output: str  # Template string with {field} placeholders
    fields: Dict[str, Dict[str, FieldDefinition]]  # Nested: {appearance: {age: FieldDef}}
    metadata: Dict = field(default_factory=dict)


@dataclass
class Chunk:
    """A configured text chunk instance implementing a template."""
    name: str
    type: str  # "chunk"
    version: str
    implements: Optional[str] = None  # Path to template
    fields: Dict[str, Dict[str, str]] = field(default_factory=dict)  # {appearance: {age: "23"}}
    metadata: Dict = field(default_factory=dict)


@dataclass
class MultiFieldVariation(Variation):
    """Variation that expands multiple fields simultaneously."""
    fields: Dict[str, str] = field(default_factory=dict)  # {appearance.skin: "dark", ...}


@dataclass
class ChunkOverride:
    """Represents an override in CHUNK with syntax."""
    field_path: str  # e.g., "ethnicity"
    source: str  # e.g., "ETHNICITIES"
    selector: str  # e.g., "[african,asian]"
