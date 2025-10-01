"""
Tests for the output_namer module (SF-4).

Tests cover:
- Filename component sanitization
- Session folder name generation
- Image filename generation
- Edge cases and special characters
"""

import pytest
from datetime import datetime
import sys
import os

# Add CLI to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'CLI'))

from output.output_namer import (
    sanitize_filename_component,
    generate_session_folder_name,
    generate_image_filename,
    format_timestamp_iso
)


class TestSanitizeFilenameComponent:
    """Tests for sanitize_filename_component function."""

    def test_basic_sanitization(self):
        """Test basic string sanitization to camelCase."""
        assert sanitize_filename_component("happy smile") == "happySmile"
        assert sanitize_filename_component("test-value") == "testValue"

    def test_space_replacement(self):
        """Test that spaces create camelCase."""
        assert sanitize_filename_component("front view") == "frontView"
        assert sanitize_filename_component("multiple  spaces") == "multipleSpaces"

    def test_special_characters(self):
        """Test special character handling with camelCase."""
        assert sanitize_filename_component("test:file*name?") == "testFileName"
        assert sanitize_filename_component("path/to/file") == "pathToFile"
        assert sanitize_filename_component("test,comma;semicolon") == "testCommaSemicolon"

    def test_unicode_and_accents(self):
        """Test handling of unicode and accented characters."""
        assert sanitize_filename_component("café") == "caf"
        assert sanitize_filename_component("naïve") == "nave"
        # Emoji should be removed
        result = sanitize_filename_component("smile😊test")
        assert "😊" not in result
        assert result == "smiletest"

    def test_length_limiting(self):
        """Test that long strings are truncated to max_length."""
        long_string = "a" * 100
        result = sanitize_filename_component(long_string, max_length=50)
        assert len(result) == 50

        # Test with custom max_length - multiple words
        result = sanitize_filename_component("very long text " * 20, max_length=20)
        assert len(result) == 20

    def test_empty_and_edge_cases(self):
        """Test empty strings and edge cases."""
        assert sanitize_filename_component("") == "empty"
        assert sanitize_filename_component("   ") == "empty"
        assert sanitize_filename_component("!!!") == "unnamed"
        assert sanitize_filename_component("___") == "unnamed"

    def test_multiple_consecutive_chars(self):
        """Test handling of multiple words (creates camelCase)."""
        assert sanitize_filename_component("test   value") == "testValue"
        assert sanitize_filename_component("test---value") == "testValue"
        assert sanitize_filename_component("test_value") == "testValue"

    def test_preserves_alphanumeric(self):
        """Test that alphanumeric characters are preserved in camelCase."""
        assert sanitize_filename_component("test123ABC") == "test123abc"
        assert sanitize_filename_component("ABC 123 xyz") == "abc123Xyz"


