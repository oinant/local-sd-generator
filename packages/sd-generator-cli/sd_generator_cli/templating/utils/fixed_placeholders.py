"""
Utility functions for handling fixed placeholder values.

Allows locking specific placeholder values during generation while
others vary normally.
"""


def parse_fixed_values(fixed_arg: str | None) -> dict[str, str]:
    """
    Parse --use-fixed argument into dict of placeholder:key pairs.

    Args:
        fixed_arg: String in format "placeholder:key|placeholder2:key2"
                  Example: "rendering:semi-realistic|mood:sad"

    Returns:
        Dict mapping placeholder names to their fixed keys.
        Empty dict if fixed_arg is None or empty.

    Raises:
        ValueError: If format is invalid (missing ':' separator)

    Examples:
        >>> parse_fixed_values("mood:sad")
        {'mood': 'sad'}

        >>> parse_fixed_values("rendering:semi-realistic|mood:sad")
        {'rendering': 'semi-realistic', 'mood': 'sad'}

        >>> parse_fixed_values(None)
        {}
    """
    if not fixed_arg:
        return {}

    pairs = fixed_arg.split('|')
    result = {}

    for pair in pairs:
        pair = pair.strip()
        if not pair:
            continue

        if ':' not in pair:
            raise ValueError(
                f"Invalid --use-fixed format: '{pair}'. "
                f"Expected 'placeholder:key', got '{pair}'"
            )

        placeholder, key = pair.split(':', 1)
        result[placeholder.strip()] = key.strip()

    return result
