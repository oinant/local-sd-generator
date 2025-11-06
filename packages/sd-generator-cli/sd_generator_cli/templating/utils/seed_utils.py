"""
Utilities for parsing seed specifications.

Supports 3 formats:
- Explicit list: "1000,1005,1008" → [1000, 1005, 1008]
- Range: "1000-1019" → [1000, 1001, ..., 1019]
- Count + start: "20#1000" → [1000, 1001, ..., 1019] (20 seeds starting at 1000)
"""

from typing import List


def parse_seeds(seed_spec: str) -> List[int]:
    """
    Parse a seed specification string into a list of seeds.

    Args:
        seed_spec: Seed specification in one of these formats:
            - "1000,1005,1008" (explicit list)
            - "1000-1019" (range)
            - "20#1000" (count#start)

    Returns:
        List of seed integers

    Raises:
        ValueError: If seed_spec format is invalid

    Examples:
        >>> parse_seeds("1000,1005,1008")
        [1000, 1005, 1008]

        >>> parse_seeds("1000-1004")
        [1000, 1001, 1002, 1003, 1004]

        >>> parse_seeds("5#1000")
        [1000, 1001, 1002, 1003, 1004]
    """
    seed_spec = seed_spec.strip()

    # Format 1: Count#Start (e.g., "20#1000")
    if '#' in seed_spec:
        try:
            count_str, start_str = seed_spec.split('#', 1)
            count = int(count_str.strip())
            start = int(start_str.strip())

            if count <= 0:
                raise ValueError(f"Seed count must be positive, got: {count}")

            return list(range(start, start + count))
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(
                    f"Invalid count#start format: '{seed_spec}'. "
                    f"Expected format: <count>#<start> (e.g., '20#1000')"
                ) from e
            raise

    # Format 2: Explicit list (e.g., "1000,1005,1008") - Check BEFORE range
    if ',' in seed_spec:
        try:
            seeds = [int(s.strip()) for s in seed_spec.split(',') if s.strip()]
            return seeds
        except ValueError as e:
            raise ValueError(
                f"Invalid seed list format: '{seed_spec}'. "
                f"Expected comma-separated integers (e.g., '1000,1005,1008')"
            ) from e

    # Format 3: Range (e.g., "1000-1019")
    if '-' in seed_spec:
        try:
            # Handle negative numbers in range (e.g., "-5--1" or "1000--1")
            parts = seed_spec.split('-')

            # Simple case: "1000-1019" (2 parts)
            if len(parts) == 2:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            # Negative start: "-5-10" → ['', '5', '10']
            elif len(parts) == 3 and parts[0] == '':
                start = -int(parts[1].strip())
                end = int(parts[2].strip())
            # Negative end: "1000--1" → ['1000', '', '1']
            elif len(parts) == 3 and parts[1] == '':
                start = int(parts[0].strip())
                end = -int(parts[2].strip())
            # Both negative: "-10--1" → ['', '10', '', '1']
            elif len(parts) == 4 and parts[0] == '' and parts[2] == '':
                start = -int(parts[1].strip())
                end = -int(parts[3].strip())
            else:
                raise ValueError(f"Ambiguous range format: '{seed_spec}'")

            if start > end:
                raise ValueError(f"Invalid range: start ({start}) > end ({end})")

            return list(range(start, end + 1))
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(
                    f"Invalid range format: '{seed_spec}'. "
                    f"Expected format: <start>-<end> (e.g., '1000-1019')"
                ) from e
            raise

    # Single seed
    try:
        return [int(seed_spec)]
    except ValueError as e:
        raise ValueError(
            f"Invalid seed specification: '{seed_spec}'. "
            f"Expected one of:\n"
            f"  - Explicit list: '1000,1005,1008'\n"
            f"  - Range: '1000-1019'\n"
            f"  - Count#start: '20#1000'\n"
            f"  - Single seed: '1000'"
        ) from e
