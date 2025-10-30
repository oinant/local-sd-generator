"""
Base schema classes for YAML file validation.

Provides common base classes and validators used across all schema types.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional


class BaseFileSchema(BaseModel):
    """
    Base schema for all YAML configuration files.

    Common fields present in all file types.
    """

    version: str = Field(
        default="2.0",
        description="Schema version"
    )

    name: str = Field(
        ...,
        description="Configuration name",
        min_length=1
    )

    class Config:
        extra = "forbid"  # Reject unknown fields for strict validation

    @validator('version')
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        if v not in ["1.0", "2.0"]:
            raise ValueError(
                f"Invalid version '{v}'. Expected '1.0' or '2.0'."
            )
        return v


class ImplementableSchema(BaseFileSchema):
    """
    Base schema for files that support inheritance (implements field).

    Used by TemplateFileSchema, PromptFileSchema, and ChunkFileSchema.
    """

    implements: Optional[str] = Field(
        None,
        description="Path to parent file to inherit from"
    )

    imports: Dict[str, Any] = Field(
        default_factory=dict,
        description="Import mappings for placeholders"
    )

    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Generation parameters"
    )

    negative_prompt: Optional[str] = Field(
        None,
        description="Negative prompt text"
    )

    @validator('implements')
    def validate_implements_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate implements path format."""
        if v is not None:
            if not (v.endswith('.yaml') or v.endswith('.yml')):
                raise ValueError(
                    f"Invalid implements path '{v}'. "
                    f"Must end with .yaml or .yml"
                )
        return v
