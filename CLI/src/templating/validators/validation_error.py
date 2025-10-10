"""
Validation error models for Template System V2.0.

This module defines error types used during the 5-phase validation process.
"""

from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path


@dataclass
class ValidationError:
    """
    Model for a single validation error.

    Attributes:
        type: Error type ('structure', 'path', 'inheritance', 'import', 'template')
        message: Human-readable error message
        file: Path to the file where the error occurred (optional)
        line: Line number in the file (optional)
        name: Name of the field/import causing the error (optional)
        details: Additional error details as a dictionary (optional)
    """
    type: str
    message: str
    file: Optional[Path] = None
    line: Optional[int] = None
    name: Optional[str] = None
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        """
        Convert error to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the error
        """
        return {
            'type': self.type,
            'message': self.message,
            'file': str(self.file) if self.file else None,
            'line': self.line,
            'name': self.name,
            'details': self.details
        }


@dataclass
class ValidationResult:
    """
    Result of the complete validation process.

    Attributes:
        is_valid: True if no errors were found, False otherwise
        errors: List of all validation errors collected during the 5 phases
    """
    is_valid: bool
    errors: List[ValidationError]

    @property
    def error_count(self) -> int:
        """Get the total number of errors."""
        return len(self.errors)

    def to_json(self) -> dict:
        """
        Export validation result as JSON for logging.

        Returns:
            Dictionary with errors and count for JSON serialization
        """
        return {
            'errors': [e.to_dict() for e in self.errors],
            'count': self.error_count
        }
