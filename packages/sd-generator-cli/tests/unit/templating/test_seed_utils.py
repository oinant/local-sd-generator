"""
Tests for seed_utils module (seed specification parsing).
"""

import pytest
from sd_generator_cli.templating.utils.seed_utils import parse_seeds


class TestParseSeedsExplicitList:
    """Test explicit list format: '1000,1005,1008'"""

    def test_simple_list(self):
        """Test basic comma-separated list."""
        result = parse_seeds("1000,1005,1008")
        assert result == [1000, 1005, 1008]

    def test_single_value(self):
        """Test single seed value."""
        result = parse_seeds("1000")
        assert result == [1000]

    def test_list_with_spaces(self):
        """Test list with spaces around values."""
        result = parse_seeds("1000 , 1005 , 1008")
        assert result == [1000, 1005, 1008]

    def test_negative_seeds_in_list(self):
        """Test list with negative seeds."""
        result = parse_seeds("-5,-2,0,10")
        assert result == [-5, -2, 0, 10]

    def test_invalid_list_non_integer(self):
        """Test list with non-integer values."""
        with pytest.raises(ValueError, match="Invalid seed list format"):
            parse_seeds("1000,abc,1008")


class TestParseSeedsRange:
    """Test range format: '1000-1019'"""

    def test_simple_range(self):
        """Test basic range."""
        result = parse_seeds("1000-1004")
        assert result == [1000, 1001, 1002, 1003, 1004]

    def test_range_with_spaces(self):
        """Test range with spaces."""
        result = parse_seeds("1000 - 1004")
        assert result == [1000, 1001, 1002, 1003, 1004]

    def test_single_value_range(self):
        """Test range with same start and end."""
        result = parse_seeds("1000-1000")
        assert result == [1000]

    def test_large_range(self):
        """Test large range (20 seeds)."""
        result = parse_seeds("1000-1019")
        assert len(result) == 20
        assert result[0] == 1000
        assert result[-1] == 1019

    def test_negative_start_range(self):
        """Test range with negative start."""
        result = parse_seeds("-5-5")
        assert result == [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]

    def test_negative_end_range(self):
        """Test range with negative end (invalid: start > end)."""
        with pytest.raises(ValueError, match="Invalid range: start .* > end"):
            parse_seeds("1000--1")  # 1000 > -1, so this is invalid

    def test_both_negative_range(self):
        """Test range with both negative values."""
        result = parse_seeds("-10--1")
        assert result == [-10, -9, -8, -7, -6, -5, -4, -3, -2, -1]

    def test_invalid_range_start_greater_than_end(self):
        """Test invalid range where start > end."""
        with pytest.raises(ValueError, match="Invalid range: start .* > end"):
            parse_seeds("1019-1000")

    def test_invalid_range_non_integer(self):
        """Test range with non-integer values."""
        with pytest.raises(ValueError, match="Invalid range format"):
            parse_seeds("1000-abc")


class TestParseSeedsCountStart:
    """Test count#start format: '20#1000'"""

    def test_simple_count_start(self):
        """Test basic count#start."""
        result = parse_seeds("5#1000")
        assert result == [1000, 1001, 1002, 1003, 1004]

    def test_count_start_with_spaces(self):
        """Test count#start with spaces."""
        result = parse_seeds("5 # 1000")
        assert result == [1000, 1001, 1002, 1003, 1004]

    def test_count_one(self):
        """Test count#start with count=1."""
        result = parse_seeds("1#1000")
        assert result == [1000]

    def test_large_count(self):
        """Test count#start with large count."""
        result = parse_seeds("20#1000")
        assert len(result) == 20
        assert result[0] == 1000
        assert result[-1] == 1019

    def test_negative_start(self):
        """Test count#start with negative start."""
        result = parse_seeds("5#-2")
        assert result == [-2, -1, 0, 1, 2]

    def test_invalid_count_zero(self):
        """Test count#start with zero count."""
        with pytest.raises(ValueError, match="Seed count must be positive"):
            parse_seeds("0#1000")

    def test_invalid_count_negative(self):
        """Test count#start with negative count."""
        with pytest.raises(ValueError, match="Seed count must be positive"):
            parse_seeds("-5#1000")

    def test_invalid_count_non_integer(self):
        """Test count#start with non-integer count."""
        with pytest.raises(ValueError, match="Invalid count#start format"):
            parse_seeds("abc#1000")

    def test_invalid_start_non_integer(self):
        """Test count#start with non-integer start."""
        with pytest.raises(ValueError, match="Invalid count#start format"):
            parse_seeds("5#abc")


class TestParseSeedsEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string(self):
        """Test empty string."""
        with pytest.raises(ValueError, match="Invalid seed specification"):
            parse_seeds("")

    def test_whitespace_only(self):
        """Test whitespace-only string."""
        with pytest.raises(ValueError, match="Invalid seed specification"):
            parse_seeds("   ")

    def test_invalid_format(self):
        """Test completely invalid format."""
        with pytest.raises(ValueError, match="Invalid seed specification"):
            parse_seeds("not_a_seed_spec")

    def test_mixed_separators(self):
        """Test string with multiple separator types (should fail)."""
        with pytest.raises(ValueError):
            parse_seeds("1000-1010,1020")  # Can't mix range and list

    def test_trailing_comma(self):
        """Test list with trailing comma."""
        result = parse_seeds("1000,1005,")
        # Should handle gracefully (empty strings filtered out by `if s.strip()`)
        assert result == [1000, 1005]

    def test_multiple_hash_symbols(self):
        """Test count#start with multiple hash symbols."""
        with pytest.raises(ValueError):
            parse_seeds("5#10#100")


class TestParseSeedsRealWorldUseCases:
    """Test real-world use cases from GitHub issue #64."""

    def test_ab_testing_20_seeds(self):
        """Test A/B testing with 20 seeds (issue example)."""
        result = parse_seeds("20#1000")
        assert len(result) == 20
        assert result == list(range(1000, 1020))

    def test_explicit_problematic_seeds(self):
        """Test explicit list of known problematic seeds."""
        result = parse_seeds("1000,1005,1008,1042")
        assert result == [1000, 1005, 1008, 1042]

    def test_range_for_consistency_testing(self):
        """Test range for consistency testing."""
        result = parse_seeds("1000-1019")
        assert len(result) == 20
        assert result[0] == 1000
        assert result[-1] == 1019
