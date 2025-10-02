"""
Multi-field expansion system for the templating engine.

A multi-field variation can expand multiple character fields simultaneously.
For example, an ethnicity variation can set skin, hair, and eyes together.
"""

from pathlib import Path
from typing import Dict, List
import yaml

from .types import MultiFieldVariation, Variation


def is_multi_field_variation(variation_data: dict) -> bool:
    """
    Check if a variation file contains multi-field type variations.

    Args:
        variation_data: Parsed YAML data from variation file

    Returns:
        True if the file has type: multi_field
    """
    return variation_data.get('type') == 'multi_field'


def load_multi_field_variations(filepath: Path, base_path: Path = None) -> Dict[str, MultiFieldVariation]:
    """
    Load multi-field variations from a YAML file.

    Args:
        filepath: Path to the multi-field variation file
        base_path: Base directory for resolving relative paths

    Returns:
        Dictionary mapping variation keys to MultiFieldVariation objects

    Example:
        variations/ethnic_features.yaml:
        ```yaml
        type: multi_field
        variations:
          - key: african
            fields:
              appearance.skin: "dark skin"
              appearance.hair: "coily black hair"
        ```

        Result: {"african": MultiFieldVariation(key="african", fields={...})}
    """
    if base_path:
        filepath = base_path / filepath

    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not is_multi_field_variation(data):
        raise ValueError(f"File {filepath} is not a multi_field variation file")

    variations = {}
    for var_entry in data.get('variations', []):
        key = var_entry.get('key')
        if not key:
            raise ValueError(f"Multi-field variation missing 'key' in {filepath}")

        # Extract fields
        fields = var_entry.get('fields', {})

        # Create MultiFieldVariation
        # For now, value is empty string as it's not used for multi-field
        variations[key] = MultiFieldVariation(
            key=key,
            value="",  # Multi-field doesn't have a single value
            weight=var_entry.get('weight', 1.0),
            fields=fields
        )

    return variations


def expand_multi_field(
    variation: MultiFieldVariation,
    chunk_fields: Dict[str, Dict[str, str]]
) -> Dict[str, Dict[str, str]]:
    """
    Expand a multi-field variation into chunk fields.

    Args:
        variation: MultiFieldVariation to expand
        chunk_fields: Existing chunk fields (nested dict)

    Returns:
        Updated chunk fields with multi-field values applied

    Example:
        variation.fields = {"appearance.skin": "dark skin", "appearance.hair": "coily hair"}
        chunk_fields = {"appearance": {"age": "23"}}

        Result: {"appearance": {"age": "23", "skin": "dark skin", "hair": "coily hair"}}
    """
    import copy
    result = copy.deepcopy(chunk_fields)

    # Apply each field from the multi-field variation
    for field_path, value in variation.fields.items():
        # Split path like "appearance.skin" into ["appearance", "skin"]
        parts = field_path.split('.')

        if len(parts) == 1:
            # Top-level field (rare but supported)
            if parts[0] not in result:
                result[parts[0]] = {}
            # For top-level, we might need different handling
            # For now, treat as error
            raise ValueError(f"Multi-field path must be nested (e.g., 'appearance.skin'), got '{field_path}'")
        elif len(parts) == 2:
            # Standard nested field like "appearance.skin"
            category, field_name = parts
            if category not in result:
                result[category] = {}
            result[category][field_name] = value
        else:
            # Deeper nesting not yet supported
            raise ValueError(f"Multi-field paths deeper than 2 levels not yet supported: '{field_path}'")

    return result


def merge_multi_field_into_chunk(
    selected_variations: List[MultiFieldVariation],
    chunk_fields: Dict[str, Dict[str, str]],
    inline_overrides: Dict[str, str] = None
) -> Dict[str, Dict[str, str]]:
    """
    Merge multiple multi-field variations into chunk fields with priority handling.

    Priority (highest to lowest):
    1. Inline overrides
    2. Multi-field expansion values
    3. Existing chunk field values

    Args:
        selected_variations: List of MultiFieldVariation objects to apply
        chunk_fields: Base chunk fields
        inline_overrides: Field overrides specified inline (e.g., {"appearance.skin": "red skin"})

    Returns:
        Merged chunk fields
    """
    import copy
    result = copy.deepcopy(chunk_fields)

    # Apply multi-field variations
    for variation in selected_variations:
        result = expand_multi_field(variation, result)

    # Apply inline overrides (highest priority)
    if inline_overrides:
        for field_path, value in inline_overrides.items():
            parts = field_path.split('.')
            if len(parts) == 2:
                category, field_name = parts
                if category not in result:
                    result[category] = {}
                result[category][field_name] = value
            else:
                raise ValueError(f"Inline override path must be 2-level nested: '{field_path}'")

    return result
