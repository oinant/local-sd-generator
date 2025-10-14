"""
Unit tests for ManifestWriter and ManifestImage (Snapshot System V2)
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from execution.manifest import ManifestWriter, ManifestImage


class TestManifestImage:
    """Test ManifestImage dataclass"""

    def test_manifest_image_creation(self):
        """Test creating a ManifestImage"""
        img = ManifestImage(
            filename="img_0001.png",
            seed=42,
            prompt="beautiful girl, smiling",
            negative_prompt="low quality, blurry",
            applied_variations={"Expression": "happy", "Angle": "front"}
        )

        assert img.filename == "img_0001.png"
        assert img.seed == 42
        assert img.prompt == "beautiful girl, smiling"
        assert img.negative_prompt == "low quality, blurry"
        assert img.applied_variations == {"Expression": "happy", "Angle": "front"}

    def test_manifest_image_to_dict(self):
        """Test converting ManifestImage to dictionary"""
        img = ManifestImage(
            filename="test.png",
            seed=123,
            prompt="test prompt",
            negative_prompt="test negative",
            applied_variations={"Var1": "val1"}
        )

        result = img.to_dict()

        assert result == {
            "filename": "test.png",
            "seed": 123,
            "prompt": "test prompt",
            "negative_prompt": "test negative",
            "applied_variations": {"Var1": "val1"}
        }


class TestManifestWriter:
    """Test ManifestWriter class"""

    def test_manifest_writer_init(self, tmp_path):
        """Test ManifestWriter initialization"""
        writer = ManifestWriter(tmp_path)
        assert writer.output_dir == tmp_path

    def test_write_manifest_creates_file(self, tmp_path):
        """Test that write() creates manifest.json file"""
        writer = ManifestWriter(tmp_path)

        snapshot = {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "runtime_info": {"sd_model_checkpoint": "test_model.safetensors"},
            "resolved_template": {"prompt": "test {Var}", "negative": "bad"},
            "generation_params": {"mode": "random", "num_images": 2},
            "api_params": {"steps": 30},
            "variations": {"Var": ["val1", "val2"]}
        }

        images = [
            ManifestImage("img_0001.png", 42, "test val1", "bad", {"Var": "val1"}),
            ManifestImage("img_0002.png", 43, "test val2", "bad", {"Var": "val2"})
        ]

        manifest_path = writer.write(snapshot, images)

        assert manifest_path.exists()
        assert manifest_path.name == "manifest.json"

    def test_write_manifest_content(self, tmp_path):
        """Test manifest content structure"""
        writer = ManifestWriter(tmp_path)

        snapshot = {
            "version": "2.0",
            "timestamp": "2025-10-13T14:23:45",
            "runtime_info": {"sd_model_checkpoint": "model.safetensors [abc123]"},
            "resolved_template": {
                "prompt": "masterpiece, {Expression}",
                "negative": "low quality"
            },
            "generation_params": {
                "mode": "combinatorial",
                "seed_mode": "progressive",
                "base_seed": 42,
                "num_images": 1,
                "total_combinations": 5
            },
            "api_params": {"steps": 30, "cfg_scale": 7.5},
            "variations": {"Expression": ["happy", "sad"]}
        }

        images = [
            ManifestImage(
                "img_0001.png",
                42,
                "masterpiece, happy",
                "low quality",
                {"Expression": "happy"}
            )
        ]

        manifest_path = writer.write(snapshot, images)

        # Load and verify content
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert "snapshot" in manifest
        assert "images" in manifest
        assert manifest["snapshot"]["version"] == "2.0"
        assert manifest["snapshot"]["runtime_info"]["sd_model_checkpoint"] == "model.safetensors [abc123]"
        assert len(manifest["images"]) == 1
        assert manifest["images"][0]["filename"] == "img_0001.png"
        assert manifest["images"][0]["seed"] == 42

    def test_write_manifest_utf8_encoding(self, tmp_path):
        """Test manifest handles UTF-8 characters correctly"""
        writer = ManifestWriter(tmp_path)

        snapshot = {
            "version": "2.0",
            "timestamp": "2025-10-13T14:23:45",
            "runtime_info": {"sd_model_checkpoint": "model.safetensors"},
            "resolved_template": {"prompt": "日本語 emoji 🎨", "negative": ""},
            "generation_params": {"mode": "random", "num_images": 1},
            "api_params": {},
            "variations": {}
        }

        images = [
            ManifestImage("test.png", 1, "日本語 emoji 🎨", "", {})
        ]

        manifest_path = writer.write(snapshot, images)

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert manifest["snapshot"]["resolved_template"]["prompt"] == "日本語 emoji 🎨"
        assert manifest["images"][0]["prompt"] == "日本語 emoji 🎨"

    def test_write_manifest_indented(self, tmp_path):
        """Test manifest is written with indentation"""
        writer = ManifestWriter(tmp_path)

        snapshot = {"version": "2.0", "timestamp": "2025-10-13T14:23:45"}
        images = []

        manifest_path = writer.write(snapshot, images)

        # Read raw file content
        content = manifest_path.read_text(encoding='utf-8')

        # Should be indented (not minified)
        assert "\n" in content
        assert "  " in content  # 2-space indentation

    def test_write_manifest_dict(self, tmp_path):
        """Test write_manifest_dict() method"""
        writer = ManifestWriter(tmp_path)

        manifest_dict = {
            "snapshot": {
                "version": "2.0",
                "timestamp": "2025-10-13T14:23:45"
            },
            "images": [
                {
                    "filename": "test.png",
                    "seed": 42,
                    "prompt": "test",
                    "negative_prompt": "",
                    "applied_variations": {}
                }
            ]
        }

        manifest_path = writer.write_manifest_dict(manifest_dict)

        assert manifest_path.exists()

        with open(manifest_path, 'r') as f:
            loaded = json.load(f)

        assert loaded == manifest_dict

    def test_write_empty_images_list(self, tmp_path):
        """Test writing manifest with no images"""
        writer = ManifestWriter(tmp_path)

        snapshot = {
            "version": "2.0",
            "timestamp": "2025-10-13T14:23:45"
        }

        manifest_path = writer.write(snapshot, [])

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        assert manifest["images"] == []

    def test_write_multiple_images(self, tmp_path):
        """Test writing manifest with multiple images"""
        writer = ManifestWriter(tmp_path)

        snapshot = {"version": "2.0", "timestamp": "2025-10-13T14:23:45"}

        images = [
            ManifestImage(f"img_{i:04d}.png", i, f"prompt {i}", "", {})
            for i in range(100)
        ]

        manifest_path = writer.write(snapshot, images)

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        assert len(manifest["images"]) == 100
        assert manifest["images"][0]["filename"] == "img_0000.png"
        assert manifest["images"][99]["filename"] == "img_0099.png"

    def test_manifest_path_returned(self, tmp_path):
        """Test that write() returns Path object"""
        writer = ManifestWriter(tmp_path)
        snapshot = {"version": "2.0"}
        images = []

        result = writer.write(snapshot, images)

        assert isinstance(result, Path)
        assert result == tmp_path / "manifest.json"
