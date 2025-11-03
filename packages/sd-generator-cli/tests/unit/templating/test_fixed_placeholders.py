"""
Unit tests for fixed placeholder functionality.

Tests parse_fixed_values() and _apply_fixed_to_context().
"""

import pytest
from sd_generator_cli.templating.utils.fixed_placeholders import parse_fixed_values


class TestParseFixedValues:
    """Tests for parse_fixed_values() function."""

    def test_parse_single_value(self):
        """Test parsing a single placeholder:key pair."""
        result = parse_fixed_values("mood:sad")
        assert result == {"mood": "sad"}

    def test_parse_multiple_values(self):
        """Test parsing multiple placeholder:key pairs."""
        result = parse_fixed_values("rendering:semi-realistic|mood:sad")
        assert result == {
            "rendering": "semi-realistic",
            "mood": "sad"
        }

    def test_parse_with_spaces(self):
        """Test parsing handles whitespace correctly."""
        result = parse_fixed_values(" mood : sad | rendering : anime ")
        assert result == {
            "mood": "sad",
            "rendering": "anime"
        }

    def test_parse_empty_string(self):
        """Test parsing empty string returns empty dict."""
        result = parse_fixed_values("")
        assert result == {}

    def test_parse_none(self):
        """Test parsing None returns empty dict."""
        result = parse_fixed_values(None)
        assert result == {}

    def test_parse_complex_keys(self):
        """Test parsing keys with hyphens and underscores."""
        result = parse_fixed_values("hair_color:neon-blue|body-type:athletic")
        assert result == {
            "hair_color": "neon-blue",
            "body-type": "athletic"
        }

    def test_parse_key_with_colon_in_value(self):
        """Test parsing when value contains colons."""
        result = parse_fixed_values("time:12:30:45")
        # Should split on FIRST colon only
        assert result == {"time": "12:30:45"}

    def test_parse_invalid_format_no_colon(self):
        """Test parsing raises ValueError for invalid format."""
        with pytest.raises(ValueError, match="Invalid --use-fixed format"):
            parse_fixed_values("mood-sad")

    def test_parse_invalid_format_no_colon_in_pair(self):
        """Test parsing raises ValueError when one pair has no colon."""
        with pytest.raises(ValueError, match="Invalid --use-fixed format"):
            parse_fixed_values("mood:sad|rendering-anime")

    def test_parse_empty_pairs_ignored(self):
        """Test parsing ignores empty pairs from trailing pipes."""
        result = parse_fixed_values("mood:sad||rendering:anime|")
        assert result == {
            "mood": "sad",
            "rendering": "anime"
        }


class TestApplyFixedToContext:
    """Tests for _apply_fixed_to_context() function."""

    def test_apply_single_fixed_value(self):
        """Test applying a single fixed value filters imports."""
        from unittest.mock import Mock

        # Create mock context
        context = Mock()
        context.imports = {
            "mood": {
                "sad": "sad, melancholic",
                "happy": "happy, joyful",
                "angry": "angry, fierce"
            },
            "pose": {
                "standing": "standing upright",
                "sitting": "sitting down"
            }
        }

        # Import the function
        from sd_generator_cli.cli import _apply_fixed_to_context

        # Apply fixed value
        fixed = {"mood": "sad"}
        result = _apply_fixed_to_context(context, fixed)

        # Check mood was filtered to single value
        assert len(result.imports["mood"]) == 1
        assert "sad" in result.imports["mood"]
        assert result.imports["mood"]["sad"] == "sad, melancholic"

        # Check pose was not filtered
        assert len(result.imports["pose"]) == 2

    def test_apply_multiple_fixed_values(self):
        """Test applying multiple fixed values."""
        from unittest.mock import Mock
        from sd_generator_cli.cli import _apply_fixed_to_context

        context = Mock()
        context.imports = {
            "mood": {
                "sad": "sad",
                "happy": "happy"
            },
            "pose": {
                "standing": "standing",
                "sitting": "sitting"
            }
        }

        fixed = {"mood": "sad", "pose": "sitting"}
        result = _apply_fixed_to_context(context, fixed)

        assert len(result.imports["mood"]) == 1
        assert "sad" in result.imports["mood"]
        assert len(result.imports["pose"]) == 1
        assert "sitting" in result.imports["pose"]

    def test_apply_fixed_placeholder_not_in_context(self):
        """Test applying fixed value for placeholder not in context (should skip)."""
        from unittest.mock import Mock
        from sd_generator_cli.cli import _apply_fixed_to_context

        context = Mock()
        context.imports = {
            "mood": {
                "sad": "sad",
                "happy": "happy"
            }
        }

        # Try to fix placeholder that doesn't exist
        fixed = {"nonexistent": "value"}
        result = _apply_fixed_to_context(context, fixed)

        # Should not raise error, just skip
        assert result.imports == context.imports

    def test_apply_fixed_key_not_found(self):
        """Test applying fixed value with key that doesn't exist raises error."""
        from unittest.mock import Mock
        from sd_generator_cli.cli import _apply_fixed_to_context

        context = Mock()
        context.imports = {
            "mood": {
                "sad": "sad",
                "happy": "happy"
            }
        }

        fixed = {"mood": "nonexistent_key"}

        with pytest.raises(ValueError, match="Key 'nonexistent_key' not found"):
            _apply_fixed_to_context(context, fixed)

    def test_apply_fixed_shows_available_keys_in_error(self):
        """Test error message shows available keys."""
        from unittest.mock import Mock
        from sd_generator_cli.cli import _apply_fixed_to_context

        context = Mock()
        context.imports = {
            "mood": {
                "sad": "sad",
                "happy": "happy",
                "angry": "angry"
            }
        }

        fixed = {"mood": "wrong"}

        with pytest.raises(ValueError, match="Available keys:"):
            _apply_fixed_to_context(context, fixed)

    def test_apply_fixed_empty_context(self):
        """Test applying fixed values to empty context."""
        from unittest.mock import Mock
        from sd_generator_cli.cli import _apply_fixed_to_context

        context = Mock()
        context.imports = {}

        fixed = {"mood": "sad"}
        result = _apply_fixed_to_context(context, fixed)

        # Should not raise error
        assert result.imports == {}

    def test_apply_fixed_no_imports_attribute(self):
        """Test applying fixed values when context has no imports attribute."""
        from unittest.mock import Mock
        from sd_generator_cli.cli import _apply_fixed_to_context

        context = Mock(spec=[])  # Context without imports attribute

        fixed = {"mood": "sad"}
        result = _apply_fixed_to_context(context, fixed)

        # Should return context as-is
        assert result == context
