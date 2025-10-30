"""
Schema for variation files (.yaml or .variations.yaml).

Variation files contain key-value mappings for placeholder substitution.
Supports both simple variations (string values) and multi-part variations (dict values).
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import Dict, Any, Union, Literal, Optional

from .base import BaseFileSchema


class VariationsFileSchema(BaseFileSchema):
    """
    Schema for variation files (.yaml or .variations.yaml).

    Variation files must:
    - Have type: "variations"
    - Contain a variations field with key-value mappings
    - Support simple variations (string values)
    - Support multi-part variations (dict values with named parts)
    """

    type: Literal["variations"] = Field(
        ...,
        description="File type identifier (must be 'variations')"
    )

    variations: Dict[str, Union[str, Dict[str, str]]] = Field(
        ...,
        description="Key-value mappings for placeholder substitution"
    )

    # Optional fields
    description: Optional[str] = Field(
        None,
        description="Human-readable description of this variations file"
    )

    class Config:
        extra = "forbid"  # Reject unknown fields

    @validator('variations')
    def validate_variations_not_empty(cls, v: Dict[str, Union[str, Dict[str, str]]]) -> Dict[str, Union[str, Dict[str, str]]]:
        """Ensure variations dict is not empty."""
        if not v:
            raise ValueError("Variations field cannot be empty")
        return v

    @validator('variations')
    def validate_variation_values(cls, v: Dict[str, Union[str, Dict[str, str]]]) -> Dict[str, Union[str, Dict[str, str]]]:
        """
        Validate variation values.

        Simple variations: value must be string
        Multi-part variations: value must be dict with string keys and string values
        """
        for key, value in v.items():
            if isinstance(value, dict):
                # Multi-part variation - validate all parts are strings
                if not value:
                    raise ValueError(
                        f"Multi-part variation '{key}' cannot be empty. "
                        "Provide at least one named part."
                    )
                for part_name, part_value in value.items():
                    if not isinstance(part_name, str):
                        raise ValueError(
                            f"Multi-part variation '{key}' has non-string part name: {part_name}"
                        )
                    if not isinstance(part_value, str):
                        raise ValueError(
                            f"Multi-part variation '{key}' has non-string value for part '{part_name}': {type(part_value).__name__}"
                        )
                    # Check for nested dicts
                    if isinstance(part_value, dict):
                        raise ValueError(
                            f"Multi-part variation '{key}' has nested dict in part '{part_name}'. "
                            "Only one level of nesting is allowed."
                        )
            elif not isinstance(value, str):
                raise ValueError(
                    f"Variation '{key}' has invalid value type: {type(value).__name__}. "
                    "Expected string (simple variation) or dict (multi-part variation)."
                )
        return v

    @validator('variations')
    def validate_variation_keys(cls, v: Dict[str, Union[str, Dict[str, str]]]) -> Dict[str, Union[str, Dict[str, str]]]:
        """Validate variation keys are valid identifiers."""
        for key in v.keys():
            if not key:
                raise ValueError("Variation keys cannot be empty strings")
            # Check for whitespace-only keys
            if not key.strip():
                raise ValueError("Variation keys cannot be whitespace only")
        return v


class LegacyVariationsFileSchema(BaseModel):
    """
    Schema for legacy variation files without 'type' field.

    This schema supports the legacy format where variations are defined
    at the root level without a 'type' field or 'variations' wrapper.

    Example:
        short_bob: short bob cut
        long_waves: long wavy hair
    """

    # No type field for legacy format
    # No version or name required for legacy

    class Config:
        extra = "allow"  # Allow any fields (they're all variations)

    @root_validator(pre=True)
    def validate_legacy_format(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate legacy format variations.

        All root-level fields are treated as variations.
        """
        if not values:
            raise ValueError("Legacy variation file cannot be empty")

        # Check for modern format fields
        if 'type' in values:
            raise ValueError(
                "Legacy format should not have 'type' field. "
                "Use VariationsFileSchema for modern format."
            )

        # Validate all values are strings or dicts
        for key, value in values.items():
            if isinstance(value, dict):
                # Multi-part variation
                for part_name, part_value in value.items():
                    if not isinstance(part_value, str):
                        raise ValueError(
                            f"Multi-part variation '{key}' has non-string value for part '{part_name}'"
                        )
            elif not isinstance(value, str):
                raise ValueError(
                    f"Variation '{key}' has invalid value type: {type(value).__name__}"
                )

        return values
