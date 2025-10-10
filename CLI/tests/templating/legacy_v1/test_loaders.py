"""Tests for loaders.py"""

import pytest
from pathlib import Path
from templating.loaders import load_variations
from templating.types import Variation


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_yaml_with_keys():
    """Load a YAML file with key/value format."""
    variations = load_variations(FIXTURES_DIR / "expressions.yaml")

    assert len(variations) == 5
    assert "happy" in variations
    assert variations["happy"].value == "smiling, cheerful"
    assert variations["sad"].value == "crying, tears"


def test_load_yaml_simple_format():
    """Load a YAML file with simple list format."""
    variations = load_variations(FIXTURES_DIR / "poses.yaml")

    assert len(variations) == 10
    # Simple format generates auto keys like _0, _1, etc.
    assert "_0" in variations
    assert variations["_0"].value == "standing"


def test_load_nonexistent_file():
    """Loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_variations(FIXTURES_DIR / "nonexistent.yaml")


def test_variation_has_weight():
    """Variations have default weight of 1.0."""
    variations = load_variations(FIXTURES_DIR / "expressions.yaml")
    assert variations["happy"].weight == 1.0
