"""
Hash utilities for Template System V2.0.

This module provides hashing functions for generating unique keys
for inline variation strings.
"""

import hashlib


def md5_short(value: str, length: int = 8) -> str:
    """
    Generate a short MD5 hash of a string.

    This is used to create unique keys for inline variation strings
    that don't have explicit keys in the YAML.

    Args:
        value: String to hash
        length: Length of the hash to return (default: 8)

    Returns:
        Short MD5 hash (lowercase hex string)

    Example:
        >>> md5_short("red dress")
        '7d8e3a2f'
    """
    hash_full = hashlib.md5(value.encode('utf-8')).hexdigest()
    return hash_full[:length]
