"""
Config validator for Template System V2.0.

This module implements a 5-phase validation process that collects ALL errors
before failing, providing comprehensive feedback to the user.

Validation Phases:
    1. Structure: YAML well-formed, required fields present
    2. Paths: implements/imports files exist
    3. Inheritance: Type compatibility, no cycles
    4. Imports: No duplicate keys in merge
    5. Templates: Reserved placeholders only in allowed contexts
"""

from pathlib import Path
from typing import List, Union
import re

from .validation_error import ValidationError, ValidationResult
from ..models.config_models import TemplateConfig, ChunkConfig, PromptConfig


class ConfigValidator:
    """
    Validates configuration files through 5 phases.

    All errors are collected during validation (not fail-fast), allowing users
    to see and fix all issues at once. After validation, errors can be exported
    to JSON for logging.

    Attributes:
        loader: YamlLoader instance for loading parent files during validation
        errors: List of all validation errors collected across all phases
    """

    # Reserved placeholders that have special meaning
    RESERVED_PLACEHOLDERS = {'prompt', 'negprompt', 'loras'}

    def __init__(self, loader, parser=None):
        """
        Initialize the validator.

        Args:
            loader: YamlLoader instance for loading files during validation
            parser: ConfigParser instance for parsing variations (optional, will create if None)
        """
        self.loader = loader
        self.parser = parser
        # Lazy import to avoid circular dependency
        if self.parser is None:
            from ..loaders.parser import ConfigParser
            self.parser = ConfigParser()
        self.errors: List[ValidationError] = []

    def validate(
        self,
        config: Union[TemplateConfig, ChunkConfig, PromptConfig]
    ) -> ValidationResult:
        """
        Run complete validation (5 phases) and collect all errors.

        This method runs all validation phases even if errors are found in
        earlier phases, to provide comprehensive feedback.

        Args:
            config: Configuration object to validate

        Returns:
            ValidationResult with is_valid flag and list of all errors
        """
        # Reset errors for this validation run
        self.errors = []

        # Phase 1: Structure validation
        self._validate_structure(config)

        # Phase 2: Path validation
        self._validate_paths(config)

        # Phase 3: Inheritance validation
        self._validate_inheritance(config)

        # Phase 4: Import validation
        self._validate_imports(config)

        # Phase 5: Template validation
        self._validate_templates(config)

        # Return result
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors
        )

    def _validate_structure(
        self,
        config: Union[TemplateConfig, ChunkConfig, PromptConfig]
    ):
        """
        Phase 1: Validate structural requirements.

        Checks:
        - version field is present
        - Required fields for each config type are present
        - template field is not empty

        Args:
            config: Configuration to validate
        """
        # Check version field
        if not config.version:
            self.errors.append(ValidationError(
                type='structure',
                message='Missing required field: version',
                file=config.source_file
            ))

        # Check type-specific required fields
        if isinstance(config, TemplateConfig):
            # Template requires: name, template
            if not config.name:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: name',
                    file=config.source_file
                ))
            if not config.template:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: template',
                    file=config.source_file
                ))

        elif isinstance(config, ChunkConfig):
            # Chunk requires: type, template
            if not config.type:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: type',
                    file=config.source_file
                ))
            if not config.template:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: template',
                    file=config.source_file
                ))

        elif isinstance(config, PromptConfig):
            # Prompt requires: name, generation, template
            # Note: implements is optional (standalone prompts don't need it)
            if not config.name:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: name',
                    file=config.source_file
                ))
            if not config.generation:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: generation',
                    file=config.source_file
                ))
            if not config.template:
                self.errors.append(ValidationError(
                    type='structure',
                    message='Missing required field: template',
                    file=config.source_file
                ))

    def _validate_paths(
        self,
        config: Union[TemplateConfig, ChunkConfig, PromptConfig]
    ):
        """
        Phase 2: Validate that all referenced files exist.

        Checks:
        - implements: file exists
        - imports: all file paths exist (not inline strings)

        Args:
            config: Configuration to validate
        """
        base_path = config.source_file.parent

        # Validate implements path
        if config.implements:
            try:
                # Use allow_absolute=False to enforce relative paths in YAML
                resolved_path = self.loader.resolve_path(
                    config.implements,
                    base_path,
                    allow_absolute=False
                )
                if not resolved_path.exists():
                    self.errors.append(ValidationError(
                        type='path',
                        message=f'File not found: {config.implements}',
                        file=config.source_file,
                        name='implements'
                    ))
            except ValueError as e:
                # Catches absolute path errors
                self.errors.append(ValidationError(
                    type='path',
                    message=str(e),
                    file=config.source_file,
                    name='implements'
                ))
            except Exception as e:
                # Other path resolution errors
                self.errors.append(ValidationError(
                    type='path',
                    message=f'Path resolution error: {str(e)}',
                    file=config.source_file,
                    name='implements'
                ))

        # Validate import paths
        for import_name, import_value in config.imports.items():
            if isinstance(import_value, str):
                # Single file import
                self._validate_import_file(
                    import_value,
                    import_name,
                    base_path,
                    config.source_file
                )

            elif isinstance(import_value, list):
                # Multi-source import (files + inline strings)
                for item in import_value:
                    # Skip inline strings (not file paths)
                    if isinstance(item, str):
                        # Inline strings: start with quotes OR don't end with .yaml
                        if item.strip().startswith('"') or item.strip().startswith("'"):
                            continue
                        if not item.strip().endswith('.yaml'):
                            continue  # Skip inline strings like "frontview"
                        # It's a file path
                        self._validate_import_file(
                            item,
                            import_name,
                            base_path,
                            config.source_file
                        )

            elif isinstance(import_value, dict):
                # Nested imports (e.g., chunks: {positive: ..., negative: ...})
                for nested_name, nested_path in import_value.items():
                    if isinstance(nested_path, str):
                        self._validate_import_file(
                            nested_path,
                            f'{import_name}.{nested_name}',
                            base_path,
                            config.source_file
                        )

    def _validate_import_file(
        self,
        file_path: str,
        import_name: str,
        base_path: Path,
        source_file: Path
    ):
        """
        Validate a single import file path.

        Args:
            file_path: Path to the import file
            import_name: Name of the import for error reporting
            base_path: Base path for resolution
            source_file: Source file for error reporting
        """
        try:
            resolved_path = self.loader.resolve_path(
                file_path,
                base_path,
                allow_absolute=False
            )
            if not resolved_path.exists():
                self.errors.append(ValidationError(
                    type='path',
                    message=f'File not found: {file_path}',
                    file=source_file,
                    name=f'imports.{import_name}'
                ))
        except ValueError as e:
            # Absolute path error
            self.errors.append(ValidationError(
                type='path',
                message=str(e),
                file=source_file,
                name=f'imports.{import_name}'
            ))
        except Exception as e:
            # Other errors
            self.errors.append(ValidationError(
                type='path',
                message=f'Path resolution error: {str(e)}',
                file=source_file,
                name=f'imports.{import_name}'
            ))

    def _validate_inheritance(
        self,
        config: Union[TemplateConfig, ChunkConfig, PromptConfig]
    ):
        """
        Phase 3: Validate inheritance rules.

        Checks (for ChunkConfig only):
        - Parent chunk must have same type
        - If parent has no type, issue warning

        Note: Cycle detection is not implemented yet (would require
        full recursive resolution).

        Args:
            config: Configuration to validate
        """
        # Only validate type compatibility for chunks
        if not isinstance(config, ChunkConfig):
            return

        if not config.implements:
            return

        # Try to load parent and check type
        try:
            base_path = config.source_file.parent
            parent_path = self.loader.resolve_path(
                config.implements,
                base_path,
                allow_absolute=False
            )

            # Check if file exists (might have been caught in Phase 2)
            if not parent_path.exists():
                # Already reported in Phase 2, skip
                return

            # Load parent file
            parent_data = self.loader.load_file(parent_path, base_path)
            parent_type = parent_data.get('type')

            if parent_type and parent_type != config.type:
                # Type mismatch - ERROR
                self.errors.append(ValidationError(
                    type='inheritance',
                    message=(
                        f'Type mismatch: {config.source_file.name} ({config.type}) '
                        f'cannot implement {parent_path.name} ({parent_type})'
                    ),
                    file=config.source_file,
                    details={
                        'child_type': config.type,
                        'parent_type': parent_type,
                        'parent_file': str(parent_path)
                    }
                ))
            elif not parent_type:
                # Parent has no type - WARNING
                self.errors.append(ValidationError(
                    type='inheritance',
                    message=(
                        f'Warning: {parent_path.name} has no type field, '
                        f'assuming type "{config.type}"'
                    ),
                    file=config.source_file,
                    details={
                        'assumed_type': config.type,
                        'parent_file': str(parent_path)
                    }
                ))

        except Exception:
            # Error already caught in Phase 2 (path validation)
            # or YAML parsing error - don't duplicate errors
            pass

    def _validate_imports(
        self,
        config: Union[TemplateConfig, ChunkConfig, PromptConfig]
    ):
        """
        Phase 4: Validate import merge rules.

        Note: Duplicate key validation is now handled by ImportResolver
        with automatic prefixing, so this phase is currently a no-op.
        Kept for future validation rules if needed.

        Args:
            config: Configuration to validate
        """
        # Duplicate keys are now handled by ImportResolver with auto-prefixing
        # No validation needed here
        pass

    def _validate_multi_source_import(
        self,
        import_name: str,
        sources: list,
        base_path: Path,
        source_file: Path
    ):
        """
        Validate a multi-source import for duplicate keys.

        Args:
            import_name: Name of the import
            sources: List of file paths and inline strings
            base_path: Base path for resolution
            source_file: Source file for error reporting
        """
        seen_keys = {}  # key -> source file where it was first seen

        for source in sources:
            # Skip inline strings (they get auto-generated keys)
            if isinstance(source, str):
                if source.startswith('"') or source.startswith("'"):
                    continue

            # Try to load the file and check for duplicate keys
            try:
                resolved_path = self.loader.resolve_path(
                    source,
                    base_path,
                    allow_absolute=False
                )

                if not resolved_path.exists():
                    # Already reported in Phase 2
                    continue

                # Load variation file
                data = self.loader.load_file(resolved_path, base_path)

                if not isinstance(data, dict):
                    # Invalid format, but not our concern in this phase
                    continue

                # Parse variations to extract only the variation keys (not metadata)
                # This handles both structured format (with type/name/version/variations keys)
                # and flat format (direct key-value pairs)
                try:
                    variations = self.parser.parse_variations(data)
                except Exception:
                    # Parse error - skip this file (will be caught elsewhere)
                    continue

                # Check each variation key for duplicates
                for key in variations.keys():
                    if key in seen_keys:
                        # Duplicate key found!
                        self.errors.append(ValidationError(
                            type='import',
                            message=(
                                f"Duplicate key '{key}' in {import_name} imports "
                                f"(found in {seen_keys[key]} and {source})"
                            ),
                            file=source_file,
                            name=import_name,
                            details={
                                'key': key,
                                'source1': seen_keys[key],
                                'source2': source
                            }
                        ))
                    else:
                        seen_keys[key] = source

            except Exception:
                # File error or YAML parse error
                # Already reported in Phase 2 or will be caught elsewhere
                pass

    def _validate_templates(
        self,
        config: Union[TemplateConfig, ChunkConfig, PromptConfig]
    ):
        """
        Phase 5: Validate template strings.

        Checks:
        - Reserved placeholders ({prompt}, {negprompt}, {loras}) are NOT
          used in ChunkConfig templates
        - Reserved placeholders ARE allowed in TemplateConfig and PromptConfig

        Args:
            config: Configuration to validate
        """
        # For chunks: DISALLOW reserved placeholders
        if isinstance(config, ChunkConfig):
            template = config.template
            for reserved in self.RESERVED_PLACEHOLDERS:
                # Case-insensitive search for {reserved}
                pattern = r'\{' + reserved + r'\}'
                if re.search(pattern, template, re.IGNORECASE):
                    self.errors.append(ValidationError(
                        type='template',
                        message=f'Reserved placeholder {{{reserved}}} not allowed in chunks',
                        file=config.source_file,
                        name=reserved
                    ))

        # For templates and prompts: reserved placeholders are OK
        # (they are meant to be used there)
