"""
Tests for multi-field variation expansion functionality.
"""

import pytest
from pathlib import Path
from CLI.templating.multi_field import (
    is_multi_field_variation,
    load_multi_field_variations,
    expand_multi_field,
    merge_multi_field_into_chunk,
)
from CLI.templating.types import MultiFieldVariation


# Use fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_is_multi_field_variation():
    """Test detection of multi-field variation files."""
    # Multi-field type
    assert is_multi_field_variation({'type': 'multi_field'})

    # Not multi-field
    assert not is_multi_field_variation({'type': 'simple'})
    assert not is_multi_field_variation({})


def test_load_multi_field_variations():
    """Test loading multi-field variations from YAML."""
    variations_path = FIXTURES_DIR / "variations" / "ethnic_features.yaml"
    variations = load_multi_field_variations(variations_path)

    assert isinstance(variations, dict)
    assert "african" in variations
    assert "asian" in variations
    assert "caucasian" in variations

    # Check african variation
    african = variations["african"]
    assert isinstance(african, MultiFieldVariation)
    assert african.key == "african"
    assert "appearance.skin" in african.fields
    assert african.fields["appearance.skin"] == "dark skin, ebony complexion"
    assert "appearance.hair" in african.fields
    assert african.fields["appearance.hair"] == "coily black hair"


def test_expand_multi_field():
    """Test expanding a single multi-field variation into chunk fields."""
    variation = MultiFieldVariation(
        key="test",
        value="",
        fields={
            "appearance.skin": "dark skin",
            "appearance.hair": "coily hair",
            "appearance.eyes": "brown eyes"
        }
    )

    chunk_fields = {
        "appearance": {
            "age": "23 years old",
            "body_type": "athletic"
        },
        "identity": {
            "name": "Emma"
        }
    }

    result = expand_multi_field(variation, chunk_fields)

    # Original fields should be preserved
    assert result["appearance"]["age"] == "23 years old"
    assert result["appearance"]["body_type"] == "athletic"
    assert result["identity"]["name"] == "Emma"

    # Multi-field values should be added
    assert result["appearance"]["skin"] == "dark skin"
    assert result["appearance"]["hair"] == "coily hair"
    assert result["appearance"]["eyes"] == "brown eyes"


def test_expand_multi_field_overwrites():
    """Test that multi-field expansion overwrites existing values."""
    variation = MultiFieldVariation(
        key="test",
        value="",
        fields={
            "appearance.hair": "blonde hair"  # Will overwrite
        }
    )

    chunk_fields = {
        "appearance": {
            "hair": "brown hair"  # Original
        }
    }

    result = expand_multi_field(variation, chunk_fields)

    # Multi-field should win
    assert result["appearance"]["hair"] == "blonde hair"


def test_merge_multi_field_into_chunk():
    """Test merging multiple multi-field variations."""
    var1 = MultiFieldVariation(
        key="ethnicity",
        value="",
        fields={
            "appearance.skin": "dark skin",
            "appearance.hair": "coily hair"
        }
    )

    var2 = MultiFieldVariation(
        key="outfit",
        value="",
        fields={
            "clothing.top": "tank top",
            "clothing.bottom": "shorts"
        }
    )

    chunk_fields = {
        "identity": {
            "name": "Emma"
        }
    }

    result = merge_multi_field_into_chunk([var1, var2], chunk_fields)

    # All variations should be applied
    assert result["appearance"]["skin"] == "dark skin"
    assert result["appearance"]["hair"] == "coily hair"
    assert result["clothing"]["top"] == "tank top"
    assert result["clothing"]["bottom"] == "shorts"
    assert result["identity"]["name"] == "Emma"


def test_merge_with_inline_overrides():
    """Test that inline overrides have highest priority."""
    variation = MultiFieldVariation(
        key="test",
        value="",
        fields={
            "appearance.skin": "dark skin",
            "appearance.hair": "coily hair"
        }
    )

    chunk_fields = {
        "appearance": {
            "skin": "fair skin"  # Original value
        }
    }

    inline_overrides = {
        "appearance.skin": "red skin"  # Highest priority
    }

    result = merge_multi_field_into_chunk(
        [variation],
        chunk_fields,
        inline_overrides=inline_overrides
    )

    # Inline override should win
    assert result["appearance"]["skin"] == "red skin"
    # Multi-field value for hair should still apply
    assert result["appearance"]["hair"] == "coily hair"


def test_multi_field_creates_new_categories():
    """Test that multi-field can create new field categories."""
    variation = MultiFieldVariation(
        key="test",
        value="",
        fields={
            "new_category.field1": "value1"
        }
    )

    chunk_fields = {
        "existing": {
            "field": "value"
        }
    }

    result = expand_multi_field(variation, chunk_fields)

    # New category should be created
    assert "new_category" in result
    assert result["new_category"]["field1"] == "value1"
    # Existing should be preserved
    assert result["existing"]["field"] == "value"


def test_load_multi_field_real_fixture():
    """Test loading the actual ethnic_features.yaml fixture."""
    variations_path = FIXTURES_DIR / "variations" / "ethnic_features.yaml"
    variations = load_multi_field_variations(variations_path)

    # Test african variation
    african = variations["african"]
    assert "dark skin" in african.fields["appearance.skin"]
    assert "coily" in african.fields["appearance.hair"]
    assert "dark brown" in african.fields["appearance.eyes"]

    # Test asian variation
    asian = variations["asian"]
    assert "light skin" in asian.fields["appearance.skin"]
    assert "straight" in asian.fields["appearance.hair"]
    assert "almond" in asian.fields["appearance.eyes"]

    # Test caucasian variation
    caucasian = variations["caucasian"]
    assert "fair skin" in caucasian.fields["appearance.skin"]
    assert "blonde" in caucasian.fields["appearance.hair"]
    assert "blue" in caucasian.fields["appearance.eyes"]
