"""
YAML file loader for Template System V2.0.

This module handles loading of YAML files with proper path resolution.
All paths are resolved relative to a base path for portability across systems.
Includes Pydantic schema validation for explicit type checking.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml
from pydantic import ValidationError

from ..schemas import (
    TemplateFileSchema,
    PromptFileSchema,
    ChunkFileSchema,
    VariationsFileSchema,
    ThemeFileSchema,
)
from ..schemas.variations_schema import LegacyVariationsFileSchema


class YamlLoader:
    """
    Loads YAML files with relative path resolution.

    All paths are resolved relative to a base path to ensure portability.
    No caching is used - files are loaded fresh each time for simplicity.
    Supports optional Pydantic schema validation for explicit type checking.
    """

    def __init__(self, strict_validation: bool = False):
        """
        Initialize the YAML loader.

        Args:
            strict_validation: If True, validation errors raise exceptions.
                             If False, validation errors are warnings only.
        """
        self.strict_validation = strict_validation

    def load_file(
        self,
        path: Path | str,
        base_path: Optional[Path] = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Load a YAML file with optional schema validation.

        Args:
            path: Path to the YAML file (relative or absolute).
                  Absolute paths are allowed as entry points (e.g., loading the root config).
            base_path: Base directory for resolving relative paths.
                      If None, uses current working directory.
            validate: If True, validates YAML against Pydantic schemas.

        Returns:
            Dictionary containing the parsed YAML data

        Raises:
            FileNotFoundError: If the file does not exist
            yaml.YAMLError: If the YAML is malformed
            ValidationError: If validation is enabled, strict mode is on, and validation fails
        """
        # Allow absolute paths for entry points (direct load_file calls)
        resolved_path = self.resolve_path(path, base_path, allow_absolute=True)

        # Check file exists
        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {resolved_path}")

        # Load and parse YAML
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML in {resolved_path}: {e}")

        # Validate if requested
        if validate:
            self.validate_yaml(data, resolved_path)

        return data

    def resolve_path(self, path: Path | str, base_path: Optional[Path] = None,
                     allow_absolute: bool = False) -> Path:
        """
        Resolve a path relative to a base path.

        This method ensures all paths are resolved consistently. By default,
        absolute paths are rejected for portability within YAML files
        (implements/imports), but can be allowed for entry points.

        Args:
            path: Path to resolve (string or Path object)
            base_path: Base directory for relative resolution.
                      If None and path is relative, uses current working directory.
            allow_absolute: If True, allows absolute paths. Use for entry points only.

        Returns:
            Absolute Path object resolved relative to base_path (or as-is if absolute)

        Raises:
            ValueError: If path is absolute and allow_absolute is False
        """
        path = Path(path)

        # If absolute path
        if path.is_absolute():
            if not allow_absolute:
                raise ValueError(
                    f"Absolute paths are not supported for portability: {path}. "
                    f"Please use relative paths instead."
                )
            # Allow absolute paths for entry points (direct load_file calls)
            return path.resolve()

        # Relative path resolution
        # Use current directory if no base_path provided
        if base_path is None:
            base_path = Path.cwd()

        # Resolve relative to base_path
        resolved = (base_path / path).resolve()
        return resolved

    def validate_yaml(
        self,
        data: Dict[str, Any],
        file_path: Optional[Path] = None
    ) -> Optional[Union[TemplateFileSchema, PromptFileSchema, ChunkFileSchema,
                        VariationsFileSchema, ThemeFileSchema]]:
        """
        Validate YAML data against appropriate Pydantic schema.

        This method detects the file type based on the 'type' field and validates
        against the corresponding schema. Returns validated schema object if successful.

        Args:
            data: Parsed YAML data dictionary
            file_path: Optional file path for error messages

        Returns:
            Validated Pydantic schema object if validation succeeds, None if soft mode

        Raises:
            ValidationError: If strict_validation=True and validation fails
            ValueError: If 'type' field is missing or unrecognized
        """
        file_str = str(file_path) if file_path else "unknown file"

        # Check for type field
        if 'type' not in data:
            error_msg = (
                f"Missing 'type' field in {file_str}. "
                f"All YAML files must have explicit 'type' field. "
                f"Valid types: template, prompt, chunk, variations, theme_config"
            )
            if self.strict_validation:
                raise ValueError(error_msg)
            else:
                print(f"⚠️  WARNING: {error_msg}")
                return None

        file_type = data['type']

        # Map type to schema
        schema_map = {
            'template': TemplateFileSchema,
            'prompt': PromptFileSchema,
            'chunk': ChunkFileSchema,
            'variations': VariationsFileSchema,
            'theme_config': ThemeFileSchema,
        }

        if file_type not in schema_map:
            error_msg = (
                f"Unrecognized 'type' field '{file_type}' in {file_str}. "
                f"Valid types: {', '.join(schema_map.keys())}"
            )
            if self.strict_validation:
                raise ValueError(error_msg)
            else:
                print(f"⚠️  WARNING: {error_msg}")
                return None

        # Validate against schema
        schema_class = schema_map[file_type]
        try:
            validated = schema_class(**data)
            return validated
        except ValidationError as e:
            error_msg = f"Validation failed for {file_str}:\n{e}"
            if self.strict_validation:
                raise ValidationError(e.errors(), schema_class) from e
            else:
                print(f"⚠️  WARNING: {error_msg}")
                return None
