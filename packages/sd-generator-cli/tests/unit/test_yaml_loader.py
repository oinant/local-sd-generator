"""
Unit tests for YamlLoader (Phase 1).

Tests YAML file loading, caching, and path resolution.
"""

import pytest
import yaml
from pathlib import Path
from sd_generator_cli.templating.loaders.yaml_loader import YamlLoader


class TestYamlLoaderPathResolution:
    """Tests for path resolution logic."""

    def test_resolve_relative_path(self, tmp_path):
        """Test resolving a relative path from a base path."""
        loader = YamlLoader()
        base_path = tmp_path / "configs"
        base_path.mkdir()

        resolved = loader.resolve_path("../variations/test.yaml", base_path)

        # Should resolve to parent of base_path
        expected = (tmp_path / "variations" / "test.yaml").resolve()
        assert resolved == expected

    def test_resolve_path_with_cwd_default(self):
        """Test resolving a path with no base_path (uses cwd)."""
        loader = YamlLoader()
        resolved = loader.resolve_path("test.yaml")

        # Should resolve relative to current working directory
        expected = (Path.cwd() / "test.yaml").resolve()
        assert resolved == expected

    def test_reject_absolute_path(self):
        """Test that absolute paths are rejected for portability."""
        loader = YamlLoader()

        with pytest.raises(ValueError, match="Absolute paths are not supported"):
            loader.resolve_path("/absolute/path/test.yaml")

    def test_resolve_nested_relative_path(self, tmp_path):
        """Test resolving nested relative paths."""
        loader = YamlLoader()
        base_path = tmp_path / "prompts" / "subdir"

        resolved = loader.resolve_path("../../templates/base.yaml", base_path)

        expected = (tmp_path / "templates" / "base.yaml").resolve()
        assert resolved == expected


class TestYamlLoaderFileLoading:
    """Tests for YAML file loading functionality."""

    def test_load_valid_yaml_file(self, tmp_path):
        """Test loading a valid YAML file."""
        loader = YamlLoader()
        test_file = tmp_path / "test.yaml"
        test_file.write_text("""
version: '2.0'
name: 'TestConfig'
template: 'masterpiece, {prompt}'
""")

        data = loader.load_file(test_file)

        assert data['version'] == '2.0'
        assert data['name'] == 'TestConfig'
        assert data['template'] == 'masterpiece, {prompt}'

    def test_load_file_with_base_path(self, tmp_path):
        """Test loading a file using relative path and base_path."""
        loader = YamlLoader()

        # Create structure: tmp_path/configs/subdir/test.yaml
        configs_dir = tmp_path / "configs"
        subdir = configs_dir / "subdir"
        subdir.mkdir(parents=True)

        test_file = subdir / "test.yaml"
        test_file.write_text("name: 'Test'")

        # Load with relative path from configs_dir
        data = loader.load_file("subdir/test.yaml", base_path=configs_dir)

        assert data['name'] == 'Test'

    def test_load_file_not_found(self, tmp_path):
        """Test loading a non-existent file raises FileNotFoundError."""
        loader = YamlLoader()
        missing_file = tmp_path / "missing.yaml"

        with pytest.raises(FileNotFoundError, match="File not found"):
            loader.load_file(missing_file)

    def test_load_malformed_yaml(self, tmp_path):
        """Test loading malformed YAML raises YAMLError."""
        loader = YamlLoader()
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("""
invalid yaml:
  - item1
  item2 without dash
    bad indentation
""")

        with pytest.raises(yaml.YAMLError, match="Failed to parse YAML"):
            loader.load_file(bad_file)

    def test_load_empty_yaml_file(self, tmp_path):
        """Test loading an empty YAML file returns None."""
        loader = YamlLoader()
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")

        data = loader.load_file(empty_file)

        assert data is None


# NOTE: Caching tests removed - cache was disabled as premature optimization
# (see yaml_loader.py lines 53-58 and 71-72)
# The cache added complexity without measurable benefit for local NVMe SSD access
