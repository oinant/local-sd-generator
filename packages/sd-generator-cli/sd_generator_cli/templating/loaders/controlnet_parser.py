"""Parser for .controlnet.yaml preset files.

This module handles loading and validation of ControlNet preset files,
following the same pattern as adetailer_parser.py.
"""

import yaml
from pathlib import Path
from typing import Any

from ..models.controlnet import ControlNetUnit, ControlNetConfig


class ControlNetParseError(Exception):
    """Raised when ControlNet preset file parsing fails."""
    pass


def parse_controlnet_file(file_path: str | Path) -> ControlNetConfig:
    """Parse a .controlnet.yaml preset file.

    Args:
        file_path: Path to .controlnet.yaml file

    Returns:
        ControlNetConfig with parsed units

    Raises:
        ControlNetParseError: If file is invalid or malformed
        FileNotFoundError: If file doesn't exist

    Example:
        >>> config = parse_controlnet_file("presets/canny.controlnet.yaml")
        >>> len(config.units)
        1
        >>> config.units[0].model
        'control_v11p_sd15_canny'
    """
    file_path = Path(file_path)

    # Check file exists
    if not file_path.exists():
        raise FileNotFoundError(f"ControlNet preset file not found: {file_path}")

    # Load YAML
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ControlNetParseError(f"Invalid YAML in {file_path}: {e}")

    # Validate structure
    if not isinstance(data, dict):
        raise ControlNetParseError(f"ControlNet file must be a YAML dict: {file_path}")

    # Validate type
    if data.get('type') != 'controlnet_config':
        raise ControlNetParseError(
            f"Invalid type in {file_path}. "
            f"Expected 'controlnet_config', got '{data.get('type')}'"
        )

    # Validate version
    if data.get('version') != '1.0':
        raise ControlNetParseError(
            f"Invalid version in {file_path}. "
            f"Expected '1.0', got '{data.get('version')}'"
        )

    # Validate units array
    units_data = data.get('units')
    if not units_data:
        raise ControlNetParseError(f"ControlNet file must have 'units' array: {file_path}")

    if not isinstance(units_data, list):
        raise ControlNetParseError(f"'units' must be an array: {file_path}")

    # Parse units
    units: list[ControlNetUnit] = []
    for idx, unit_data in enumerate(units_data):
        if not isinstance(unit_data, dict):
            raise ControlNetParseError(
                f"Unit #{idx} in {file_path} must be a dict"
            )

        # Validate required field
        if 'model' not in unit_data:
            raise ControlNetParseError(
                f"Unit #{idx} in {file_path} missing required field 'model'"
            )

        try:
            unit = ControlNetUnit(**unit_data)
            units.append(unit)
        except TypeError as e:
            raise ControlNetParseError(
                f"Invalid unit #{idx} in {file_path}: {e}"
            )

    return ControlNetConfig(units=units)


def resolve_controlnet_parameter(
    value: Any,
    base_path: str | Path
) -> Optional[ControlNetConfig]:
    """Resolve parameters.controlnet field.

    Supports 3 formats:
    1. String: Path to .controlnet.yaml file
    2. List: Multiple files + optional overrides
    3. Dict: Inline unit configuration

    Args:
        value: The controlnet parameter value (str | list | dict | None)
        base_path: Base directory for resolving relative paths

    Returns:
        ControlNetConfig or None if value is None

    Example:
        >>> # Format 1: String path
        >>> config = resolve_controlnet_parameter(
        ...     "presets/canny.controlnet.yaml",
        ...     "/configs"
        ... )

        >>> # Format 2: List with overrides
        >>> config = resolve_controlnet_parameter(
        ...     ["presets/canny.controlnet.yaml", {"weight": 0.8}],
        ...     "/configs"
        ... )

        >>> # Format 3: Inline dict
        >>> config = resolve_controlnet_parameter(
        ...     {"model": "control_v11p_sd15_canny", "module": "canny"},
        ...     "/configs"
        ... )
    """
    if value is None:
        return None

    base_path = Path(base_path)

    # Format 1: String (single file path)
    if isinstance(value, str):
        file_path = base_path / value if not Path(value).is_absolute() else Path(value)
        return parse_controlnet_file(file_path)

    # Format 2: List (multiple files + overrides)
    elif isinstance(value, list):
        units: list[ControlNetUnit] = []
        overrides: Optional[dict] = None

        for item in value:
            if isinstance(item, str):
                # Parse file and add units
                file_path = base_path / item if not Path(item).is_absolute() else Path(item)
                config = parse_controlnet_file(file_path)
                units.extend(config.units)

            elif isinstance(item, dict):
                # Store overrides for first unit
                if overrides is None:
                    overrides = item

        if units:
            # Apply overrides to first unit
            if overrides:
                for key, val in overrides.items():
                    if hasattr(units[0], key):
                        setattr(units[0], key, val)

            return ControlNetConfig(units=units)

        return None

    # Format 3: Dict (inline configuration)
    elif isinstance(value, dict):
        try:
            unit = ControlNetUnit(**value)
            return ControlNetConfig(units=[unit])
        except TypeError as e:
            raise ControlNetParseError(f"Invalid inline ControlNet config: {e}")

    return None


# Type hint for optional import
from typing import Optional
