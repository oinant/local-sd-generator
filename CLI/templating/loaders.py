"""
Loaders for variation files (YAML format only).
"""

from pathlib import Path
from typing import Dict, Union
import yaml

from .types import Variation


def load_variations(filepath: Union[str, Path]) -> Dict[str, Variation]:
    """
    Load variations from a YAML file.

    Expected format:
        version: "1.0"
        variations:
          - key: happy
            value: "smiling, cheerful"
            weight: 1.0
          - key: sad
            value: "crying, tears"

    Or simple format:
        variations:
          - standing
          - sitting
          - lying down

    Args:
        filepath: Path to the YAML file

    Returns:
        Dictionary mapping keys to Variation objects

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If YAML format is invalid
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Variation file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML format in {filepath}: expected dict at root")

    # Check if this is a multi-field file (has 'type' and 'sources')
    file_type = data.get('type', 'variations')

    if file_type == 'multi-field':
        # This is a multi-field file - delegate to multi_field module
        from .multi_field import load_multi_field_variations
        return load_multi_field_variations(filepath)

    if file_type == 'chunk':
        # This is a chunk file - will be handled by chunk module
        # For now, treat it as having no direct variations
        return {}

    if 'variations' not in data:
        raise ValueError(f"Invalid YAML format in {filepath}: missing 'variations' key")

    variations_data = data['variations']

    # Support both list format (Phase 1) and dict format (Phase 2 converted files)
    variations = {}

    if isinstance(variations_data, list):
        # Phase 1 format: list of items
        for idx, item in enumerate(variations_data):
            if isinstance(item, str):
                # Simple format: just strings
                key = f"_{idx}"  # Auto-generated key
                value = item
                weight = 1.0
            elif isinstance(item, dict):
                # Full format with key/value/weight
                if 'value' in item:
                    key = item.get('key', f"_{idx}")
                    value = item['value']
                    weight = item.get('weight', 1.0)
                else:
                    raise ValueError(f"Invalid variation format at index {idx}: {item}")
            else:
                raise ValueError(f"Invalid variation format at index {idx}: expected str or dict, got {type(item)}")

            variations[key] = Variation(key=key, value=value, weight=weight)

    elif isinstance(variations_data, dict):
        # Phase 2 format: dict with key->value mappings
        for key, value in variations_data.items():
            if isinstance(value, str):
                variations[key] = Variation(key=key, value=value, weight=1.0)
            elif isinstance(value, dict):
                # Support weight if specified
                variations[key] = Variation(
                    key=key,
                    value=value.get('value', str(value)),
                    weight=value.get('weight', 1.0)
                )
            else:
                variations[key] = Variation(key=key, value=str(value), weight=1.0)

    else:
        raise ValueError(f"Invalid YAML format in {filepath}: 'variations' must be a list or dict")

    return variations
