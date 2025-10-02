"""
Parser and resolver for variation selectors.

Syntax:
    {SOURCE[selector1,selector2,...]}

Selector types:
    - Keys: [happy,sad]
    - Indices: [1,5,8]
    - Range: [range:1-10]
    - Random: [random:5]
    - All: [all] or no selector
"""

import random
import re
from typing import Dict, List, Optional
from .types import Variation, Selector


def parse_selector(selector_str: str) -> List[Selector]:
    """
    Parse a selector string like "[happy,sad,random:3]" into Selector objects.

    Args:
        selector_str: The selector string (with or without brackets)

    Returns:
        List of Selector objects

    Raises:
        ValueError: If syntax is invalid
    """
    # Remove brackets if present
    selector_str = selector_str.strip()
    if selector_str.startswith('[') and selector_str.endswith(']'):
        selector_str = selector_str[1:-1]

    # Empty or "all" means select all
    if not selector_str or selector_str == 'all':
        return [Selector(type="all")]

    # Split by comma
    parts = [part.strip() for part in selector_str.split(',')]
    selectors = []

    # Track what we're collecting
    keys = []
    indices = []

    for part in parts:
        if not part:
            continue

        # Random selector: random:N
        if part.startswith('random:'):
            try:
                count = int(part.split(':', 1)[1])
                selectors.append(Selector(type="random", count=count))
            except (ValueError, IndexError):
                raise ValueError(f"Invalid random selector: '{part}'. Expected 'random:N'")

        # Range selector: range:N-M
        elif part.startswith('range:'):
            try:
                range_part = part.split(':', 1)[1]
                start, end = range_part.split('-')
                start, end = int(start), int(end)
                if start > end:
                    raise ValueError(f"Invalid range {start}-{end}: start must be <= end")
                selectors.append(Selector(type="range", start=start, end=end))
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid range selector: '{part}'. Expected 'range:N-M'") from e

        # Index selector: just a number
        elif part.isdigit():
            indices.append(int(part))

        # Key selector: anything else
        else:
            keys.append(part)

    # Add key and index selectors if we collected any
    if keys:
        selectors.insert(0, Selector(type="keys", keys=keys))
    if indices:
        selectors.insert(0, Selector(type="indices", indices=indices))

    return selectors if selectors else [Selector(type="all")]


def resolve_selectors(
    variations: Dict[str, Variation],
    selectors: List[Selector],
    index_base: int = 0,
    strict_mode: bool = True,
    allow_duplicates: bool = False,
    random_seed: Optional[int] = None
) -> List[Variation]:
    """
    Resolve selectors against a set of variations.

    Args:
        variations: Dict of available variations
        selectors: List of Selector objects to apply
        index_base: 0 for 0-indexed, 1 for 1-indexed
        strict_mode: Raise errors on invalid keys/indices
        allow_duplicates: Allow duplicate variations in result
        random_seed: Seed for random selections (None = use system random)

    Returns:
        List of selected Variation objects

    Raises:
        KeyError: If strict_mode and key not found
        IndexError: If strict_mode and index out of range
    """
    result = []
    all_variations_list = list(variations.values())

    # Set random seed if provided
    if random_seed is not None:
        random.seed(random_seed)

    for selector in selectors:
        if selector.type == "all":
            result.extend(all_variations_list)

        elif selector.type == "keys":
            for key in selector.keys:
                if key in variations:
                    result.append(variations[key])
                elif strict_mode:
                    raise KeyError(f"Key '{key}' not found in variations")

        elif selector.type == "indices":
            for idx in selector.indices:
                # Adjust for index_base
                adjusted_idx = idx - index_base
                if 0 <= adjusted_idx < len(all_variations_list):
                    result.append(all_variations_list[adjusted_idx])
                elif strict_mode:
                    raise IndexError(
                        f"Index {idx} out of range [0-{len(all_variations_list)-1}] "
                        f"(index_base={index_base})"
                    )

        elif selector.type == "range":
            start = selector.start - index_base
            end = selector.end - index_base
            if start < 0 or end >= len(all_variations_list):
                if strict_mode:
                    raise IndexError(
                        f"Range {selector.start}-{selector.end} out of bounds "
                        f"[0-{len(all_variations_list)-1}] (index_base={index_base})"
                    )
                # Clamp to valid range
                start = max(0, start)
                end = min(len(all_variations_list) - 1, end)
            result.extend(all_variations_list[start:end+1])

        elif selector.type == "random":
            # Select from variations not already in result (unless allow_duplicates)
            if allow_duplicates:
                available = all_variations_list
            else:
                available = [v for v in all_variations_list if v not in result]

            count = min(selector.count, len(available))
            if count < selector.count and strict_mode:
                # Warning, not error
                pass
            result.extend(random.sample(available, count))

    # Deduplicate if needed
    if not allow_duplicates:
        # Preserve order while removing duplicates
        seen = set()
        deduplicated = []
        for v in result:
            if v.key not in seen:
                seen.add(v.key)
                deduplicated.append(v)
        result = deduplicated

    return result


def extract_placeholders(prompt_template: str) -> Dict[str, Optional[str]]:
    """
    Extract placeholders from a prompt template.

    Args:
        prompt_template: Template string like "beautiful {EXPR[happy,sad]}, {POSE}"

    Returns:
        Dict mapping placeholder names to their selector strings (or None if no selector)
        Example: {"EXPR": "[happy,sad]", "POSE": None}
    """
    # Pattern: {PLACEHOLDER} or {PLACEHOLDER[selector]}
    pattern = r'\{([A-Z_]+)(?:\[([^\]]+)\])?\}'
    matches = re.findall(pattern, prompt_template)

    placeholders = {}
    for name, selector in matches:
        placeholders[name] = selector if selector else None

    return placeholders


def parse_chunk_with_syntax(placeholder_content: str) -> tuple:
    """
    Parse chunk placeholder with "with" syntax.

    Syntax: CHUNK with field1=SOURCE1[selector1], field2=SOURCE2[selector2]

    Args:
        placeholder_content: Content inside {} like "CHARACTER with ethnicity=ETHNICITIES[african,asian]"

    Returns:
        Tuple of (chunk_name, overrides_dict) where overrides_dict is:
        {"ethnicity": ("ETHNICITIES", "[african,asian]")}

    Returns:
        (None, None) if not a "with" syntax

    Example:
        >>> parse_chunk_with_syntax("CHARACTER with ethnicity=ETHNICITIES[african,asian]")
        ("CHARACTER", {"ethnicity": ("ETHNICITIES", "[african,asian]")})
    """
    # Pattern: CHUNK_NAME with field=SOURCE[selector], field2=SOURCE2[selector2]
    match = re.match(r'([A-Z_]+)\s+with\s+(.+)', placeholder_content)
    if not match:
        return None, None

    chunk_name = match.group(1)
    overrides_str = match.group(2)

    # Parse overrides: field=SOURCE[selector], field2=SOURCE2
    overrides = {}
    # Split by comma, but be careful of commas inside []
    override_pattern = r'([a-zA-Z_]+)=([A-Z_]+)(?:\[([^\]]+)\])?'

    for match in re.finditer(override_pattern, overrides_str):
        field_name = match.group(1)
        source_name = match.group(2)
        selector = match.group(3)  # Can be None

        selector_str = f"[{selector}]" if selector else None
        overrides[field_name] = (source_name, selector_str)

    return chunk_name, overrides
