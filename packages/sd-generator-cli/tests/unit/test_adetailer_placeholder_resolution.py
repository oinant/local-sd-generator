"""
Tests for ADetailer placeholder resolution in overrides.

This module tests the ability to use placeholders in ADetailer prompts
that are resolved to the same values as the main prompt, without affecting
combinatorial generation.
"""

import pytest
from sd_generator_cli.templating.models.config_models import (
    ADetailerConfig,
    ADetailerDetector
)
from sd_generator_cli.templating.utils.placeholder_resolver import (
    resolve_text_placeholders,
    extract_placeholders_from_text
)


class TestPlaceholderResolver:
    """Test the placeholder_resolver utility module."""

    def test_resolve_simple_placeholder(self):
        """Test resolving a single placeholder."""
        text = "face with {Expression}"
        variations = {"Expression": "smiling"}
        result = resolve_text_placeholders(text, variations)
        assert result == "face with smiling"

    def test_resolve_multiple_placeholders(self):
        """Test resolving multiple placeholders."""
        text = "{Expression} face, {EyeColor} eyes, {HairColor} hair"
        variations = {
            "Expression": "happy",
            "EyeColor": "blue",
            "HairColor": "blonde"
        }
        result = resolve_text_placeholders(text, variations)
        assert result == "happy face, blue eyes, blonde hair"

    def test_resolve_with_missing_placeholder(self):
        """Test that missing placeholders are left unchanged."""
        text = "{Expression} face, {Missing} placeholder"
        variations = {"Expression": "smiling"}
        result = resolve_text_placeholders(text, variations)
        assert result == "smiling face, {Missing} placeholder"

    def test_resolve_empty_text(self):
        """Test resolving empty text."""
        result = resolve_text_placeholders("", {"Expression": "smiling"})
        assert result == ""

    def test_resolve_no_placeholders(self):
        """Test text without placeholders."""
        text = "detailed face, perfect skin"
        result = resolve_text_placeholders(text, {"Expression": "smiling"})
        assert result == "detailed face, perfect skin"

    def test_extract_placeholders_simple(self):
        """Test extracting placeholder names."""
        text = "{Expression} face, {EyeColor} eyes"
        result = extract_placeholders_from_text(text)
        assert result == ["Expression", "EyeColor"]

    def test_extract_placeholders_duplicates(self):
        """Test extracting with duplicates (should return unique)."""
        text = "{Pose}, {Pose}, {Angle}"
        result = extract_placeholders_from_text(text)
        assert result == ["Pose", "Angle"]

    def test_extract_placeholders_empty(self):
        """Test extracting from text without placeholders."""
        result = extract_placeholders_from_text("no placeholders here")
        assert result == []


