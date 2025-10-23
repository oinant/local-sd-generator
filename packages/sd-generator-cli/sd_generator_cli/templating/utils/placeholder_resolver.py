"""
Utility for resolving placeholders in text with variation values.

This module provides functions to resolve {Placeholder} syntax in text
strings with actual variation values, used primarily for ADetailer prompt
overrides where placeholders should use the same values as the main prompt
without affecting combinatorial generation.
"""

import re
from typing import Dict


def resolve_text_placeholders(text: str, variations: Dict[str, str]) -> str:
    """
    Resolve placeholders in text with variation values.

    Replaces {PlaceholderName} with corresponding values from variations dict.
    Placeholders not found in variations are left unchanged.

    Args:
        text: Text containing {Placeholder} syntax
        variations: Dict mapping placeholder names to their values

    Returns:
        Text with placeholders replaced by values

    Examples:
        >>> variations = {"Expression": "smiling", "EyeColor": "blue"}
        >>> resolve_text_placeholders("face with {Expression}, {EyeColor} eyes", variations)
        'face with smiling, blue eyes'

        >>> resolve_text_placeholders("no placeholders here", {})
        'no placeholders here'

        >>> resolve_text_placeholders("{Missing} placeholder", {"Found": "value"})
        '{Missing} placeholder'
    """
    if not text:
        return text

    # Pattern: {PlaceholderName}
    # Matches curly braces with alphanumeric content (no selectors, no weight)
    pattern = r'\{([A-Za-z_][A-Za-z0-9_]*)\}'

    def replace_placeholder(match: re.Match) -> str:
        """Replace a single placeholder match."""
        placeholder_name = match.group(1)
        # Return value if found, otherwise keep original placeholder
        return variations.get(placeholder_name, match.group(0))

    return re.sub(pattern, replace_placeholder, text)


def extract_placeholders_from_text(text: str) -> list[str]:
    """
    Extract all placeholder names from text.

    Args:
        text: Text containing {Placeholder} syntax

    Returns:
        List of unique placeholder names found

    Examples:
        >>> extract_placeholders_from_text("face with {Expression}, {EyeColor} eyes")
        ['Expression', 'EyeColor']

        >>> extract_placeholders_from_text("no placeholders")
        []

        >>> extract_placeholders_from_text("{Pose}, {Pose}, {Angle}")
        ['Pose', 'Angle']
    """
    if not text:
        return []

    pattern = r'\{([A-Za-z_][A-Za-z0-9_]*)\}'
    matches = re.findall(pattern, text)

    # Return unique placeholders preserving order
    seen = set()
    result = []
    for name in matches:
        if name not in seen:
            seen.add(name)
            result.append(name)

    return result
