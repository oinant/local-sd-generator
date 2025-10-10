"""Tests for selectors.py"""

import pytest
from pathlib import Path
from templating.loaders import load_variations
from templating.selectors import (
    parse_selector,
    resolve_selectors,
    extract_placeholders
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_selector_keys():
    """Parse [happy,sad]"""
    selectors = parse_selector("[happy,sad]")
    assert len(selectors) == 1
    assert selectors[0].type == "keys"
    assert selectors[0].keys == ["happy", "sad"]


def test_parse_selector_indices():
    """Parse [1,5,8]"""
    selectors = parse_selector("[1,5,8]")
    assert len(selectors) == 1
    assert selectors[0].type == "indices"
    assert selectors[0].indices == [1, 5, 8]


def test_parse_selector_random():
    """Parse [random:5]"""
    selectors = parse_selector("[random:5]")
    assert len(selectors) == 1
    assert selectors[0].type == "random"
    assert selectors[0].count == 5


def test_parse_selector_range():
    """Parse [range:1-10]"""
    selectors = parse_selector("[range:1-10]")
    assert len(selectors) == 1
    assert selectors[0].type == "range"
    assert selectors[0].start == 1
    assert selectors[0].end == 10


def test_parse_selector_combined():
    """Parse [happy,sad,random:3]"""
    selectors = parse_selector("[happy,sad,random:3]")
    assert len(selectors) == 2
    assert selectors[0].type == "keys"
    assert selectors[0].keys == ["happy", "sad"]
    assert selectors[1].type == "random"
    assert selectors[1].count == 3


def test_parse_selector_all():
    """Parse [all] or empty"""
    selectors = parse_selector("[all]")
    assert len(selectors) == 1
    assert selectors[0].type == "all"

    selectors = parse_selector("[]")
    assert len(selectors) == 1
    assert selectors[0].type == "all"


def test_resolve_selectors_keys():
    """Resolve key selectors."""
    variations = load_variations(FIXTURES_DIR / "expressions.yaml")
    selectors = parse_selector("[happy,sad]")
    selected = resolve_selectors(variations, selectors)

    assert len(selected) == 2
    assert selected[0].key == "happy"
    assert selected[1].key == "sad"


def test_resolve_selectors_indices():
    """Resolve index selectors."""
    variations = load_variations(FIXTURES_DIR / "poses.yaml")
    selectors = parse_selector("[0,2,4]")
    selected = resolve_selectors(variations, selectors, index_base=0)

    assert len(selected) == 3
    assert selected[0].value == "standing"  # _0
    assert selected[1].value == "lying down"  # _2


def test_resolve_selectors_range():
    """Resolve range selectors."""
    variations = load_variations(FIXTURES_DIR / "poses.yaml")
    selectors = parse_selector("[range:0-4]")
    selected = resolve_selectors(variations, selectors, index_base=0)

    assert len(selected) == 5


def test_resolve_selectors_random():
    """Resolve random selectors."""
    variations = load_variations(FIXTURES_DIR / "expressions.yaml")
    selectors = parse_selector("[random:3]")
    selected = resolve_selectors(variations, selectors, random_seed=42)

    assert len(selected) == 3


def test_resolve_selectors_strict_mode():
    """Strict mode raises error on invalid key."""
    variations = load_variations(FIXTURES_DIR / "expressions.yaml")
    selectors = parse_selector("[unknown_key]")

    with pytest.raises(KeyError):
        resolve_selectors(variations, selectors, strict_mode=True)


def test_extract_placeholders():
    """Extract placeholders from template."""
    template = "beautiful {EXPR[happy,sad]}, {POSE}, detailed"
    placeholders = extract_placeholders(template)

    assert len(placeholders) == 2
    assert "EXPR" in placeholders
    assert placeholders["EXPR"] == "happy,sad"
    assert "POSE" in placeholders
    assert placeholders["POSE"] is None


def test_extract_placeholders_complex():
    """Extract complex placeholders."""
    template = "{A[1,2,random:3]}, {B[range:5-10]}, {C}"
    placeholders = extract_placeholders(template)

    assert len(placeholders) == 3
    assert placeholders["A"] == "1,2,random:3"
    assert placeholders["B"] == "range:5-10"
    assert placeholders["C"] is None
