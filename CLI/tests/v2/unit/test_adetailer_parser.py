"""
Unit tests for ADetailer file parsing and parameters integration
"""

import pytest
from pathlib import Path
from templating.loaders.adetailer_parser import parse_adetailer_file
from templating.resolvers.parameters_resolver import resolve_adetailer_parameter
from templating.models.adetailer import ADetailerConfig


class TestADetailerFileParser:
    """Test parsing .adetailer.yaml files"""

    def test_parse_single_detector_file(self, tmp_path):
        """Test parsing file with single detector"""
        yaml_content = """
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
    ad_steps: 40
    ad_mask_k_largest: 1
"""
        yaml_file = tmp_path / "face_hq.adetailer.yaml"
        yaml_file.write_text(yaml_content)

        config = parse_adetailer_file(str(yaml_file))

        assert isinstance(config, ADetailerConfig)
        assert len(config.detectors) == 1
        assert config.detectors[0].ad_model == "face_yolov9c.pt"
        assert config.detectors[0].ad_denoising_strength == 0.5
        assert config.detectors[0].ad_steps == 40

    def test_parse_multiple_detectors_file(self, tmp_path):
        """Test parsing file with multiple detectors"""
        yaml_content = """
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
  - ad_model: hand_yolov8n.pt
    ad_mask_k_largest: 2
    ad_denoising_strength: 0.4
"""
        yaml_file = tmp_path / "face_and_hands.adetailer.yaml"
        yaml_file.write_text(yaml_content)

        config = parse_adetailer_file(str(yaml_file))

        assert len(config.detectors) == 2
        assert config.detectors[0].ad_model == "face_yolov9c.pt"
        assert config.detectors[1].ad_model == "hand_yolov8n.pt"
        assert config.detectors[1].ad_mask_k_largest == 2

    def test_parse_file_with_custom_prompts(self, tmp_path):
        """Test parsing file with detector-specific prompts"""
        yaml_content = """
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_prompt: "detailed eyes, perfect skin"
    ad_negative_prompt: "blurry, distorted"
    ad_denoising_strength: 0.5
"""
        yaml_file = tmp_path / "face_custom.adetailer.yaml"
        yaml_file.write_text(yaml_content)

        config = parse_adetailer_file(str(yaml_file))

        assert config.detectors[0].ad_prompt == "detailed eyes, perfect skin"
        assert config.detectors[0].ad_negative_prompt == "blurry, distorted"

    def test_parse_file_missing_type(self, tmp_path):
        """Test parsing fails without type field"""
        yaml_content = """
version: "1.0"

detectors:
  - ad_model: test.pt
"""
        yaml_file = tmp_path / "invalid.adetailer.yaml"
        yaml_file.write_text(yaml_content)

        with pytest.raises(ValueError, match="type.*must be 'adetailer_config'"):
            parse_adetailer_file(str(yaml_file))

    def test_parse_file_wrong_type(self, tmp_path):
        """Test parsing fails with wrong type"""
        yaml_content = """
type: prompt_template
version: "1.0"

detectors:
  - ad_model: test.pt
"""
        yaml_file = tmp_path / "wrong_type.adetailer.yaml"
        yaml_file.write_text(yaml_content)

        with pytest.raises(ValueError, match="type.*must be 'adetailer_config'"):
            parse_adetailer_file(str(yaml_file))

    def test_parse_file_no_detectors(self, tmp_path):
        """Test parsing fails without detectors"""
        yaml_content = """
type: adetailer_config
version: "1.0"
"""
        yaml_file = tmp_path / "no_detectors.adetailer.yaml"
        yaml_file.write_text(yaml_content)

        with pytest.raises(ValueError, match="detectors.*required"):
            parse_adetailer_file(str(yaml_file))

    def test_parse_file_nonexistent(self):
        """Test parsing nonexistent file raises error"""
        with pytest.raises(FileNotFoundError):
            parse_adetailer_file("/nonexistent/file.adetailer.yaml")


