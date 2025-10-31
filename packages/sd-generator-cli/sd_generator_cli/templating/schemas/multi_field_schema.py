"""
Schema for multi-field files (*_combined.yaml).

Multi-field files combine multiple variation sources into a single namespace.
They reference other variation files and merge them according to a strategy.
"""

from pydantic import Field, validator
from typing import Optional, List, Literal

from .base import BaseFileSchema


class MultiFieldFileSchema(BaseFileSchema):
    """
    Schema for multi-field files (*_combined.yaml).

    Multi-field files must:
    - Have type: "multi-field"
    - Contain sources list (paths to variation files to combine)
    - Specify merge_strategy (how to combine the sources)
    """

    type: Literal["multi-field"] = Field(
        ...,
        description="File type identifier (must be 'multi-field')"
    )

    sources: List[str] = Field(
        ...,
        description="List of variation file paths to combine"
    )

    merge_strategy: str = Field(
        ...,
        description="Strategy for merging sources (e.g., 'combine', 'override', 'append')"
    )

    # Optional fields
    description: Optional[str] = Field(
        None,
        description="Human-readable description of this multi-field config"
    )

    class Config:
        extra = "forbid"  # Reject unknown fields

    @validator('sources')
    def validate_sources_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure sources list is not empty."""
        if not v:
            raise ValueError("sources field cannot be empty")
        return v

    @validator('sources')
    def validate_source_paths(cls, v: List[str]) -> List[str]:
        """Validate source paths end with .yaml or .yml."""
        for source_path in v:
            if not source_path:
                raise ValueError("Source paths cannot be empty strings")
            if not (source_path.endswith('.yaml') or source_path.endswith('.yml')):
                raise ValueError(
                    f"Source path '{source_path}' must end with .yaml or .yml"
                )
        return v

    @validator('merge_strategy')
    def validate_merge_strategy(cls, v: str) -> str:
        """Validate merge strategy is not empty."""
        if not v or not v.strip():
            raise ValueError("merge_strategy cannot be empty")
        return v
