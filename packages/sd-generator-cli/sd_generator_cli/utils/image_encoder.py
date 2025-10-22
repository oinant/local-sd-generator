"""Image encoding utilities for API communication.

This module handles conversion of image files to base64 format
required by Stable Diffusion WebUI API (ControlNet, etc.).
"""

import base64
from pathlib import Path
from typing import Union


class ImageEncoder:
    """Utility class for encoding images to base64 format."""

    @staticmethod
    def encode_image_file_from_path(image_path: Union[str, Path]) -> str:
        """
        Encode an image file to base64 string for API transmission.

        Args:
            image_path: Path to image file (absolute or relative)

        Returns:
            Base64-encoded string of the image contents

        Raises:
            FileNotFoundError: If image file doesn't exist
            IOError: If image file cannot be read

        Example:
            >>> encoder = ImageEncoder()
            >>> base64_str = encoder.encode_image_file_from_path("/path/to/image.png")
            >>> base64_str.startswith("iVBORw")  # PNG signature in base64
            True
        """
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(
                f"ControlNet image file not found: {image_path}\n"
                f"  Resolved path: {path.resolve()}"
            )

        if not path.is_file():
            raise IOError(f"Path is not a file: {image_path}")

        try:
            with open(path, 'rb') as f:
                image_bytes = f.read()
        except Exception as e:
            raise IOError(f"Failed to read image file {image_path}: {e}")

        # Encode to base64
        base64_bytes = base64.b64encode(image_bytes)
        base64_string = base64_bytes.decode('utf-8')

        return base64_string

    @staticmethod
    def is_base64_encoded(value: str) -> bool:
        """
        Check if a string is already base64 encoded.

        Args:
            value: String to check

        Returns:
            True if value appears to be base64 encoded

        Example:
            >>> ImageEncoder.is_base64_encoded("iVBORw0KGgo...")
            True
            >>> ImageEncoder.is_base64_encoded("/path/to/file.png")
            False
            >>> ImageEncoder.is_base64_encoded("data:image/png;base64,iVBORw...")
            True
        """
        if not value:
            return False

        # Check for data URI format
        if value.startswith("data:"):
            return True

        # Check for common base64 image headers
        # PNG: iVBORw0KGgo
        # JPEG: /9j/
        # GIF: R0lGOD
        if value.startswith(("iVBORw", "/9j/", "R0lGOD")):
            return True

        return False
