"""
Schema for theme.yaml files.

Theme files define theme-specific variation overrides with style support.
"""

from pydantic import Field, validator, model_validator
from typing import Dict, Any, List, Literal, Union, Optional

from .base import BaseFileSchema


# Sentinel value for [Remove] directive
REMOVE_DIRECTIVE = "[Remove]"


class ThemeFileSchema(BaseFileSchema):
    """
    Schema for theme.yaml files.

    Theme files must:
    - Have type: "theme_config"
    - Contain imports mapping placeholders to variation files
    - Support style-specific imports (PlaceholderName.style notation)
    - Support [Remove] directive to remove placeholders for specific styles
    - List active variations in variations field
    """

    type: Literal["theme_config"] = Field(
        ...,
        description="File type identifier (must be 'theme_config')"
    )

    imports: Dict[str, Union[str, List[str]]] = Field(
        ...,
        description="Import mappings for placeholders (with optional style notation)"
    )

    variations: List[str] = Field(
        ...,
        description="List of active variation placeholder names"
    )

    # Optional fields
    description: Optional[str] = Field(
        None,
        description="Human-readable description of this theme"
    )

    class Config:
        extra = "forbid"  # Reject unknown fields

    @validator('imports')
    def validate_imports_not_empty(cls, v: Dict[str, Union[str, List[str]]]) -> Dict[str, Union[str, List[str]]]:
        """Ensure imports dict is not empty."""
        if not v:
            raise ValueError("Imports field cannot be empty in theme files")
        return v

    @validator('imports')
    def validate_import_values(cls, v: Dict[str, Union[str, List[str]]]) -> Dict[str, Union[str, List[str]]]:
        """
        Validate import values.

        Values can be:
        - String: path to variation file
        - List with single element: must be exactly [Remove] (case-sensitive)
        """
        for placeholder_name, value in v.items():
            if isinstance(value, list):
                # Check if [Remove] directive
                if len(value) != 1:
                    raise ValueError(
                        f"Import '{placeholder_name}' has list value with {len(value)} elements. "
                        f"Expected either a string path or [Remove] directive (single-element list)."
                    )
                if value[0] != "Remove":
                    raise ValueError(
                        f"Import '{placeholder_name}' has list value [{value[0]}]. "
                        f"Expected exactly [Remove] (case-sensitive) for remove directive."
                    )
            elif isinstance(value, str):
                # File path - validate ends with .yaml or .yml
                if not (value.endswith('.yaml') or value.endswith('.yml')):
                    raise ValueError(
                        f"Import '{placeholder_name}' has invalid file path '{value}'. "
                        f"Must end with .yaml or .yml"
                    )
            else:
                raise ValueError(
                    f"Import '{placeholder_name}' has invalid value type: {type(value).__name__}. "
                    f"Expected string (file path) or list ([Remove])."
                )
        return v

    @validator('imports')
    def validate_import_keys(cls, v: Dict[str, Union[str, List[str]]]) -> Dict[str, Union[str, List[str]]]:
        """
        Validate import keys (placeholder names with optional style notation).

        Valid formats:
        - PlaceholderName (default import)
        - PlaceholderName.style (style-specific import)
        """
        for key in v.keys():
            if not key:
                raise ValueError("Import keys cannot be empty strings")

            # Check for style notation (PlaceholderName.style)
            parts = key.split('.')
            if len(parts) > 2:
                raise ValueError(
                    f"Import key '{key}' has invalid format. "
                    f"Expected 'PlaceholderName' or 'PlaceholderName.style'"
                )

            # Validate placeholder name (before dot)
            placeholder_name = parts[0]
            if not placeholder_name:
                raise ValueError(
                    f"Import key '{key}' has empty placeholder name before dot"
                )

            # Validate style name (after dot) if present
            if len(parts) == 2:
                style_name = parts[1]
                if not style_name:
                    raise ValueError(
                        f"Import key '{key}' has empty style name after dot"
                    )

        return v

    @validator('variations')
    def validate_variations_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure variations list is not empty."""
        if not v:
            raise ValueError("Variations field cannot be empty in theme files")
        return v

    @validator('variations')
    def validate_variation_names(cls, v: List[str]) -> List[str]:
        """Validate variation names are valid identifiers."""
        for variation_name in v:
            if not variation_name:
                raise ValueError("Variation names cannot be empty strings")
            if not variation_name.strip():
                raise ValueError("Variation names cannot be whitespace only")
        return v

    @model_validator(mode='after')
    def validate_variations_in_imports(self) -> 'ThemeFileSchema':
        """
        Validate that all variations listed exist in imports (ignoring style suffixes).

        Example:
        - variations: [Hair, Outfit]
        - imports: {Hair: path1, Outfit.safe: path2, Outfit.spicy: path3}
        - Valid because both Hair and Outfit have at least one import
        """
        variations = self.variations
        imports = self.imports

        if not variations or not imports:
            return self

        # Extract base placeholder names from import keys (strip .style suffix)
        import_base_names = set()
        for key in imports.keys():
            base_name = key.split('.')[0]
            import_base_names.add(base_name)

        # Check each variation has at least one import
        for variation_name in variations:
            if variation_name not in import_base_names:
                raise ValueError(
                    f"Variation '{variation_name}' listed in variations field "
                    f"but no corresponding import found in imports"
                )

        return self
