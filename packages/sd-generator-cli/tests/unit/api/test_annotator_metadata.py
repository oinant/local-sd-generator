"""
Test that image annotations preserve PNG metadata (parameters chunk).

Critical for ensuring annotated images keep SD generation parameters.
"""

import tempfile
from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin

from sd_generator_cli.api.annotator import ImageAnnotator


@pytest.fixture
def temp_dir():
    """Create temporary directory for test images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_png_with_metadata(temp_dir):
    """Create a sample PNG with SD-style metadata."""
    # Create a simple image
    img = Image.new('RGB', (512, 512), color='blue')

    # Add SD-style metadata (parameters chunk)
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("parameters", """masterpiece, best quality, beautiful girl, long blonde hair
Negative prompt: low quality, blurry, ugly
Steps: 20, Sampler: DPM++ 2M, Schedule type: Karras, CFG scale: 7.0, Seed: 123456789, Size: 512x512, Model: animagine-xl-3.1, Model hash: 1234abcd, Version: v1.9.4""")

    # Save with metadata
    image_path = temp_dir / "test_image.png"
    img.save(image_path, pnginfo=pnginfo)

    return image_path


def test_annotate_preserves_metadata(sample_png_with_metadata):
    """Test that annotation preserves PNG metadata."""
    image_path = sample_png_with_metadata

    # Verify image has metadata before annotation
    with Image.open(image_path) as img:
        original_params = img.info.get('parameters', '')

    assert original_params, "Test image should have metadata"
    assert 'Steps: 20' in original_params
    assert 'Sampler: DPM++ 2M' in original_params
    assert 'Seed: 123456789' in original_params

    # Annotate the image
    annotator = ImageAnnotator(
        position="bottom-left",
        font_size=16,
        text_color=(255, 255, 255),
        background_color=(0, 0, 0, 180),
        padding=10,
        margin=20
    )

    variations = {
        "Hair": "long_blonde",
        "Outfit": "casual_dress",
        "Pose": "standing"
    }

    # Annotate (overwrites original)
    annotator.annotate_image(image_path, variations)

    # Verify metadata is preserved after annotation
    with Image.open(image_path) as img:
        annotated_params = img.info.get('parameters', '')

    assert annotated_params, "Annotated image should still have metadata"
    assert annotated_params == original_params, "Metadata should be identical"
    assert 'Steps: 20' in annotated_params
    assert 'Sampler: DPM++ 2M' in annotated_params
    assert 'Seed: 123456789' in annotated_params


def test_annotate_preserves_all_metadata_chunks(temp_dir):
    """Test that all PNG text chunks are preserved (not just parameters)."""
    # Create image with multiple metadata chunks
    img = Image.new('RGB', (512, 512), color='red')

    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("parameters", "test parameters")
    pnginfo.add_text("workflow", "test workflow")
    pnginfo.add_text("custom_field", "custom value")

    image_path = temp_dir / "multi_metadata.png"
    img.save(image_path, pnginfo=pnginfo)

    # Annotate
    annotator = ImageAnnotator()
    annotator.annotate_image(image_path, {"Test": "value"})

    # Verify all chunks preserved
    with Image.open(image_path) as img:
        assert img.info.get('parameters') == "test parameters"
        assert img.info.get('workflow') == "test workflow"
        assert img.info.get('custom_field') == "custom value"


def test_annotate_jpeg_no_metadata(temp_dir):
    """Test that JPEG annotation works (metadata not supported for JPEG)."""
    # Create JPEG
    img = Image.new('RGB', (512, 512), color='green')
    jpeg_path = temp_dir / "test_image.jpg"
    img.save(jpeg_path, 'JPEG')

    # Annotate (should work without errors even though JPEG can't store PNG metadata)
    annotator = ImageAnnotator()
    annotator.annotate_image(jpeg_path, {"Hair": "short_brown"})

    # Verify image was annotated (file exists and is larger due to text)
    assert jpeg_path.exists()


def test_annotate_empty_variations_preserves_metadata(sample_png_with_metadata):
    """Test that even with no variations to display, metadata is preserved."""
    image_path = sample_png_with_metadata

    with Image.open(image_path) as img:
        original_params = img.info.get('parameters', '')

    # Annotate with empty variations (should return early without modifying)
    annotator = ImageAnnotator()
    annotator.annotate_image(image_path, {})  # Empty dict

    # Metadata should still exist (file wasn't modified)
    with Image.open(image_path) as img:
        assert img.info.get('parameters') == original_params


def test_annotate_with_output_path_preserves_metadata(sample_png_with_metadata, temp_dir):
    """Test that saving to a different path preserves metadata."""
    original_path = sample_png_with_metadata
    output_path = temp_dir / "annotated_copy.png"

    with Image.open(original_path) as img:
        original_params = img.info.get('parameters', '')

    # Annotate to a different file
    annotator = ImageAnnotator()
    annotator.annotate_image(
        original_path,
        {"Hair": "red_ponytail"},
        output_path=output_path
    )

    # Both files should have metadata
    with Image.open(original_path) as img:
        assert img.info.get('parameters') == original_params

    with Image.open(output_path) as img:
        assert img.info.get('parameters') == original_params
