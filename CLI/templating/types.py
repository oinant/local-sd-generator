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

    # Selector configuration
    index_base: int = 0  # 0-indexed or 1-indexed
    strict_mode: bool = True
    allow_duplicates: bool = False
    random_seed: Optional[int] = None


@dataclass
class ResolvedVariation:
    """A single resolved prompt variation ready for generation."""
    index: int
    seed: int
    placeholders: Dict[str, str]  # {EXPRESSIONS: "happy", POSES: "standing"}
    final_prompt: str
    negative_prompt: str = ""
