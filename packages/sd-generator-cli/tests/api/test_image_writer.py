"""
Unit tests for ImageWriter
"""

import pytest
import tempfile
import shutil
import base64
import json
from pathlib import Path

from sd_generator_cli.api import ImageWriter


class TestImageWriter:
    """Test image and JSON file I/O"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_image_b64(self):
        """Create sample base64 image data"""
        # Simple 1x1 PNG in base64
        png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        return base64.b64encode(png_bytes).decode('utf-8')

    def test_init(self, temp_output_dir):
        """Test writer initialization"""
        writer = ImageWriter(temp_output_dir)

        assert writer.output_dir == Path(temp_output_dir)

    def test_init_with_path_object(self, temp_output_dir):
        """Test initialization with Path object"""
        writer = ImageWriter(Path(temp_output_dir))

        assert writer.output_dir == Path(temp_output_dir)

    def test_save_image(self, temp_output_dir, sample_image_b64):
        """Test saving base64 image to file"""
        writer = ImageWriter(temp_output_dir)

        filepath = writer.save_image(sample_image_b64, "test.png")

        assert filepath.exists()
        assert filepath.name == "test.png"
        assert filepath.parent == Path(temp_output_dir)

        # Check file was written
        assert filepath.stat().st_size > 0

    def test_save_json_request(self, temp_output_dir):
        """Test saving JSON request payload"""
        writer = ImageWriter(temp_output_dir)

        payload = {
            "prompt": "a cat",
            "steps": 30,
            "seed": 42
        }

        filepath = writer.save_json_request(payload, "request_001.png")

        assert filepath.exists()
        assert filepath.name == "request_001.json"  # .png → .json

        # Verify JSON content
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        assert loaded['prompt'] == "a cat"
        assert loaded['steps'] == 30
        assert loaded['seed'] == 42

    def test_save_json_request_already_json_extension(self, temp_output_dir):
        """Test saving JSON with .json extension"""
        writer = ImageWriter(temp_output_dir)

        payload = {"test": "data"}
        filepath = writer.save_json_request(payload, "request.json")

        # Should still work, might result in .json.json but that's ok
        assert filepath.exists()

    def test_save_images_from_response_single(self, temp_output_dir, sample_image_b64):
        """Test saving single image from API response"""
        writer = ImageWriter(temp_output_dir)

        api_response = {
            'images': [sample_image_b64],
            'parameters': {},
            'info': '{}'
        }

        paths = writer.save_images_from_response(api_response, "output.png")

        assert len(paths) == 1
        assert paths[0].name == "output.png"
        assert paths[0].exists()

    def test_save_images_from_response_multiple(self, temp_output_dir, sample_image_b64):
        """Test saving multiple images from API response"""
        writer = ImageWriter(temp_output_dir)

        api_response = {
            'images': [sample_image_b64, sample_image_b64, sample_image_b64],
            'parameters': {},
            'info': '{}'
        }

        paths = writer.save_images_from_response(api_response, "batch.png")

        assert len(paths) == 3
        assert paths[0].name == "batch_001.png"
        assert paths[1].name == "batch_002.png"
        assert paths[2].name == "batch_003.png"

        for path in paths:
            assert path.exists()

    def test_save_images_from_response_no_images_key(self, temp_output_dir):
        """Test error when response missing 'images' key"""
        writer = ImageWriter(temp_output_dir)

        api_response = {'parameters': {}}

        with pytest.raises(KeyError):
            writer.save_images_from_response(api_response, "output.png")

    def test_file_exists(self, temp_output_dir):
        """Test file existence check"""
        writer = ImageWriter(temp_output_dir)

        # File doesn't exist yet
        assert writer.file_exists("test.png") is False

        # Create file
        test_file = Path(temp_output_dir) / "test.png"
        test_file.write_text("test")

        # Now it exists
        assert writer.file_exists("test.png") is True

    def test_get_file_path(self, temp_output_dir):
        """Test getting full file path"""
        writer = ImageWriter(temp_output_dir)

        filepath = writer.get_file_path("image.png")

        assert filepath == Path(temp_output_dir) / "image.png"
        assert isinstance(filepath, Path)

    def test_save_image_invalid_base64(self, temp_output_dir):
        """Test saving with invalid base64 data"""
        writer = ImageWriter(temp_output_dir)

        with pytest.raises(Exception):
            writer.save_image("invalid_base64!!!", "bad.png")

    def test_save_json_unicode(self, temp_output_dir):
        """Test saving JSON with unicode characters"""
        writer = ImageWriter(temp_output_dir)

        payload = {
            "prompt": "かわいい猫, cute cat, très mignon",
            "chinese": "可爱的猫"
        }

        filepath = writer.save_json_request(payload, "unicode.png")

        with open(filepath, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        assert loaded['prompt'] == "かわいい猫, cute cat, très mignon"
        assert loaded['chinese'] == "可爱的猫"
