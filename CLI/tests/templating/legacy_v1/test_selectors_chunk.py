"""
Tests for chunk "with" syntax parsing in selectors.
"""

import pytest
from templating.selectors import parse_chunk_with_syntax


def test_parse_chunk_with_single_override():
    """Test parsing CHUNK with single field override."""
    content = "CHARACTER with ethnicity=ETHNICITIES[african,asian]"
    chunk_name, overrides = parse_chunk_with_syntax(content)

    assert chunk_name == "CHARACTER"
    assert "ethnicity" in overrides
    assert overrides["ethnicity"] == ("ETHNICITIES", "[african,asian]")


def test_parse_chunk_with_multiple_overrides():
    """Test parsing CHUNK with multiple field overrides."""
    content = "CHARACTER with ethnicity=ETHNICITIES[african], outfit=OUTFITS[casual]"
    chunk_name, overrides = parse_chunk_with_syntax(content)

    assert chunk_name == "CHARACTER"
    assert len(overrides) == 2
    assert overrides["ethnicity"] == ("ETHNICITIES", "[african]")
    assert overrides["outfit"] == ("OUTFITS", "[casual]")


def test_parse_chunk_with_no_selector():
    """Test parsing CHUNK with field but no selector."""
    content = "CHARACTER with ethnicity=ETHNICITIES"
    chunk_name, overrides = parse_chunk_with_syntax(content)

    assert chunk_name == "CHARACTER"
    assert overrides["ethnicity"] == ("ETHNICITIES", None)


def test_parse_chunk_without_with():
    """Test that non-with syntax returns None."""
    content = "EXPRESSIONS[happy,sad]"
    chunk_name, overrides = parse_chunk_with_syntax(content)

    assert chunk_name is None
    assert overrides is None


def test_parse_chunk_with_complex_selector():
    """Test parsing with complex selectors."""
    content = "CHAR with ethnicity=ETH[african,asian,random:2], pose=POSES[range:1-10]"
    chunk_name, overrides = parse_chunk_with_syntax(content)

    assert chunk_name == "CHAR"
    assert overrides["ethnicity"] == ("ETH", "[african,asian,random:2]")
    assert overrides["pose"] == ("POSES", "[range:1-10]")


def test_parse_chunk_with_underscores():
    """Test parsing with underscored names."""
    content = "MY_CHARACTER with skin_tone=SKIN_TONES[dark]"
    chunk_name, overrides = parse_chunk_with_syntax(content)

    assert chunk_name == "MY_CHARACTER"
    assert overrides["skin_tone"] == ("SKIN_TONES", "[dark]")
