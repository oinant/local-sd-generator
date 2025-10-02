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

    if 'variations' not in data:
        raise ValueError(f"Invalid YAML format in {filepath}: missing 'variations' key")

    variations_data = data['variations']
    if not isinstance(variations_data, list):
        raise ValueError(f"Invalid YAML format in {filepath}: 'variations' must be a list")

    variations = {}

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

    return variations
