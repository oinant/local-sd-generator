"""
Tests for resolver import handling (multi-file, inline values, None handling).

Tests the bug fixes for:
1. Multi-file imports with PromptConfig normalization
2. Inline values with PromptConfig normalization
3. None data in is_multi_field_variation
"""

import pytest
from pathlib import Path
from templating.multi_field import is_multi_field_variation
from templating.resolver import _load_all_imports
from templating.types import PromptConfig, Variation


# Test is_multi_field_variation with None
def test_is_multi_field_variation_with_none():
    """Test that is_multi_field_variation handles None gracefully."""
    assert is_multi_field_variation(None) is False


def test_is_multi_field_variation_with_empty_dict():
    """Test that is_multi_field_variation handles empty dict."""
    assert is_multi_field_variation({}) is False


def test_is_multi_field_variation_with_valid_type():
    """Test that is_multi_field_variation detects multi-field correctly."""
    assert is_multi_field_variation({'type': 'multi_field'}) is True
    assert is_multi_field_variation({'type': 'multi-field'}) is True


def test_is_multi_field_variation_with_invalid_type():
    """Test that is_multi_field_variation rejects non-multi-field types."""
    assert is_multi_field_variation({'type': 'simple'}) is False
    assert is_multi_field_variation({'type': 'chunk'}) is False


# Test _load_all_imports with different formats
class TestLoadAllImports:
    """Tests for _load_all_imports function with various import formats."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to fixtures directory."""
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def base_path(self, fixtures_dir):
        """Return base path for test fixtures."""
        return fixtures_dir

    def test_load_single_file_import(self, base_path):
        """Test loading a single file import (string path)."""
        config = PromptConfig(
            name="Test",
            prompt_template="test {Expression}",
            imports={
                "Expression": "variations/expressions.yaml"
            },
            width=512,
            height=512
        )

        imports = _load_all_imports(config, base_path)

        assert "Expression" in imports
        assert imports["Expression"]["type"] == "variations"
        assert isinstance(imports["Expression"]["data"], dict)

    def test_load_multi_file_imports_normalized(self, base_path):
        """Test loading multi-file imports (PromptConfig normalized to dict with 'sources')."""
        # Simulate PromptConfig normalization
        config = PromptConfig(
            name="Test",
            prompt_template="test {Outfit}",
            imports={
                "Outfit": {
                    'type': 'multi-field',
                    'sources': [
                        'variations/outfits_casual.yaml',
                        'variations/outfits_formal.yaml'
                    ],
                    'merge_strategy': 'combine'
                }
            },
            width=512,
            height=512
        )

        imports = _load_all_imports(config, base_path)

        assert "Outfit" in imports
        assert imports["Outfit"]["type"] == "variations"
        # Should have merged variations from both files
        assert isinstance(imports["Outfit"]["data"], dict)
        assert len(imports["Outfit"]["data"]) > 0

    def test_load_inline_values_normalized_new_format(self):
        """Test loading inline values (PromptConfig normalized to dict with 'type: inline')."""
        config = PromptConfig(
            name="Test",
            
            prompt_template="test {View}",
            imports={
                "View": {
                    'type': 'inline',
                    'values': ['frontview', 'backview', 'from side', 'from above']
                }
            },
            width=512,
            height=512
        )

        imports = _load_all_imports(config, base_path=Path("."))

        assert "View" in imports
        assert imports["View"]["type"] == "variations"
        assert isinstance(imports["View"]["data"], dict)
        # Should have 4 variations
        assert len(imports["View"]["data"]) == 4
        # Check that values are converted to Variation objects
        assert all(isinstance(v, Variation) for v in imports["View"]["data"].values())
        # Check actual values
        values = [v.value for v in imports["View"]["data"].values()]
        assert 'frontview' in values
        assert 'backview' in values

    def test_load_inline_values_normalized_old_format(self):
        """Test loading inline values (old format with 'inline_values')."""
        config = PromptConfig(
            name="Test",
            
            prompt_template="test {Color}",
            imports={
                "Color": {
                    'inline_values': ['red', 'blue', 'green']
                }
            },
            width=512,
            height=512
        )

        imports = _load_all_imports(config, base_path=Path("."))

        assert "Color" in imports
        assert imports["Color"]["type"] == "variations"
        assert len(imports["Color"]["data"]) == 3
        values = [v.value for v in imports["Color"]["data"].values()]
        assert 'red' in values
        assert 'blue' in values
        assert 'green' in values

    def test_load_mixed_imports(self, base_path):
        """Test loading a mix of file imports and inline values."""
        config = PromptConfig(
            name="Test",
            
            prompt_template="test {Expression} {View}",
            imports={
                "Expression": "variations/expressions.yaml",  # File import
                "View": {
                    'type': 'inline',
                    'values': ['frontview', 'backview']
                }  # Inline values
            },
            width=512,
            height=512
        )

        imports = _load_all_imports(config, base_path)

        assert "Expression" in imports
        assert "View" in imports
        assert imports["Expression"]["type"] == "variations"
        assert imports["View"]["type"] == "variations"

    def test_invalid_import_format_raises_error(self):
        """Test that invalid import format raises ValueError."""
        config = PromptConfig(
            name="Test",
            
            prompt_template="test {Invalid}",
            imports={
                "Invalid": 12345  # Invalid type (int)
            },
            width=512,
            height=512
        )

        with pytest.raises(ValueError, match="Invalid import format"):
            _load_all_imports(config, base_path=Path("."))

    def test_unknown_dict_format_raises_error(self):
        """Test that unknown dict format raises ValueError."""
        config = PromptConfig(
            name="Test",
            
            prompt_template="test {Unknown}",
            imports={
                "Unknown": {
                    'unknown_key': 'unknown_value'
                }  # Missing 'sources', 'inline_values', or 'values'
            },
            width=512,
            height=512
        )

        with pytest.raises(ValueError, match="Unknown dict format"):
            _load_all_imports(config, base_path=Path("."))