class TestGenerateSessionFolderName:
    """Tests for generate_session_folder_name function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dt = datetime(2025, 10, 1, 14, 30, 52)

    def test_with_session_name(self):
        """Test folder naming with provided session name."""
        result = generate_session_folder_name(self.test_dt, "anime_test_v2")
        assert result == "20251001_143052_animeTestV2"

    def test_with_session_name_sanitization(self):
        """Test that session names are properly sanitized to camelCase."""
        result = generate_session_folder_name(self.test_dt, "test session")
        assert result == "20251001_143052_testSession"

        result = generate_session_folder_name(self.test_dt, "test/session:name")
        assert result == "20251001_143052_testSessionName"

    def test_with_filename_keys(self):
        """Test folder naming with filename_keys (sanitized to camelCase)."""
        result = generate_session_folder_name(
            self.test_dt,
            filename_keys=["Expression", "Angle"]
        )
        assert result == "20251001_143052_expression_angle"

    def test_with_filename_keys_multiple(self):
        """Test folder naming with multiple filename_keys (sanitized to camelCase)."""
        result = generate_session_folder_name(
            self.test_dt,
            filename_keys=["Expression", "Angle", "Lighting"]
        )
        assert result == "20251001_143052_expression_angle_lighting"

    def test_default_fallback(self):
        """Test default folder naming when no options provided."""
        result = generate_session_folder_name(self.test_dt)
        assert result == "20251001_143052_session"

    def test_session_name_priority(self):
        """Test that session_name takes priority over filename_keys."""
        result = generate_session_folder_name(
            self.test_dt,
            session_name="custom_name",
            filename_keys=["Expression", "Angle"]
        )
        assert result == "20251001_143052_customName"
        assert "expression" not in result.lower() or result.endswith("customName")

    def test_timestamp_format(self):
        """Test timestamp formatting."""
        dt = datetime(2025, 1, 5, 9, 5, 3)
        result = generate_session_folder_name(dt, "test")
        assert result.startswith("20250105_090503")


class TestGenerateImageFilename:
    """Tests for generate_image_filename function."""

    def test_simple_index_only(self):
        """Test filename with index only (no variations)."""
        assert generate_image_filename(1) == "001.png"
        assert generate_image_filename(42) == "042.png"
        assert generate_image_filename(999) == "999.png"

    def test_with_single_key(self):
        """Test filename with single variation key."""
        result = generate_image_filename(
            5,
            variation_dict={"Expression": "smiling"},
            filename_keys=["Expression"]
        )
        assert result == "005_Expression-smiling.png"

    def test_with_multiple_keys(self):
        """Test filename with multiple variation keys."""
        result = generate_image_filename(
            42,
            variation_dict={"Expression": "smiling", "Angle": "front view"},
            filename_keys=["Expression", "Angle"]
        )
        assert result == "042_Expression-smiling_Angle-frontView.png"

    def test_key_order_preservation(self):
        """Test that filename_keys order is preserved."""
        variations = {"Expression": "happy", "Angle": "side", "Lighting": "soft"}

        result1 = generate_image_filename(1, variations, ["Expression", "Angle"])
        assert result1 == "001_Expression-happy_Angle-side.png"

        result2 = generate_image_filename(1, variations, ["Angle", "Expression"])
        assert result2 == "001_Angle-side_Expression-happy.png"

    def test_value_sanitization(self):
        """Test that variation values are sanitized to camelCase."""
        result = generate_image_filename(
            1,
            variation_dict={"Expression": "big smile", "Pose": "action/dynamic"},
            filename_keys=["Expression", "Pose"]
        )
        assert result == "001_Expression-bigSmile_Pose-actionDynamic.png"

    def test_missing_key_in_dict(self):
        """Test behavior when filename_key not in variation_dict."""
        result = generate_image_filename(
            1,
            variation_dict={"Expression": "smiling"},
            filename_keys=["Expression", "Angle"]  # Angle missing
        )
        # Should only include Expression
        assert result == "001_Expression-smiling.png"
        assert "Angle" not in result

    def test_empty_filename_keys(self):
        """Test that empty filename_keys falls back to index only."""
        result = generate_image_filename(
            10,
            variation_dict={"Expression": "smiling"},
            filename_keys=[]
        )
        assert result == "010.png"

    def test_none_values(self):
        """Test behavior with None values."""
        assert generate_image_filename(5, None, None) == "005.png"
        assert generate_image_filename(5, {}, []) == "005.png"


class TestFormatTimestampISO:
    """Tests for format_timestamp_iso function."""

    def test_iso_format(self):
        """Test ISO 8601 formatting."""
        dt = datetime(2025, 10, 1, 14, 30, 52)
        result = format_timestamp_iso(dt)
        assert result == "2025-10-01T14:30:52"

    def test_iso_format_with_single_digits(self):
        """Test ISO formatting with single digit values."""
        dt = datetime(2025, 1, 5, 9, 5, 3)
        result = format_timestamp_iso(dt)
        assert result == "2025-01-05T09:05:03"


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    def test_complete_session_workflow(self):
        """Test a complete session naming workflow."""
        dt = datetime(2025, 10, 1, 14, 30, 52)

        # Create session folder name
        folder = generate_session_folder_name(
            dt,
            session_name="anime_portraits"
        )
        assert folder == "20251001_143052_animePortraits"

        # Create image filenames in that session
        variations = [
            {"Expression": "smiling", "Angle": "front"},
            {"Expression": "sad", "Angle": "side"},
            {"Expression": "angry", "Angle": "back"},
        ]

        filenames = []
        for i, var_dict in enumerate(variations, 1):
            filename = generate_image_filename(
                i,
                var_dict,
                ["Expression", "Angle"]
            )
            filenames.append(filename)

        assert filenames == [
            "001_Expression-smiling_Angle-front.png",
            "002_Expression-sad_Angle-side.png",
            "003_Expression-angry_Angle-back.png",
        ]

    def test_backward_compatibility_mode(self):
        """Test backward compatibility (no filename_keys)."""
        dt = datetime(2025, 10, 1, 14, 30, 52)

        # Session name sanitized to camelCase
        folder = generate_session_folder_name(dt, "test_session")
        assert folder == "20251001_143052_testSession"

        # Old behavior: index-only filenames
        filenames = [generate_image_filename(i) for i in range(1, 4)]
        assert filenames == ["001.png", "002.png", "003.png"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
