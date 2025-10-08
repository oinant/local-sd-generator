"""
Image and JSON file I/O for generation outputs

Handles writing image data and JSON request payloads to disk.
"""

import json
import base64
from pathlib import Path
from typing import Union


class ImageWriter:
    """
    Handles image and JSON file I/O

    Responsibility: File operations only
    - Save PNG images from base64 data
    - Save JSON request payloads (dry-run mode)

    Does NOT handle:
    - Directory creation (SessionManager's job)
    - API communication
    - Progress reporting
    """

    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize image writer

        Args:
            output_dir: Directory where files will be saved
        """
        self.output_dir = Path(output_dir)

    def save_image(self, image_data_b64: str, filename: str) -> Path:
        """
        Save base64-encoded image to PNG file

        Args:
            image_data_b64: Base64-encoded image data (from API response)
            filename: Output filename (e.g., "image_001.png")

        Returns:
            Path: Full path to saved file

        Raises:
            IOError: If file cannot be written
        """
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_data_b64)

        # Write to file
        filepath = self.output_dir / filename
        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        return filepath

    def save_json_request(self, payload: dict, filename: str) -> Path:
        """
        Save JSON request payload to file (dry-run mode)

        Converts .png extension to .json automatically.

        Args:
            payload: API request payload to save
            filename: Output filename (e.g., "request_001.png" → "request_001.json")

        Returns:
            Path: Full path to saved file

        Raises:
            IOError: If file cannot be written
        """
        # Replace .png with .json
        json_filename = filename.replace('.png', '.json')

        filepath = self.output_dir / json_filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        return filepath

    def save_images_from_response(self, api_response: dict, filename: str) -> list[Path]:
        """
        Save all images from API response

        Args:
            api_response: Full API response dict with 'images' key
            filename: Base filename (e.g., "image.png")
                     If multiple images, will append _001, _002, etc.

        Returns:
            list[Path]: Paths to all saved files

        Raises:
            KeyError: If api_response doesn't contain 'images'
            IOError: If files cannot be written
        """
        images = api_response['images']
        saved_paths = []

        if len(images) == 1:
            # Single image - use filename as-is
            path = self.save_image(images[0], filename)
            saved_paths.append(path)
        else:
            # Multiple images - add counter
            base_name = filename.rsplit('.', 1)[0]
            extension = filename.rsplit('.', 1)[1] if '.' in filename else 'png'

            for i, img_data in enumerate(images, 1):
                numbered_filename = f"{base_name}_{i:03d}.{extension}"
                path = self.save_image(img_data, numbered_filename)
                saved_paths.append(path)

        return saved_paths

    def file_exists(self, filename: str) -> bool:
        """
        Check if file exists in output directory

        Args:
            filename: Filename to check

        Returns:
            bool: True if file exists
        """
        return (self.output_dir / filename).exists()

    def get_file_path(self, filename: str) -> Path:
        """
        Get full path for a filename in output directory

        Args:
            filename: Filename

        Returns:
            Path: Full path (may or may not exist)
        """
        return self.output_dir / filename
