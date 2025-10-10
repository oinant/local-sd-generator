"""
Test for parse_variations() to ensure structured format extracts only variations.

This test verifies the fix for the duplicate keys bug where metadata fields
(type, name, version, description) were incorrectly included in parsed variations.
"""

import pytest
from pathlib import Path
from templating.loaders.yaml_loader import YamlLoader
from templating.loaders.parser import ConfigParser


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "variations"


def test_parse_variations_structured_format():
    """
    Test that parse_variations() extracts ONLY the 'variations' dict,
    excluding metadata fields (type, name, version, description).

    This prevents duplicate key errors when merging multiple variation files.
    """
    # Load structured variation file
    loader = YamlLoader()
    parser = ConfigParser()

    fixture_path = FIXTURES_DIR / "haircolors_structured.yaml"
    raw_data = loader.load_file(fixture_path)

    # Verify fixture structure
    assert 'type' in raw_data
    assert 'name' in raw_data
    assert 'version' in raw_data
    assert 'variations' in raw_data

    # Parse variations
    result = parser.parse_variations(raw_data)

    # CRITICAL: Metadata fields should NOT be in result
    assert 'type' not in result, "BUG: 'type' metadata leaked into variations!"
    assert 'name' not in result, "BUG: 'name' metadata leaked into variations!"
    assert 'version' not in result, "BUG: 'version' metadata leaked into variations!"
    assert 'description' not in result, "BUG: 'description' metadata leaked into variations!"
    assert 'variations' not in result, "BUG: 'variations' key leaked into result!"

    # Only actual variation keys should be present
    assert 'BobCut' in result
    assert 'LongHair' in result
    assert 'PixieCut' in result
    assert 'Braided' in result
    assert len(result) == 4

    # Values should be strings
    assert result['BobCut'] == 'bob cut hair, chin-length'
    assert result['LongHair'] == 'long flowing hair, waist-length'


def test_parse_variations_flat_format():
    """
    Test that parse_variations() handles flat format (backward compatibility).

    Flat format has no metadata, just key: value pairs.
    """
    parser = ConfigParser()

    flat_data = {
        'BobCut': 'bob cut hair',
        'LongHair': 'long hair'
    }

    result = parser.parse_variations(flat_data)

    assert len(result) == 2
    assert 'BobCut' in result
    assert 'LongHair' in result
    assert result['BobCut'] == 'bob cut hair'


def test_parse_variations_in_memory():
    """
    Test parse_variations() with in-memory data (no file I/O).

    This isolates the parsing logic from file loading.
    """
    parser = ConfigParser()

    structured_data = {
        'type': 'variations',
        'name': 'Test',
        'version': '1.0',
        'variations': {
            'Key1': 'value1',
            'Key2': 'value2'
        }
    }

    result = parser.parse_variations(structured_data)

    # Should extract only variations dict
    assert result == {'Key1': 'value1', 'Key2': 'value2'}
    assert 'type' not in result
    assert 'name' not in result
    assert 'version' not in result