class TestADetailerParametersResolver:
    """Test resolving parameters.adetailer in templates"""

    def test_resolve_string_path(self, tmp_path):
        """Test resolving string path to .adetailer.yaml"""
        yaml_content = """
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
"""
        yaml_file = tmp_path / "face.adetailer.yaml"
        yaml_file.write_text(yaml_content)

        config = resolve_adetailer_parameter(
            str(yaml_file),
            str(tmp_path)
        )

        assert isinstance(config, ADetailerConfig)
        assert len(config.detectors) == 1
        assert config.detectors[0].ad_model == "face_yolov9c.pt"

    def test_resolve_list_with_path_only(self, tmp_path):
        """Test resolving list with single path"""
        yaml_content = """
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
"""
        yaml_file = tmp_path / "face.adetailer.yaml"
        yaml_file.write_text(yaml_content)

        config = resolve_adetailer_parameter(
            [str(yaml_file)],
            str(tmp_path)
        )

        assert isinstance(config, ADetailerConfig)
        assert len(config.detectors) == 1

    def test_resolve_list_with_overrides(self, tmp_path):
        """Test resolving list with path + overrides dict"""
        yaml_content = """
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
    ad_steps: 40
"""
        yaml_file = tmp_path / "face.adetailer.yaml"
        yaml_file.write_text(yaml_content)

        config = resolve_adetailer_parameter(
            [str(yaml_file), {"ad_model": "face_yolov8n.pt", "ad_steps": 30}],
            str(tmp_path)
        )

        assert len(config.detectors) == 1
        # Overrides should replace values
        assert config.detectors[0].ad_model == "face_yolov8n.pt"
        assert config.detectors[0].ad_steps == 30
        # Non-overridden values should remain
        assert config.detectors[0].ad_denoising_strength == 0.5

    def test_resolve_list_multiple_files(self, tmp_path):
        """Test resolving list with multiple preset files"""
        face_yaml = """
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
"""
        hand_yaml = """
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: hand_yolov8n.pt
    ad_mask_k_largest: 2
"""
        face_file = tmp_path / "face.adetailer.yaml"
        hand_file = tmp_path / "hand.adetailer.yaml"
        face_file.write_text(face_yaml)
        hand_file.write_text(hand_yaml)

        config = resolve_adetailer_parameter(
            [str(face_file), str(hand_file)],
            str(tmp_path)
        )

        # Should merge detectors from both files
        assert len(config.detectors) == 2
        assert config.detectors[0].ad_model == "face_yolov9c.pt"
        assert config.detectors[1].ad_model == "hand_yolov8n.pt"

    def test_resolve_dict_inline_config(self, tmp_path):
        """Test resolving inline dict config (no file)"""
        inline_config = {
            "ad_model": "face_yolov9c.pt",
            "ad_denoising_strength": 0.6,
            "ad_steps": 50
        }

        config = resolve_adetailer_parameter(inline_config, str(tmp_path))

        assert len(config.detectors) == 1
        assert config.detectors[0].ad_model == "face_yolov9c.pt"
        assert config.detectors[0].ad_denoising_strength == 0.6
        assert config.detectors[0].ad_steps == 50

    def test_resolve_relative_path(self, tmp_path):
        """Test resolving relative path from base_path"""
        yaml_content = """
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
"""
        subdir = tmp_path / "presets"
        subdir.mkdir()
        yaml_file = subdir / "face.adetailer.yaml"
        yaml_file.write_text(yaml_content)

        # Resolve with relative path
        config = resolve_adetailer_parameter(
            "presets/face.adetailer.yaml",
            str(tmp_path)
        )

        assert isinstance(config, ADetailerConfig)
        assert config.detectors[0].ad_model == "face_yolov9c.pt"

    def test_resolve_empty_list(self, tmp_path):
        """Test resolving empty list returns None"""
        config = resolve_adetailer_parameter([], str(tmp_path))
        assert config is None

    def test_resolve_none(self, tmp_path):
        """Test resolving None returns None"""
        config = resolve_adetailer_parameter(None, str(tmp_path))
        assert config is None
