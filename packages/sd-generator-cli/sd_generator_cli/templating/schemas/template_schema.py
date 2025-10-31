"""
Schema for .template.yaml files.

Template files are base configurations that contain a {prompt} placeholder
and are meant to be inherited by prompt files via the implements field.
"""

from pydantic import Field, validator
from typing import Optional, Dict, Any, Literal, List

from .base import ImplementableSchema


class TemplateFileSchema(ImplementableSchema):
    """
    Schema for .template.yaml files.

    Template files must:
    - Have type: "template"
    - Contain a template field with {prompt} placeholder
    - NOT have a generation field (not executable)
    - NOT have a prompt field (use template instead)
    """

    type: Literal["template"] = Field(
        ...,
        description="File type identifier (must be 'template')"
    )

    template: str = Field(
        ...,
        description="Template string containing {prompt} placeholder",
        min_length=1
    )

    # Optional fields
    description: Optional[str] = Field(
        None,
        description="Human-readable description of this template"
    )

    chunks: Optional[Dict[str, Any]] = Field(
        None,
        description="Reusable chunk definitions"
    )

    defaults: Optional[Dict[str, str]] = Field(
        None,
        description="Default values for placeholders"
    )

    # Theme support (themable templates)
    themes: Optional[Dict[str, Any]] = Field(
        None,
        description="Theme autodiscovery configuration"
    )

    style_sensitive_placeholders: Optional[List[str]] = Field(
        None,
        description="List of placeholders that vary by style (safe/sexy/xxx)"
    )

    prompts: Optional[Dict[str, str]] = Field(
        None,
        description="Default prompt mappings"
    )

    output: Optional[Dict[str, Any]] = Field(
        None,
        description="Output configuration (session_name, filename_keys)"
    )

    class Config:
        extra = "forbid"  # Reject unknown fields

    @validator('template')
    def validate_template_has_prompt(cls, v: str) -> str:
        """Ensure template contains {prompt} placeholder."""
        if '{prompt}' not in v:
            raise ValueError(
                "Template file must contain {prompt} placeholder. "
                "This is what child prompt files inject their content into."
            )
        return v

    @validator('type')
    def validate_no_generation_field(cls, v: str, values: Dict[str, Any]) -> str:
        """
        Ensure template files don't have generation field.

        Note: This validator runs after all fields are parsed, so we can't
        directly check for 'generation' in values. Instead, we rely on
        extra="forbid" to reject unknown fields like 'generation'.
        """
        return v

    def __init__(self, **data: Any) -> None:
        """Override __init__ to explicitly reject generation field."""
        if 'generation' in data:
            raise ValueError(
                "Template files cannot have 'generation' field. "
                "Templates are not executable - they are inherited by prompt files."
            )
        if 'prompt' in data:
            raise ValueError(
                "Template files use 'template' field, not 'prompt'. "
                "Only prompt files use the 'prompt' field."
            )
        super().__init__(**data)
