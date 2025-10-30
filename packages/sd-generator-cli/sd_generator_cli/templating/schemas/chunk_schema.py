"""
Schema for .chunk.yaml files.

Chunk files are reusable template fragments that can be imported
into templates, prompts, or other chunks.
"""

from pydantic import Field, validator
from typing import Optional, Dict, Any, Literal

from .base import ImplementableSchema


class ChunkFileSchema(ImplementableSchema):
    """
    Schema for .chunk.yaml files.

    Chunk files must:
    - Have type: "chunk"
    - Contain a template field (reusable fragment)
    - NOT contain {prompt} placeholder (reserved for templates)
    - NOT have a generation field (not executable)
    - NOT have a prompt field (use template instead)
    """

    type: Literal["chunk"] = Field(
        ...,
        description="File type identifier (must be 'chunk')"
    )

    template: str = Field(
        ...,
        description="Template fragment (can use placeholders but NOT {prompt})",
        min_length=1
    )

    # Optional fields
    description: Optional[str] = Field(
        None,
        description="Human-readable description of this chunk"
    )

    chunks: Optional[Dict[str, Any]] = Field(
        None,
        description="Nested chunk definitions"
    )

    defaults: Optional[Dict[str, str]] = Field(
        None,
        description="Default values for placeholders"
    )

    class Config:
        extra = "forbid"  # Reject unknown fields

    @validator('template')
    def validate_no_prompt_placeholder(cls, v: str) -> str:
        """
        Ensure chunk template doesn't contain {prompt} placeholder.

        {prompt} is reserved for base templates that are inherited by prompts.
        Chunks are reusable fragments and shouldn't use {prompt}.
        """
        if '{prompt}' in v:
            raise ValueError(
                "Chunk files cannot contain {prompt} placeholder. "
                "{prompt} is reserved for template files that are inherited by prompt files. "
                "Use a different placeholder name for chunks."
            )
        return v

    @validator('template')
    def validate_template_not_empty(cls, v: str) -> str:
        """Ensure template is not just whitespace."""
        if not v.strip():
            raise ValueError("Template field cannot be empty or whitespace only")
        return v

    def __init__(self, **data: Any) -> None:
        """Override __init__ to explicitly reject generation and prompt fields."""
        if 'generation' in data:
            raise ValueError(
                "Chunk files cannot have 'generation' field. "
                "Chunks are reusable fragments - they are not executable."
            )
        if 'prompt' in data:
            raise ValueError(
                "Chunk files use 'template' field, not 'prompt'. "
                "Only prompt files use the 'prompt' field."
            )
        super().__init__(**data)
