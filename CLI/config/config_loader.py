"""
Configuration Loader & Validator for JSON Config System (SF-1)

Loads and validates JSON configuration files with comprehensive error checking.
"""

import json
from pathlib import Path
from typing import List, Set, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from variation_loader import extract_placeholders
from config.config_schema import (
    GenerationSessionConfig,
    ValidationResult,
    ValidationError
)


# Valid enum values
VALID_GENERATION_MODES = {"combinatorial", "random", "ask"}
VALID_SEED_MODES = {"fixed", "progressive", "random", "ask"}


def load_config_from_file(path: Path) -> GenerationSessionConfig:
    """
    Load configuration from JSON file.

    Args:
        path: Path to JSON configuration file

    Returns:
        GenerationSessionConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If JSON is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {path}: {e}")
    except Exception as e:
        raise ValueError(f"Error reading config file {path}: {e}")

    return GenerationSessionConfig.from_dict(data)


def validate_required_fields(config: GenerationSessionConfig, result: ValidationResult) -> None:
    """
    Validate required fields are present.

    Args:
        config: Configuration to validate
        result: ValidationResult to add errors to
    """
    # Version
    if not config.version:
        result.add_error("version", "Version is required", "Add: \"version\": \"1.0\"")

    # Prompt template
    if not config.prompt.template:
        result.add_error("prompt.template", "Prompt template is required",
                         "Add a prompt with placeholders like: \"masterpiece, {Expression}, beautiful\"")

    # Variations
    if not config.variations:
        result.add_error("variations", "At least one variation file is required",
                         "Add variation files mapping, e.g. {\"Expression\": \"/path/to/file.txt\"}")


def validate_field_types(config: GenerationSessionConfig, result: ValidationResult) -> None:
    """
    Validate field types and ranges.

    Args:
        config: Configuration to validate
        result: ValidationResult to add errors to
    """
    # Generation mode
    if config.generation.mode not in VALID_GENERATION_MODES:
        result.add_error(
            "generation.mode",
            f"Invalid generation mode: '{config.generation.mode}'",
            f"Valid values: {', '.join(sorted(VALID_GENERATION_MODES))}"
        )

    # Seed mode
    if config.generation.seed_mode not in VALID_SEED_MODES:
        result.add_error(
            "generation.seed_mode",
            f"Invalid seed mode: '{config.generation.seed_mode}'",
            f"Valid values: {', '.join(sorted(VALID_SEED_MODES))}"
        )

    # Numeric parameters (only validate if not -1, which means "ask")
    if config.parameters.width != -1 and config.parameters.width <= 0:
        result.add_error("parameters.width", "Width must be positive or -1 (ask user)")

    if config.parameters.height != -1 and config.parameters.height <= 0:
        result.add_error("parameters.height", "Height must be positive or -1 (ask user)")

    if config.parameters.steps != -1 and config.parameters.steps <= 0:
        result.add_error("parameters.steps", "Steps must be positive or -1 (ask user)")

    if config.parameters.cfg_scale != -1.0 and config.parameters.cfg_scale <= 0:
        result.add_error("parameters.cfg_scale", "CFG scale must be positive or -1 (ask user)")

    if config.parameters.batch_size != -1 and config.parameters.batch_size <= 0:
        result.add_error("parameters.batch_size", "Batch size must be positive or -1 (ask user)")

    if config.parameters.batch_count != -1 and config.parameters.batch_count <= 0:
        result.add_error("parameters.batch_count", "Batch count must be positive or -1 (ask user)")


def validate_variation_files(config: GenerationSessionConfig, result: ValidationResult) -> None:
    """
    Validate variation file paths exist.

    Args:
        config: Configuration to validate
        result: ValidationResult to add errors to
    """
    for placeholder_name, file_path in config.variations.items():
        path = Path(file_path)

        if not path.exists():
            result.add_error(
                f"variations.{placeholder_name}",
                f"Variation file not found: {file_path}",
                "Check that the path is correct and the file exists"
            )
        elif not path.is_file():
            result.add_error(
                f"variations.{placeholder_name}",
                f"Path is not a file: {file_path}",
                "Provide a path to a text file containing variations"
            )
        elif not os.access(path, os.R_OK):
            result.add_error(
                f"variations.{placeholder_name}",
                f"File is not readable: {file_path}",
                "Check file permissions"
            )


def validate_placeholders_match(config: GenerationSessionConfig, result: ValidationResult) -> None:
    """
    Validate placeholders in prompt match variation files.

    Args:
        config: Configuration to validate
        result: ValidationResult to add errors to
    """
    # Extract placeholders from prompt template
    placeholders = extract_placeholders(config.prompt.template)

    # Get variation keys
    variation_keys = set(config.variations.keys())

    # Check for missing variations
    missing_variations = placeholders - variation_keys
    for placeholder in missing_variations:
        result.add_error(
            f"variations.{placeholder}",
            f"Placeholder '{{{placeholder}}}' in prompt has no variation file",
            f"Add variation file for '{placeholder}' in variations section"
        )

    # Warn about unused variations
    unused_variations = variation_keys - placeholders
    for unused in unused_variations:
        result.add_warning(
            f"variations.{unused}",
            f"Variation file defined but placeholder '{{{unused}}}' not used in prompt",
            f"Either add '{{{unused}}}' to prompt or remove from variations"
        )


def validate_filename_keys(config: GenerationSessionConfig, result: ValidationResult) -> None:
    """
    Validate filename_keys reference existing variations.

    Args:
        config: Configuration to validate
        result: ValidationResult to add errors to
    """
    if not config.output.filename_keys:
        return  # Optional field, empty is valid

    variation_keys = set(config.variations.keys())

    for key in config.output.filename_keys:
        if key not in variation_keys:
            result.add_error(
                f"output.filename_keys",
                f"Filename key '{key}' not found in variations",
                f"Available keys: {', '.join(sorted(variation_keys))}"
            )


def validate_sampler(config: GenerationSessionConfig, result: ValidationResult,
                     available_samplers: Optional[List[str]] = None) -> None:
    """
    Validate sampler name.

    Args:
        config: Configuration to validate
        result: ValidationResult to add errors to
        available_samplers: List of available samplers from SD API (optional)
    """
    sampler = config.parameters.sampler

    # "ask" is always valid
    if sampler == "ask":
        return

    # If we have sampler list from API, validate against it
    if available_samplers is not None:
        if sampler not in available_samplers:
            result.add_error(
                "parameters.sampler",
                f"Sampler '{sampler}' not available in Stable Diffusion API",
                f"Use 'ask' or one of: {', '.join(available_samplers[:5])}..."
            )


def validate_config(config: GenerationSessionConfig,
                    available_samplers: Optional[List[str]] = None) -> ValidationResult:
    """
    Perform comprehensive validation of configuration.

    Args:
        config: Configuration to validate
        available_samplers: List of available samplers from SD API (optional)

    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult()

    # Run all validation checks
    validate_required_fields(config, result)
    validate_field_types(config, result)
    validate_variation_files(config, result)
    validate_placeholders_match(config, result)
    validate_filename_keys(config, result)
    validate_sampler(config, result, available_samplers)

    return result


def load_and_validate_config(path: Path,
                              available_samplers: Optional[List[str]] = None) -> tuple[GenerationSessionConfig, ValidationResult]:
    """
    Load and validate configuration in one step.

    Args:
        path: Path to JSON configuration file
        available_samplers: List of available samplers from SD API (optional)

    Returns:
        Tuple of (config, validation_result)

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If JSON is invalid
    """
    config = load_config_from_file(path)
    result = validate_config(config, available_samplers)
    return config, result


# Import os for file access check
import os
