"""
Tests for PromptNormalizer - Phase 6.

Tests the 5 normalization rules from spec section 8.1:
1. Trim whitespace at start/end of lines
2. Collapse multiple commas
3. Remove orphan commas at start/end
4. Normalize spacing around commas
5. Preserve max 1 blank line
"""

import pytest
from templating.v2.normalizers.normalizer import PromptNormalizer


class TestPromptNormalizer:
    """Test suite for PromptNormalizer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = PromptNormalizer()

    # Rule 1: Trim whitespace at start/end of lines
    def test_trim_line_whitespace(self):
        """Test trimming whitespace at start and end of lines."""
        input_text = "  1girl, beautiful  "
        expected = "1girl, beautiful"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_trim_multiline_whitespace(self):
        """Test trimming whitespace on multiple lines."""
        input_text = "  1girl, beautiful  \n  detailed background  "
        expected = "1girl, beautiful\ndetailed background"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    # Rule 2: Collapse multiple commas
    def test_collapse_double_commas(self):
        """Test collapsing double commas."""
        input_text = "1girl,, beautiful"
        expected = "1girl, beautiful"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_collapse_triple_commas(self):
        """Test collapsing triple commas."""
        input_text = "1girl,,, beautiful"
        expected = "1girl, beautiful"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_collapse_commas_with_spaces(self):
        """Test collapsing commas with spaces between them."""
        input_text = "1girl, , beautiful"
        expected = "1girl, beautiful"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    # Rule 3: Remove orphan commas at start/end
    def test_remove_leading_comma(self):
        """Test removing comma at start."""
        input_text = ", 1girl, beautiful"
        expected = "1girl, beautiful"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_remove_trailing_comma(self):
        """Test removing comma at end."""
        input_text = "1girl, beautiful,"
        expected = "1girl, beautiful"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_remove_both_orphan_commas(self):
        """Test removing commas at both start and end."""
        input_text = ", 1girl, beautiful,"
        expected = "1girl, beautiful"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    # Rule 4: Normalize spacing around commas
    def test_add_space_after_comma(self):
        """Test adding space after comma when missing."""
        input_text = "1girl,beautiful"
        expected = "1girl, beautiful"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_remove_space_before_comma(self):
        """Test removing space before comma."""
        input_text = "1girl , beautiful"
        expected = "1girl, beautiful"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_normalize_comma_spacing_complex(self):
        """Test normalizing complex comma spacing."""
        input_text = "1girl ,beautiful,detailed ,high quality"
        expected = "1girl, beautiful, detailed, high quality"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    # Rule 5: Preserve max 1 blank line
    def test_preserve_single_blank_line(self):
        """Test preserving single blank line."""
        input_text = "1girl,\n\ndetailed background"
        expected = "1girl,\n\ndetailed background"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_collapse_double_blank_lines(self):
        """Test collapsing 2 blank lines to 1."""
        input_text = "1girl,\n\n\ndetailed background"
        expected = "1girl,\n\ndetailed background"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_collapse_triple_blank_lines(self):
        """Test collapsing 3 blank lines to 1."""
        input_text = "1girl,\n\n\n\ndetailed background"
        expected = "1girl,\n\ndetailed background"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    # Combined rules
    def test_combined_all_rules(self):
        """Test applying all normalization rules together."""
        input_text = "  , 1girl,, beautiful  \n\n\n  detailed background,  "
        expected = "1girl, beautiful\n\ndetailed background"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_empty_placeholder_handling(self):
        """Test handling empty placeholders (spec section 8.2)."""
        # Simulates: @chunks.positive,\n,\ndetailed background
        # The orphan comma line is removed, blank line not preserved (SD ignores it anyway)
        input_text = "masterpiece,\n,\ndetailed background"
        expected = "masterpiece,\ndetailed background"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_empty_string(self):
        """Test normalizing empty string."""
        input_text = ""
        expected = ""
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_only_whitespace(self):
        """Test normalizing string with only whitespace."""
        input_text = "   \n\n   "
        expected = ""
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_only_commas(self):
        """Test normalizing string with only commas."""
        input_text = ",,,,"
        expected = ""
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_real_world_example(self):
        """Test with real-world SD prompt."""
        input_text = """  masterpiece, best quality,


        1girl, beautiful, detailed eyes,  ,
        dramatic lighting,,scenic background  """
        expected = "masterpiece, best quality,\n\n1girl, beautiful, detailed eyes,\ndramatic lighting, scenic background"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    # Edge cases
    def test_preserve_single_newline(self):
        """Test that single newlines are preserved."""
        input_text = "1girl,\nbeautiful"
        expected = "1girl,\nbeautiful"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected

    def test_preserve_content_commas(self):
        """Test that commas in meaningful content are preserved."""
        input_text = "1girl, 20 years old, slim build"
        expected = "1girl, 20 years old, slim build"
        result = self.normalizer.normalize_prompt(input_text)
        assert result == expected
