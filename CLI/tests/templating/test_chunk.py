"""
Tests for chunk template and loading functionality.
"""

import pytest
from pathlib import Path
from CLI.templating.chunk import (
    load_chunk_template,
    load_chunk,
    resolve_chunk_fields,
    render_chunk,
)
from CLI.templating.types import ChunkTemplate, Chunk


# Use fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_chunk_template():
    """Test loading a chunk template file."""
    template_path = FIXTURES_DIR / "base" / "portrait_subject.char.template.yaml"
    template = load_chunk_template(template_path)

    assert isinstance(template, ChunkTemplate)
    assert template.name == "Portrait Subject Template"
    assert template.type == "chunk_template"
    assert "identity" in template.fields
    assert "appearance" in template.fields
    assert "name" in template.fields["identity"]
    assert "age" in template.fields["appearance"]


def test_load_chunk():
    """Test loading a chunk configuration file."""
    chunk_path = FIXTURES_DIR / "characters" / "emma.char.yaml"
    chunk = load_chunk(chunk_path)

    assert isinstance(chunk, Chunk)
    assert chunk.name == "Emma - Athletic Portrait"
    assert chunk.type == "chunk"
    assert chunk.implements == "base/portrait_subject.char.template.yaml"
    assert "identity" in chunk.fields
    assert chunk.fields["identity"]["name"] == "Emma"
    assert chunk.fields["appearance"]["age"] == "23 years old"


def test_resolve_chunk_fields_basic():
    """Test resolving chunk fields with template defaults."""
    template_path = FIXTURES_DIR / "base" / "portrait_subject.char.template.yaml"
    chunk_path = FIXTURES_DIR / "characters" / "emma.char.yaml"

    template = load_chunk_template(template_path)
    chunk = load_chunk(chunk_path)

    resolved = resolve_chunk_fields(chunk, template)

    # Check chunk values
    assert resolved["identity.name"] == "Emma"
    assert resolved["appearance.age"] == "23 years old"
    assert resolved["appearance.body_type"] == "athletic build"

    # Check template defaults
    assert "technical.quality" in resolved
    assert resolved["technical.quality"] == "masterpiece, best quality"


def test_resolve_chunk_fields_with_additional():
    """Test resolving with additional fields (multi-field expansion)."""
    template_path = FIXTURES_DIR / "base" / "portrait_subject.char.template.yaml"
    chunk_path = FIXTURES_DIR / "characters" / "emma.char.yaml"

    template = load_chunk_template(template_path)
    chunk = load_chunk(chunk_path)

    additional = {
        "appearance": {
            "skin": "dark skin, ebony complexion",
            "hair": "coily black hair",
            "eyes": "dark brown eyes"
        }
    }

    resolved = resolve_chunk_fields(chunk, template, additional)

    # Additional fields should override
    assert resolved["appearance.skin"] == "dark skin, ebony complexion"
    assert resolved["appearance.hair"] == "coily black hair"
    assert resolved["appearance.eyes"] == "dark brown eyes"

    # Chunk values should still be present
    assert resolved["identity.name"] == "Emma"
    assert resolved["appearance.age"] == "23 years old"


def test_render_chunk():
    """Test rendering a chunk with template output."""
    template_path = FIXTURES_DIR / "base" / "portrait_subject.char.template.yaml"
    chunk_path = FIXTURES_DIR / "characters" / "emma.char.yaml"

    template = load_chunk_template(template_path)
    chunk = load_chunk(chunk_path)

    resolved = resolve_chunk_fields(chunk, template)
    output = render_chunk(template, resolved)

    # Check that fields are present in output
    assert "Emma" in output
    assert "23 years old" in output
    assert "athletic build" in output
    assert "masterpiece, best quality" in output


def test_render_chunk_with_multi_field():
    """Test rendering with multi-field expansion."""
    template_path = FIXTURES_DIR / "base" / "portrait_subject.char.template.yaml"
    chunk_path = FIXTURES_DIR / "characters" / "emma.char.yaml"

    template = load_chunk_template(template_path)
    chunk = load_chunk(chunk_path)

    additional = {
        "appearance": {
            "skin": "dark skin, ebony complexion",
            "hair": "coily black hair",
            "eyes": "dark brown eyes"
        }
    }

    resolved = resolve_chunk_fields(chunk, template, additional)
    output = render_chunk(template, resolved)

    # Check multi-field values in output
    assert "dark skin, ebony complexion" in output
    assert "coily black hair" in output
    assert "dark brown eyes" in output

    # Chunk values should still be there
    assert "Emma" in output
    assert "23 years old" in output


def test_chunk_priority_order():
    """Test that field resolution respects priority order."""
    template_path = FIXTURES_DIR / "base" / "portrait_subject.char.template.yaml"
    chunk_path = FIXTURES_DIR / "characters" / "emma.char.yaml"

    template = load_chunk_template(template_path)
    chunk = load_chunk(chunk_path)

    # Emma's chunk specifies body_type as "athletic build"
    # Let's override it with additional fields
    additional = {
        "appearance": {
            "body_type": "slender build"
        }
    }

    resolved = resolve_chunk_fields(chunk, template, additional)

    # additional_fields should win
    assert resolved["appearance.body_type"] == "slender build"


def test_render_chunk_cleanup():
    """Test that rendering properly cleans up empty fields."""
    template_path = FIXTURES_DIR / "base" / "portrait_subject.char.template.yaml"
    chunk_path = FIXTURES_DIR / "characters" / "emma.char.yaml"

    template = load_chunk_template(template_path)
    chunk = load_chunk(chunk_path)

    resolved = resolve_chunk_fields(chunk, template)
    output = render_chunk(template, resolved)

    # Should not have double commas or trailing commas
    assert ",," not in output
    assert not output.endswith(",")
    # Should not have empty lines
    assert "\n\n" not in output
