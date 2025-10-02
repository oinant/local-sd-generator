"""
Tests for the metadata_generator module (SF-5).

Tests cover:
- Metadata dictionary generation
- JSON file save/load operations
- Structure validation
- Legacy config text generation
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys
import os

# Add CLI to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'CLI'))

from output.metadata_generator import (
    generate_metadata_dict,
    save_metadata_json,
    load_metadata_json,
    create_legacy_config_text,
    _build_variations_metadata,
    _create_example_prompt
)


class TestGenerateMetadataDict:
    """Tests for generate_metadata_dict function."""

    def test_basic_metadata_structure(self):
        """Test that basic metadata structure is correct."""
        metadata = generate_metadata_dict(
            prompt_template="test {Expression}",
            negative_prompt="bad quality",
            variations_loaded={"Expression": {"smiling": "smiling"}},
            generation_info={
                "date": "2025-10-01T14:30:52",
                "timestamp": "20251001_143052",
                "total_images": 1
            },
            parameters={"width": 512, "height": 768},
            output_info={"folder": "/tmp/test"}
        )

        # Check required top-level keys
        assert "version" in metadata
        assert "generation_info" in metadata
        assert "prompt" in metadata
        assert "variations" in metadata
        assert "generation" in metadata
        assert "parameters" in metadata
        assert "output" in metadata

    def test_version_field(self):
        """Test that version is set correctly."""
        metadata = generate_metadata_dict(
            prompt_template="test",
            negative_prompt="",
            variations_loaded={},
            generation_info={},
            parameters={},
            output_info={}
        )
        assert metadata["version"] == "1.0"

    def test_prompt_section(self):
        """Test prompt section structure."""
        metadata = generate_metadata_dict(
            prompt_template="masterpiece, {Expression}, detailed",
            negative_prompt="low quality, blurry",
            variations_loaded={"Expression": {"happy": "happy smiling"}},
            generation_info={},
            parameters={},
            output_info={}
        )

        assert metadata["prompt"]["template"] == "masterpiece, {Expression}, detailed"
        assert metadata["prompt"]["negative"] == "low quality, blurry"
        assert "example_resolved" in metadata["prompt"]
        assert "happy smiling" in metadata["prompt"]["example_resolved"]

    def test_model_info_optional(self):
        """Test that model info is included when provided."""
        metadata = generate_metadata_dict(
            prompt_template="test",
            negative_prompt="",
            variations_loaded={},
            generation_info={},
            parameters={},
            output_info={},
            model_info={"checkpoint": "test_model.safetensors"}
        )

        assert "model" in metadata
        assert metadata["model"]["checkpoint"] == "test_model.safetensors"

    def test_config_source_optional(self):
        """Test that config_source is included when provided."""
        metadata = generate_metadata_dict(
            prompt_template="test",
            negative_prompt="",
            variations_loaded={},
            generation_info={},
            parameters={},
            output_info={},
            config_source="/path/to/config.json"
        )

        assert "config_source" in metadata
        assert metadata["config_source"] == "/path/to/config.json"

    def test_generation_mode_extraction(self):
        """Test extraction of generation mode info."""
        metadata = generate_metadata_dict(
            prompt_template="test",
            negative_prompt="",
            variations_loaded={},
            generation_info={
                "generation_mode": "combinatorial",
                "seed_mode": "progressive",
                "seed": 42,
                "total_combinations": 100,
                "total_images": 50
            },
            parameters={},
            output_info={}
        )

        gen_section = metadata["generation"]
        assert gen_section["mode"] == "combinatorial"
        assert gen_section["seed_mode"] == "progressive"
        assert gen_section["seed"] == 42
        assert gen_section["total_combinations"] == 100
        assert gen_section["images_generated"] == 50


class TestBuildVariationsMetadata:
    """Tests for _build_variations_metadata function."""

    def test_basic_variations_metadata(self):
        """Test basic variations metadata structure."""
        variations = {
            "Expression": {"happy": "happy", "sad": "sad"},
            "Angle": {"front": "front view"}
        }

        metadata = _build_variations_metadata(variations, "test {Expression} {Angle}")

        assert "Expression" in metadata
        assert "Angle" in metadata
        assert metadata["Expression"]["count"] == 2
        assert metadata["Angle"]["count"] == 1
        assert metadata["Expression"]["values"] == ["happy", "sad"]
        assert metadata["Angle"]["values"] == ["front view"]

    def test_truncation_of_many_values(self):
        """Test that large variation lists are truncated."""
        variations = {
            "Test": {str(i): f"value_{i}" for i in range(20)}
        }

        metadata = _build_variations_metadata(variations, "test {Test}", max_values_in_metadata=10)

        assert metadata["Test"]["count"] == 20
        assert len(metadata["Test"]["values"]) == 11  # 10 values + "... and N more" message
        assert "... and 10 more" in metadata["Test"]["values"][-1]

    def test_empty_variations(self):
        """Test handling of empty variations dict."""
        metadata = _build_variations_metadata({}, "test prompt")
        assert metadata == {}


class TestCreateExamplePrompt:
    """Tests for _create_example_prompt function."""

    def test_simple_replacement(self):
        """Test simple placeholder replacement."""
        result = _create_example_prompt(
            "masterpiece, {Expression}, beautiful",
            {"Expression": {"smiling": "smiling happily"}}
        )
        assert result == "masterpiece, smiling happily, beautiful"

    def test_multiple_placeholders(self):
        """Test multiple placeholder replacement."""
        result = _create_example_prompt(
            "{Expression}, {Angle}, {Lighting}",
            {
                "Expression": {"happy": "happy"},
                "Angle": {"front": "front view"},
                "Lighting": {"soft": "soft light"}
            }
        )
        assert result == "happy, front view, soft light"

    def test_empty_variations(self):
        """Test with empty variations dict."""
        result = _create_example_prompt("test {Expression}", {})
        assert result == "test {Expression}"  # Placeholders remain


class TestSaveLoadMetadata:
    """Tests for save_metadata_json and load_metadata_json functions."""

    def setup_method(self):
        """Set up temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_save_and_load_roundtrip(self):
        """Test saving and loading metadata maintains data integrity."""
        original_metadata = {
            "version": "1.0",
            "test_data": "test_value",
            "nested": {"key": "value"}
        }

        # Save
        saved_path = save_metadata_json(original_metadata, self.temp_dir)
        assert saved_path.exists()

        # Load
        loaded_metadata = load_metadata_json(self.temp_dir)
        assert loaded_metadata == original_metadata

    def test_pretty_print_formatting(self):
        """Test that JSON is pretty-printed with 2-space indent."""
        metadata = {"version": "1.0", "data": {"nested": "value"}}

        save_metadata_json(metadata, self.temp_dir)

        # Read raw file to check formatting
        with open(Path(self.temp_dir) / "metadata.json", 'r') as f:
            content = f.read()

        # Check for 2-space indentation
        assert '  "version"' in content
        assert '  "data"' in content

    def test_utf8_encoding(self):
        """Test that UTF-8 characters are preserved."""
        metadata = {
            "version": "1.0",
            "unicode_test": "café, naïve, 日本語"
        }

        save_metadata_json(metadata, self.temp_dir)
        loaded = load_metadata_json(self.temp_dir)

        assert loaded["unicode_test"] == "café, naïve, 日本語"

    def test_custom_filename(self):
        """Test saving with custom filename."""
        metadata = {"version": "1.0"}

        saved_path = save_metadata_json(metadata, self.temp_dir, filename="custom.json")
        assert saved_path.name == "custom.json"

        loaded = load_metadata_json(self.temp_dir, filename="custom.json")
        assert loaded["version"] == "1.0"

    def test_save_nonexistent_folder_raises_error(self):
        """Test that saving to non-existent folder raises error."""
        with pytest.raises(OSError):
            save_metadata_json({"test": "data"}, "/nonexistent/folder/path")

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_metadata_json(self.temp_dir, filename="nonexistent.json")

    def test_load_invalid_json_raises_error(self):
        """Test that loading invalid JSON raises error."""
        # Create invalid JSON file
        invalid_json_path = Path(self.temp_dir) / "invalid.json"
        with open(invalid_json_path, 'w') as f:
            f.write("{invalid json content")

        with pytest.raises(json.JSONDecodeError):
            load_metadata_json(self.temp_dir, filename="invalid.json")