class TestADetailerConfigPlaceholderResolution:
    """Test ADetailerConfig.resolve_placeholders() method."""

    def test_resolve_single_detector(self):
        """Test resolving placeholders in a single detector."""
        detector = ADetailerDetector(
            ad_model="face_yolov8n.pt",
            ad_prompt="detailed face, {Expression}, {EyeColor} eyes"
        )
        config = ADetailerConfig(enabled=True, detectors=[detector])

        variations = {"Expression": "smiling", "EyeColor": "blue"}
        resolved = config.resolve_placeholders(variations)

        assert resolved.enabled is True
        assert len(resolved.detectors) == 1
        assert resolved.detectors[0].ad_prompt == "detailed face, smiling, blue eyes"
        assert resolved.detectors[0].ad_model == "face_yolov8n.pt"

    def test_resolve_multiple_detectors(self):
        """Test resolving placeholders in multiple detectors."""
        face_detector = ADetailerDetector(
            ad_model="face_yolov8n.pt",
            ad_prompt="{Expression} face, {EyeColor} eyes"
        )
        hand_detector = ADetailerDetector(
            ad_model="hand_yolov8n.pt",
            ad_prompt="perfect hands, {Pose}"
        )
        config = ADetailerConfig(enabled=True, detectors=[face_detector, hand_detector])

        variations = {"Expression": "happy", "EyeColor": "green", "Pose": "waving"}
        resolved = config.resolve_placeholders(variations)

        assert len(resolved.detectors) == 2
        assert resolved.detectors[0].ad_prompt == "happy face, green eyes"
        assert resolved.detectors[1].ad_prompt == "perfect hands, waving"

    def test_resolve_negative_prompt(self):
        """Test resolving placeholders in ad_negative_prompt."""
        detector = ADetailerDetector(
            ad_model="face_yolov8n.pt",
            ad_prompt="face",
            ad_negative_prompt="bad {Expression}, deformed eyes"
        )
        config = ADetailerConfig(enabled=True, detectors=[detector])

        variations = {"Expression": "angry"}
        resolved = config.resolve_placeholders(variations)

        assert resolved.detectors[0].ad_negative_prompt == "bad angry, deformed eyes"

    def test_resolve_preserves_other_fields(self):
        """Test that resolution preserves all other detector fields."""
        detector = ADetailerDetector(
            ad_model="face_yolov8n.pt",
            ad_prompt="face, {Expression}",
            ad_confidence=0.5,
            ad_denoising_strength=0.4,
            ad_steps=30
        )
        config = ADetailerConfig(enabled=True, detectors=[detector])

        variations = {"Expression": "smiling"}
        resolved = config.resolve_placeholders(variations)

        # Check that other fields are preserved
        assert resolved.detectors[0].ad_model == "face_yolov8n.pt"
        assert resolved.detectors[0].ad_confidence == 0.5
        assert resolved.detectors[0].ad_denoising_strength == 0.4
        assert resolved.detectors[0].ad_steps == 30

    def test_resolve_with_missing_variations(self):
        """Test resolving when some placeholders have no variations."""
        detector = ADetailerDetector(
            ad_model="face_yolov8n.pt",
            ad_prompt="face, {Expression}, {Missing}"
        )
        config = ADetailerConfig(enabled=True, detectors=[detector])

        variations = {"Expression": "happy"}
        resolved = config.resolve_placeholders(variations)

        # Missing placeholder should remain unchanged
        assert resolved.detectors[0].ad_prompt == "face, happy, {Missing}"

    def test_resolve_empty_variations(self):
        """Test resolving with empty variations dict."""
        detector = ADetailerDetector(
            ad_model="face_yolov8n.pt",
            ad_prompt="face, {Expression}"
        )
        config = ADetailerConfig(enabled=True, detectors=[detector])

        resolved = config.resolve_placeholders({})

        # Placeholders should remain unchanged
        assert resolved.detectors[0].ad_prompt == "face, {Expression}"

    def test_resolve_no_placeholders(self):
        """Test resolving prompts without placeholders."""
        detector = ADetailerDetector(
            ad_model="face_yolov8n.pt",
            ad_prompt="detailed face, perfect skin"
        )
        config = ADetailerConfig(enabled=True, detectors=[detector])

        variations = {"Expression": "smiling"}
        resolved = config.resolve_placeholders(variations)

        # Text should remain unchanged
        assert resolved.detectors[0].ad_prompt == "detailed face, perfect skin"

    def test_resolve_returns_new_instance(self):
        """Test that resolve_placeholders returns a new instance."""
        detector = ADetailerDetector(
            ad_model="face_yolov8n.pt",
            ad_prompt="face, {Expression}"
        )
        original = ADetailerConfig(enabled=True, detectors=[detector])

        variations = {"Expression": "smiling"}
        resolved = original.resolve_placeholders(variations)

        # Original should be unchanged
        assert original.detectors[0].ad_prompt == "face, {Expression}"
        # Resolved should have new values
        assert resolved.detectors[0].ad_prompt == "face, smiling"
        # Should be different instances
        assert original is not resolved
        assert original.detectors[0] is not resolved.detectors[0]


class TestADetailerPlaceholderIntegration:
    """Integration tests for placeholder resolution in full workflow."""

    def test_parser_override_with_placeholders(self):
        """Test that parser preserves placeholders in overrides."""
        from sd_generator_cli.templating.loaders.parser import ConfigParser
        from pathlib import Path
        import tempfile
        import yaml

        # Create temporary YAML files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create detector file
            detector_yaml = tmpdir / "face.adetailer.yaml"
            detector_yaml.write_text(yaml.dump({
                "version": "2.0",
                "name": "Face Detector",
                "detector": {
                    "ad_model": "face_yolov8n.pt",
                    "ad_prompt": "default face prompt"
                }
            }))

            # Create prompt file with override containing placeholders
            prompt_yaml = tmpdir / "test.prompt.yaml"
            prompt_yaml.write_text(yaml.dump({
                "version": "2.0",
                "name": "Test Prompt",
                "generation": {
                    "mode": "combinatorial",
                    "seed": 42,
                    "seed_mode": "fixed",
                    "max_images": 1
                },
                "prompt": "test prompt",
                "parameters": {
                    "adetailer": {
                        "import": "face.adetailer.yaml",
                        "override": {
                            "ad_prompt": "detailed face, {Expression}, {EyeColor} eyes"
                        }
                    }
                }
            }))

            # Parse the file
            parser = ConfigParser()
            with open(prompt_yaml) as f:
                import yaml
                data = yaml.safe_load(f)
            config = parser.parse_prompt(data, prompt_yaml)

            # Check that override was applied with placeholders intact
            adetailer = config.parameters['adetailer']
            assert adetailer.detectors[0].ad_prompt == "detailed face, {Expression}, {EyeColor} eyes"

            # Now resolve with variations
            variations = {"Expression": "smiling", "EyeColor": "blue"}
            resolved = adetailer.resolve_placeholders(variations)

            assert resolved.detectors[0].ad_prompt == "detailed face, smiling, blue eyes"
