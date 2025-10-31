"""
Schema validator for recursive YAML validation.

Provides recursive scanning and validation reporting for all YAML files.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
from pydantic import ValidationError

from ..schemas import (
    TemplateFileSchema,
    PromptFileSchema,
    ChunkFileSchema,
    VariationsFileSchema,
    ThemeFileSchema,
    ADetailerFileSchema,
    MultiFieldFileSchema,
)


class ValidationResult:
    """Result of validating a single file."""

    def __init__(
        self,
        file_path: Path,
        is_valid: bool,
        file_type: Optional[str] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        yaml_error: Optional[str] = None
    ):
        self.file_path = file_path
        self.is_valid = is_valid
        self.file_type = file_type
        self.errors = errors or []
        self.yaml_error = yaml_error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": str(self.file_path),
            "valid": self.is_valid,
            "type": self.file_type,
            "errors": self.errors,
            "yaml_error": self.yaml_error
        }


class SchemaValidator:
    """
    Recursive YAML schema validator.

    Scans directories for YAML files and validates them against Pydantic schemas.
    """

    def __init__(self):
        """Initialize schema validator."""
        self.schema_map = {
            'template': TemplateFileSchema,
            'prompt': PromptFileSchema,
            'chunk': ChunkFileSchema,
            'variations': VariationsFileSchema,
            'theme_config': ThemeFileSchema,
            'adetailer_config': ADetailerFileSchema,
            'multi-field': MultiFieldFileSchema,
        }

    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a single YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            ValidationResult with validation status and errors
        """
        # Load YAML
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                yaml_error=str(e)
            )
        except Exception as e:
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                yaml_error=f"Failed to read file: {e}"
            )

        # Check for type field
        if not isinstance(data, dict) or 'type' not in data:
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                errors=[{
                    "loc": ["type"],
                    "msg": "Missing required 'type' field",
                    "type": "value_error.missing"
                }]
            )

        file_type = data['type']

        # Check if type is recognized
        if file_type not in self.schema_map:
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                file_type=file_type,
                errors=[{
                    "loc": ["type"],
                    "msg": f"Unrecognized type '{file_type}'. Valid types: {', '.join(self.schema_map.keys())}",
                    "type": "value_error.const"
                }]
            )

        # Validate against schema
        schema_class = self.schema_map[file_type]
        try:
            schema_class(**data)
            return ValidationResult(
                file_path=file_path,
                is_valid=True,
                file_type=file_type
            )
        except ValidationError as e:
            errors = []
            for error in e.errors():
                errors.append({
                    "loc": [str(loc) for loc in error['loc']],
                    "msg": error['msg'],
                    "type": error['type']
                })
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                file_type=file_type,
                errors=errors
            )
        except ValueError as e:
            # Catch __init__ validation errors (like generation field in template)
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                file_type=file_type,
                errors=[{
                    "loc": ["__init__"],
                    "msg": str(e),
                    "type": "value_error"
                }]
            )
        except Exception as e:
            # Catch any other unexpected errors
            return ValidationResult(
                file_path=file_path,
                is_valid=False,
                file_type=file_type,
                errors=[{
                    "loc": ["unknown"],
                    "msg": f"Unexpected error: {type(e).__name__}: {str(e)}",
                    "type": "error"
                }]
            )

    def validate_directory(
        self,
        directory: Path,
        recursive: bool = True,
        pattern: str = "*.yaml"
    ) -> List[ValidationResult]:
        """
        Validate all YAML files in a directory.

        Args:
            directory: Directory to scan
            recursive: If True, scan subdirectories recursively
            pattern: Glob pattern for files to validate

        Returns:
            List of ValidationResult objects
        """
        results = []

        if recursive:
            files = directory.rglob(pattern)
        else:
            files = directory.glob(pattern)

        for file_path in sorted(files):
            # Skip files in .git, __pycache__, etc.
            if any(part.startswith('.') or part == '__pycache__' for part in file_path.parts):
                continue

            result = self.validate_file(file_path)
            results.append(result)

        return results

    def generate_text_report(
        self,
        results: List[ValidationResult],
        base_path: Optional[Path] = None,
        markdown: bool = False
    ) -> str:
        """
        Generate human-readable text report.

        Args:
            results: List of validation results
            base_path: Base path for relative file paths
            markdown: If True, generate Markdown format (glow-compatible)

        Returns:
            Formatted text report
        """
        lines = []

        if markdown:
            # Markdown format
            lines.append("# YAML Schema Validation Report")
            lines.append("")
        else:
            lines.append("=" * 80)
            lines.append("YAML SCHEMA VALIDATION REPORT")
            lines.append("=" * 80)
            lines.append("")

        # Summary
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid

        if markdown:
            lines.append("## Summary")
            lines.append("")
            lines.append(f"- **Total files scanned:** {total}")
            lines.append(f"- **Valid:** ✅ {valid}")
            lines.append(f"- **Invalid:** ❌ {invalid}")
            lines.append("")
        else:
            lines.append(f"Total files scanned: {total}")
            lines.append(f"Valid: {valid}")
            lines.append(f"Invalid: {invalid}")
            lines.append("")

        if invalid == 0:
            if markdown:
                lines.append("✅ **All files passed validation!**")
            else:
                lines.append("✓ All files passed validation!")
            lines.append("")
            return "\n".join(lines)

        # Errors by file
        if markdown:
            lines.append("## Validation Errors")
            lines.append("")
        else:
            lines.append("=" * 80)
            lines.append("VALIDATION ERRORS")
            lines.append("=" * 80)
            lines.append("")

        for result in results:
            if result.is_valid:
                continue

            # File path (relative if base_path provided)
            file_path = result.file_path
            if base_path:
                try:
                    file_path = result.file_path.relative_to(base_path)
                except ValueError:
                    pass

            if markdown:
                lines.append(f"### ❌ `{file_path}`")
                lines.append("")
                if result.file_type:
                    lines.append(f"**Type:** `{result.file_type}`")
                    lines.append("")
            else:
                lines.append(f"✗ {file_path}")
                if result.file_type:
                    lines.append(f"  Type: {result.file_type}")

            # YAML parsing errors
            if result.yaml_error:
                if markdown:
                    lines.append("**YAML Parse Error:**")
                    lines.append("```")
                    lines.append(result.yaml_error)
                    lines.append("```")
                else:
                    lines.append(f"  YAML Error: {result.yaml_error}")
                lines.append("")
                continue

            # Validation errors
            if result.errors:
                if markdown:
                    lines.append("**Errors:**")
                    lines.append("")
                for error in result.errors:
                    loc = " → ".join(error['loc'])
                    if markdown:
                        lines.append(f"- **{loc}:** {error['msg']}")
                        lines.append(f"  - *Type:* `{error['type']}`")
                    else:
                        lines.append(f"  • {loc}: {error['msg']}")
                        lines.append(f"    ({error['type']})")

            lines.append("")

        return "\n".join(lines)

    def generate_json_report(
        self,
        results: List[ValidationResult],
        base_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON report.

        Args:
            results: List of validation results
            base_path: Base path for relative file paths

        Returns:
            Dictionary suitable for JSON serialization
        """
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid

        files = []
        for result in results:
            file_path = result.file_path
            if base_path:
                try:
                    file_path = result.file_path.relative_to(base_path)
                except ValueError:
                    pass

            files.append({
                "file": str(file_path),
                "valid": result.is_valid,
                "type": result.file_type,
                "errors": result.errors,
                "yaml_error": result.yaml_error
            })

        return {
            "summary": {
                "total": total,
                "valid": valid,
                "invalid": invalid
            },
            "files": files
        }