class TestCreateLegacyConfigText:
    """Tests for create_legacy_config_text function."""

    def test_legacy_text_structure(self):
        """Test that legacy config text has correct structure."""
        metadata = {
            "generation_info": {
                "session_name": "test_session",
                "date": "2025-10-01T14:30:52",
                "total_images": 10
            },
            "prompt": {
                "template": "test {Expression}",
                "negative": "low quality"
            },
            "variations": {
                "Expression": {"count": 5}
            }
        }

        text = create_legacy_config_text(metadata)

        assert "DEPRECATION NOTICE" in text
        assert "metadata.json" in text
        assert "test_session" in text
        assert "2025-10-01T14:30:52" in text
        assert "Total Images: 10" in text
        assert "Prompt Template: test {Expression}" in text

    def test_legacy_text_variations_section(self):
        """Test that variations are listed in legacy text."""
        metadata = {
            "generation_info": {},
            "prompt": {"template": "", "negative": ""},
            "variations": {
                "Expression": {"count": 10},
                "Angle": {"count": 5}
            }
        }

        text = create_legacy_config_text(metadata)

        assert "Expression: 10 variations" in text
        assert "Angle: 5 variations" in text


class TestCompleteMetadataWorkflow:
    """Integration tests for complete metadata workflow."""

    def setup_method(self):
        """Set up temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_full_generation_session_metadata(self):
        """Test complete metadata generation for a realistic session."""
        metadata = generate_metadata_dict(
            prompt_template="masterpiece, {Expression}, {Angle}, beautiful girl",
            negative_prompt="low quality, blurry, bad anatomy",
            variations_loaded={
                "Expression": {
                    "smiling": "smiling",
                    "sad": "sad",
                    "angry": "angry"
                },
                "Angle": {
                    "front": "front view",
                    "side": "side view"
                }
            },
            generation_info={
                "date": "2025-10-01T14:30:52",
                "timestamp": "20251001_143052",
                "session_name": "anime_portraits",
                "total_images": 6,
                "generation_time_seconds": 125.5,
                "generation_mode": "combinatorial",
                "seed_mode": "progressive",
                "seed": 42,
                "total_combinations": 6
            },
            parameters={
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.0,
                "sampler": "DPM++ 2M Karras",
                "batch_size": 1,
                "batch_count": 1
            },
            output_info={
                "folder": "/path/to/output/20251001_143052_animePortraits",
                "filename_keys": ["Expression", "Angle"]
            },
            model_info={
                "checkpoint": "animePastelDream_v1.safetensors"
            },
            config_source="/path/to/configs/anime_portraits.json"
        )

        # Save to file
        save_metadata_json(metadata, self.temp_dir)

        # Load and verify
        loaded = load_metadata_json(self.temp_dir)

        assert loaded["version"] == "1.0"
        assert loaded["generation_info"]["total_images"] == 6
        assert loaded["prompt"]["template"] == "masterpiece, {Expression}, {Angle}, beautiful girl"
        assert loaded["variations"]["Expression"]["count"] == 3
        assert loaded["variations"]["Angle"]["count"] == 2
        assert loaded["generation"]["mode"] == "combinatorial"
        assert loaded["parameters"]["width"] == 512
        assert loaded["model"]["checkpoint"] == "animePastelDream_v1.safetensors"
        assert loaded["config_source"] == "/path/to/configs/anime_portraits.json"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
