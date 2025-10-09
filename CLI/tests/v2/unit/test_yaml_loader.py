"""
Unit tests for YamlLoader (Phase 1).

Tests YAML file loading, caching, and path resolution.
"""

import pytest
import yaml
from pathlib import Path
from templating.v2.loaders.yaml_loader import YamlLoader


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


class TestYamlLoaderCaching:
    """Tests for caching behavior."""

    def test_file_loaded_once_and_cached(self, tmp_path):
        """Test that a file is only loaded once and then cached."""
        loader = YamlLoader()
        test_file = tmp_path / "cached.yaml"
        test_file.write_text("name: 'Original'")

        # First load
        data1 = loader.load_file(test_file)
        assert data1['name'] == 'Original'

        # Modify file after first load
        test_file.write_text("name: 'Modified'")

        # Second load should return cached data (not modified)
        data2 = loader.load_file(test_file)
        assert data2['name'] == 'Original'  # Cached version

    def test_cache_key_uses_absolute_path(self, tmp_path):
        """Test that cache keys use absolute paths."""
        loader = YamlLoader()

        subdir = tmp_path / "configs"
        subdir.mkdir()
        test_file = subdir / "test.yaml"
        test_file.write_text("name: 'Test'")

        # Load with different relative paths pointing to same file
        data1 = loader.load_file("configs/test.yaml", base_path=tmp_path)
        data2 = loader.load_file("test.yaml", base_path=subdir)

        # Both should hit the same cache entry
        assert data1 is data2  # Same object reference

    def test_clear_cache(self, tmp_path):
        """Test clearing the cache."""
        loader = YamlLoader()
        test_file = tmp_path / "test.yaml"
        test_file.write_text("name: 'Original'")

        # Load and cache
        data1 = loader.load_file(test_file)
        assert data1['name'] == 'Original'

        # Clear cache
        loader.clear_cache()

        # Modify file
        test_file.write_text("name: 'Modified'")

        # Load again should get modified version (cache cleared)
        data2 = loader.load_file(test_file)
        assert data2['name'] == 'Modified'

    def test_invalidate_specific_file(self, tmp_path):
        """Test invalidating a specific file in the cache."""
        loader = YamlLoader()

        file1 = tmp_path / "file1.yaml"
        file2 = tmp_path / "file2.yaml"
        file1.write_text("name: 'File1'")
        file2.write_text("name: 'File2'")

        # Load both files
        data1 = loader.load_file(file1)
        data2 = loader.load_file(file2)
        assert data1['name'] == 'File1'
        assert data2['name'] == 'File2'

        # Invalidate file1 only
        loader.invalidate(file1)

        # Modify file1
        file1.write_text("name: 'File1Modified'")

        # Reload file1 (should get modified), file2 (should be cached)
        data1_new = loader.load_file(file1)
        data2_cached = loader.load_file(file2)

        assert data1_new['name'] == 'File1Modified'
        assert data2_cached is data2  # Still cached


class TestYamlLoaderCustomCache:
    """Tests for using a custom cache dictionary."""

    def test_use_custom_cache(self, tmp_path):
        """Test providing a custom cache dictionary."""
        custom_cache = {}
        loader = YamlLoader(cache=custom_cache)

        test_file = tmp_path / "test.yaml"
        test_file.write_text("name: 'Test'")

        # Load file
        loader.load_file(test_file)

        # Custom cache should be populated
        assert len(custom_cache) == 1
        assert str(test_file.resolve()) in custom_cache

    def test_shared_cache_between_loaders(self, tmp_path):
        """Test that multiple loaders can share the same cache."""
        shared_cache = {}
        loader1 = YamlLoader(cache=shared_cache)
        loader2 = YamlLoader(cache=shared_cache)

        test_file = tmp_path / "shared.yaml"
        test_file.write_text("name: 'Shared'")

        # Loader1 loads file
        data1 = loader1.load_file(test_file)

        # Loader2 should get cached data from shared cache
        data2 = loader2.load_file(test_file)

        assert data1 is data2  # Same object reference from shared cache