# Edge cases
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_inline_values(self):
        """Test handling of empty inline values list."""
        config = PromptConfig(
            name="Test",
            
            prompt_template="test {Empty}",
            imports={
                "Empty": {
                    'type': 'inline',
                    'values': []
                }
            },
            width=512,
            height=512
        )

        imports = _load_all_imports(config, base_path=Path("."))

        assert "Empty" in imports
        assert len(imports["Empty"]["data"]) == 0

    def test_inline_values_with_non_strings(self):
        """Test that non-string inline values are filtered out."""
        config = PromptConfig(
            name="Test",
            
            prompt_template="test {Mixed}",
            imports={
                "Mixed": {
                    'type': 'inline',
                    'values': ['valid', 123, None, 'also_valid']
                }
            },
            width=512,
            height=512
        )

        imports = _load_all_imports(config, base_path=Path("."))

        # Only string values should be converted
        assert len(imports["Mixed"]["data"]) == 2
        values = [v.value for v in imports["Mixed"]["data"].values()]
        assert 'valid' in values
        assert 'also_valid' in values

    def test_multi_file_with_nonexistent_files(self, tmp_path):
        """Test multi-file import with some non-existent files."""
        # Create one valid file with proper variation format
        valid_file = tmp_path / "valid.yaml"
        valid_file.write_text("""type: variations
name: Test
version: '1.0'
variations:
  key1: value1
""")

        config = PromptConfig(
            name="Test",
            
            prompt_template="test {Test}",
            imports={
                "Test": {
                    'type': 'multi-field',
                    'sources': [
                        'valid.yaml',
                        'nonexistent.yaml'  # This file doesn't exist
                    ],
                    'merge_strategy': 'combine'
                }
            },
            width=512,
            height=512
        )

        # Should raise FileNotFoundError when trying to load nonexistent file
        with pytest.raises(FileNotFoundError):
            _load_all_imports(config, base_path=tmp_path)
