"""
Module for generating intelligent file and folder names.

This module provides utilities for naming session folders and image files
based on configuration and variation data.

Part of SF-4: Enhanced File Naming System
"""

import re
from datetime import datetime
from typing import Dict, List, Optional


def sanitize_filename_component(value: str, max_length: int = 50) -> str:
    """
    Sanitize a value for use in filenames using camelCase conversion.

    - Converts to camelCase (first word lowercase, rest capitalized)
    - Removes accents and special characters
    - Limits length to max_length characters

    Args:
        value: The value to sanitize
        max_length: Maximum length for the component (default: 50)

    Returns:
        Sanitized camelCase string safe for use in filenames

    Examples:
        >>> sanitize_filename_component("Happy Smile")
        "happySmile"
        >>> sanitize_filename_component("café/espresso")
        "cafeEspresso"
        >>> sanitize_filename_component("test:file*name?")
        "testFileName"
        >>> sanitize_filename_component("front view")
        "frontView"
    """
    if not value or not value.strip():
        return "empty"

    # Remove accents and normalize unicode first
    sanitized = value.encode('ascii', 'ignore').decode('ascii')

    # Replace special characters and punctuation with spaces for word splitting
    sanitized = re.sub(r'[^a-zA-Z0-9\s]', ' ', sanitized)

    # Split into words and filter empty strings
    words = [w for w in sanitized.split() if w]

    if not words:
        return "unnamed"

    # Convert to camelCase: first word lowercase, rest capitalized
    camel_case = words[0].lower() + ''.join(w.capitalize() for w in words[1:])

    # Trim to max length
    if len(camel_case) > max_length:
        camel_case = camel_case[:max_length]

    return camel_case if camel_case else "unnamed"


def generate_session_folder_name(
    timestamp: datetime,
    session_name: Optional[str] = None,
    filename_keys: Optional[List[str]] = None,
    variations_sample: Optional[Dict[str, Dict[str, str]]] = None
) -> str:
    """
    Generate a session folder name based on configuration.

    Format:
    - If session_name provided: {timestamp}_{session_name}
    - Else if filename_keys provided: {timestamp}_{key1}_{key2}...
    - Else: {timestamp}_session

    Timestamp format: YYYYMMDD_HHMMSS

    Args:
        timestamp: DateTime object for the session start
        session_name: Optional custom session name
        filename_keys: Optional list of variation keys to use in folder name
        variations_sample: Optional dict of variations (for future use)

    Returns:
        Session folder name string

    Examples:
        >>> dt = datetime(2025, 10, 1, 14, 30, 52)
        >>> generate_session_folder_name(dt, "anime_test_v2")
        "20251001_143052_anime_test_v2"
        >>> generate_session_folder_name(dt, filename_keys=["Expression", "Angle"])
        "20251001_143052_Expression_Angle"
        >>> generate_session_folder_name(dt)
        "20251001_143052_session"
    """
    # Format timestamp as YYYYMMDD_HHMMSS
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

    if session_name:
        # Use provided session name
        sanitized_name = sanitize_filename_component(session_name)
        return f"{timestamp_str}_{sanitized_name}"

    elif filename_keys:
        # Use filename_keys to build name
        sanitized_keys = [sanitize_filename_component(key) for key in filename_keys]
        keys_str = "_".join(sanitized_keys)
        return f"{timestamp_str}_{keys_str}"

    else:
        # Default fallback
        return f"{timestamp_str}_session"


def generate_image_filename(
    index: int,
    variation_dict: Optional[Dict[str, str]] = None,
    filename_keys: Optional[List[str]] = None
) -> str:
    """
    Generate an image filename based on index and variations.

    Format:
    - If filename_keys empty: {index:03d}.png
    - Else: {index:03d}_{key1}-{value1}_{key2}-{value2}.png

    Args:
        index: Image index (1-based)
        variation_dict: Dict of {placeholder: value} for this image
        filename_keys: List of keys to include in filename (in order)

    Returns:
        Image filename string

    Examples:
        >>> generate_image_filename(1)
        "001.png"
        >>> generate_image_filename(42, {"Expression": "smiling", "Angle": "front view"}, ["Expression", "Angle"])
        "042_Expression-smiling_Angle-front_view.png"
        >>> generate_image_filename(5, {"Expression": "angry"}, ["Expression"])
        "005_Expression-angry.png"
    """
    # Base index part (always 3 digits)
    filename = f"{index:03d}"

    # Add variation components if requested
    if filename_keys and variation_dict:
        components = []
        for key in filename_keys:
            if key in variation_dict:
                value = variation_dict[key]
                sanitized_value = sanitize_filename_component(value)
                components.append(f"{key}-{sanitized_value}")

        if components:
            filename += "_" + "_".join(components)

    return f"{filename}.png"


def format_timestamp_iso(dt: datetime) -> str:
    """
    Format a datetime as ISO 8601 string.

    Args:
        dt: DateTime object

    Returns:
        ISO 8601 formatted string

    Examples:
        >>> dt = datetime(2025, 10, 1, 14, 30, 52)
        >>> format_timestamp_iso(dt)
        "2025-10-01T14:30:52"
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


if __name__ == "__main__":
    # Quick manual tests
    print("🧪 Testing output_namer module\n")

    # Test sanitization
    print("Sanitization tests:")
    print(f"  'Happy Smile' → '{sanitize_filename_component('Happy Smile')}'")
    print(f"  'café/espresso' → '{sanitize_filename_component('café/espresso')}'")
    print(f"  'test:file*name?' → '{sanitize_filename_component('test:file*name?')}'")
    print()

    # Test session folder naming
    dt = datetime(2025, 10, 1, 14, 30, 52)
    print("Session folder tests:")
    print(f"  With session_name: '{generate_session_folder_name(dt, 'anime_test_v2')}'")
    print(f"  With filename_keys: '{generate_session_folder_name(dt, filename_keys=['Expression', 'Angle'])}'")
    print(f"  Default: '{generate_session_folder_name(dt)}'")
    print()

    # Test image filename
    print("Image filename tests:")
    print(f"  Simple: '{generate_image_filename(1)}'")
    print(f"  With keys: '{generate_image_filename(42, {'Expression': 'smiling', 'Angle': 'front view'}, ['Expression', 'Angle'])}'")
    print()

    print("✅ All tests completed!")
