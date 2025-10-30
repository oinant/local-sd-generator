"""
Schema for .prompt.yaml files.

Prompt files are executable configurations that implement templates
and contain generation parameters.
"""

from pydantic import Field, validator, BaseModel
from typing import Optional, Dict, Any, Literal, List

from .base import ImplementableSchema


class GenerationConfigSchema(BaseModel):
    """Schema for generation configuration block."""

    mode: Literal["combinatorial", "random"] = Field(
        ...,
        description="Generation mode: 'combinatorial' for all combinations, 'random' for sampling"
    )

    seed_mode: Literal["fixed", "progressive", "random"] = Field(
        ...,
        description="Seed mode: 'fixed' (same seed), 'progressive' (incremental), 'random' (random seeds)"
    )

    seed: int = Field(
        ...,
        description="Base seed value (-1 for random)"
    )

    max_images: int = Field(
        ...,
        description="Maximum number of images to generate",
        gt=0
    )

    class Config:
        extra = "forbid"

    @validator('seed')
    def validate_seed(cls, v: int) -> int:
        """Validate seed value."""
        if v < -1:
            raise ValueError(f"Invalid seed '{v}'. Must be >= -1 (use -1 for random)")
        return v


class AnnotationsConfigSchema(BaseModel):
    """Schema for annotations configuration."""

    enabled: bool = Field(default=False, description="Enable image annotations")
    keys: List[str] = Field(default_factory=list, description="Variation keys to display")
    position: str = Field(default="bottom-left", description="Annotation position")
    font_size: int = Field(default=16, description="Font size", gt=0)
    background_alpha: int = Field(default=180, description="Background opacity (0-255)", ge=0, le=255)
    text_color: str = Field(default="white", description="Text color")
    padding: int = Field(default=10, description="Padding", ge=0)
    margin: int = Field(default=20, description="Margin", ge=0)

    class Config:
        extra = "forbid"


class OutputConfigSchema(BaseModel):
    """Schema for output configuration."""

    session_name: Optional[str] = Field(None, description="Session directory name")
    filename_keys: List[str] = Field(default_factory=list, description="Keys for filename generation")
    annotations: Optional[AnnotationsConfigSchema] = Field(None, description="Annotation settings")

    class Config:
        extra = "forbid"


class ThemeConfigSchema(ImplementableSchema):
    """Schema for theme configuration block."""

    enable_autodiscovery: bool = Field(
        default=True,
        description="Enable automatic theme discovery"
    )

    search_paths: List[str] = Field(
        default_factory=lambda: ["."],
        description="Paths to search for themes"
    )


class PromptFileSchema(ImplementableSchema):
    """
    Schema for .prompt.yaml files.

    Prompt files must:
    - Have type: "prompt"
    - Contain a prompt field (content to inject into parent's {prompt})
    - Have a generation configuration block
    - Implement a parent template (via implements field)
    """

    type: Literal["prompt"] = Field(
        ...,
        description="File type identifier (must be 'prompt')"
    )

    prompt: str = Field(
        ...,
        description="Prompt content to inject into parent template's {prompt} placeholder",
        min_length=1
    )

    generation: GenerationConfigSchema = Field(
        ...,
        description="Generation configuration (mode, seed, max_images)"
    )

    # Optional fields
    description: Optional[str] = Field(
        None,
        description="Human-readable description of this prompt"
    )

    output: Optional[OutputConfigSchema] = Field(
        None,
        description="Output configuration (session name, filename keys, annotations)"
    )

    themable: Optional[bool] = Field(
        None,
        description="Whether this prompt supports themes"
    )

    themes: Optional[ThemeConfigSchema] = Field(
        None,
        description="Theme configuration (autodiscovery, search paths)"
    )

    style_sensitive_placeholders: Optional[List[str]] = Field(
        None,
        description="Placeholders that are style-sensitive"
    )

    chunks: Optional[Dict[str, Any]] = Field(
        None,
        description="Reusable chunk definitions"
    )

    defaults: Optional[Dict[str, str]] = Field(
        None,
        description="Default values for placeholders"
    )

    class Config:
        extra = "forbid"  # Reject unknown fields

    @validator('prompt')
    def validate_prompt_not_empty(cls, v: str) -> str:
        """Ensure prompt is not just whitespace."""
        if not v.strip():
            raise ValueError("Prompt field cannot be empty or whitespace only")
        return v

    @validator('prompt')
    def validate_no_prompt_placeholder(cls, v: str) -> str:
        """
        Warn if prompt contains {prompt} placeholder.

        Prompts inject INTO the parent's {prompt}, they shouldn't contain it.
        """
        if '{prompt}' in v:
            raise ValueError(
                "Prompt files should not contain {prompt} placeholder. "
                "The 'prompt' field is injected into the parent template's {prompt}."
            )
        return v

    def __init__(self, **data: Any) -> None:
        """Override __init__ to explicitly check for template field."""
        if 'template' in data:
            raise ValueError(
                "Prompt files use 'prompt' field, not 'template'. "
                "Only template files use the 'template' field."
            )
        super().__init__(**data)
