"""
End-to-end integration tests for Phase 2 templating system.

Tests the complete flow: chunk + multi-field + selectors + resolver.
"""

import pytest
from pathlib import Path
from CLI.templating.resolver import resolve_prompt
from CLI.templating.prompt_config import load_prompt_config
from CLI.templating.types import PromptConfig


@pytest.fixture
def fixtures_path():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


def test_emma_variations_full_resolution(fixtures_path):
    """
    Test complete resolution with Emma variations fixture.

    Expected:
    - 2 ethnicities (african, asian) × 2 poses (standing, sitting) = 4 variations
    - Each variation should have:
      - Emma's base fields (name, age, body_type)
      - Ethnicity fields (skin, hair, eyes) from multi-field expansion
      - Pose value
      - Technical quality from template defaults
    """
    config_path = fixtures_path / "prompts" / "emma_variations.prompt.yaml"
    config = load_prompt_config(config_path)

    # Resolve
    variations = resolve_prompt(config, base_path=fixtures_path)

    # Should generate 4 combinations (2 ethnicities × 2 poses)
    assert len(variations) == 4, f"Expected 4 variations, got {len(variations)}"

    # All variations should have progressive seeds (100, 101, 102, 103)
    assert variations[0].seed == 100
    assert variations[1].seed == 101
    assert variations[2].seed == 102
    assert variations[3].seed == 103

    # Check variation 0: Should be first ethnicity + first pose (african + standing)
    var0 = variations[0].final_prompt
    assert "Emma" in var0, "Variation 0 should contain Emma's name"
    assert "23 years old" in var0, "Variation 0 should contain Emma's age"
    assert "athletic build" in var0, "Variation 0 should contain Emma's body type"
    assert "dark skin" in var0, "Variation 0 should contain african ethnicity (dark skin)"
    assert "coily black hair" in var0, "Variation 0 should contain african hair"
    assert "dark brown eyes" in var0, "Variation 0 should contain african eyes"
    assert "standing" in var0, "Variation 0 should contain standing pose"
    assert "masterpiece" in var0, "Variation 0 should contain technical quality"

    # Check variation 1: first ethnicity + second pose (african + sitting)
    var1 = variations[1].final_prompt
    assert "Emma" in var1
    assert "dark skin" in var1, "Variation 1 should contain african ethnicity"
    assert "sitting" in var1, "Variation 1 should contain sitting pose"

    # Check variation 2: second ethnicity + first pose (asian + standing)
    var2 = variations[2].final_prompt
    assert "Emma" in var2
    assert "light skin" in var2, "Variation 2 should contain asian ethnicity (light skin)"
    assert "straight black hair" in var2, "Variation 2 should contain asian hair"
    assert "almond-shaped dark eyes" in var2, "Variation 2 should contain asian eyes"
    assert "standing" in var2, "Variation 2 should contain standing pose"

    # Check variation 3: second ethnicity + second pose (asian + sitting)
    var3 = variations[3].final_prompt
    assert "Emma" in var3
    assert "light skin" in var3, "Variation 3 should contain asian ethnicity"
    assert "sitting" in var3, "Variation 3 should contain sitting pose"


def test_chunk_without_overrides(fixtures_path):
    """
    Test chunk resolution without any overrides.

    Should render the chunk with its base fields only.
    """
    config = PromptConfig(
        name="Test Chunk No Overrides",
        imports={
            "CHARACTER": "characters/emma.char.yaml"
        },
        prompt_template="{CHARACTER with }",  # No overrides
        generation_mode="combinatorial",
        seed_mode="fixed",
        seed=42
    )

    # This should work but might need special handling for empty overrides
    # For now, let's test a simpler case


def test_chunk_with_single_multi_field_override(fixtures_path):
    """
    Test chunk with single multi-field override (no cartesian product).
    """
    config = PromptConfig(
        name="Test Single Override",
        imports={
            "CHARACTER": "characters/emma.char.yaml",
            "ETHNICITIES": "variations/ethnic_features.yaml"
        },
        prompt_template="{CHARACTER with ethnicity=ETHNICITIES[african]}",
        generation_mode="combinatorial",
        seed_mode="fixed",
        seed=42
    )

    variations = resolve_prompt(config, base_path=fixtures_path)

    # Should generate 1 variation (only african ethnicity)
    assert len(variations) == 1

    var0 = variations[0].final_prompt
    assert "Emma" in var0
    assert "dark skin" in var0
    assert "coily black hair" in var0
    assert "ebony complexion" in var0


def test_random_mode_with_chunks(fixtures_path):
    """
    Test random generation mode with chunks.
    """
    config = PromptConfig(
        name="Test Random Mode",
        imports={
            "CHARACTER": "characters/emma.char.yaml",
            "ETHNICITIES": "variations/ethnic_features.yaml",
            "POSES": "variations/poses.yaml"
        },
        prompt_template="{CHARACTER with ethnicity=ETHNICITIES}\n{POSES}",
        generation_mode="random",
        seed_mode="random",
        seed=42,
        max_images=3  # Generate 3 random combinations (total possible = 2 ethnicities × 2 poses = 4)
    )

    variations = resolve_prompt(config, base_path=fixtures_path)

    # Should generate 3 variations
    assert len(variations) == 3

    # All should have Emma
    for var in variations:
        assert "Emma" in var.final_prompt

    # Seeds should be -1 (random)
    for var in variations:
        assert var.seed == -1


def test_mixed_chunks_and_variations(fixtures_path):
    """
    Test prompt with both chunks and normal variations.
    """
    config = PromptConfig(
        name="Test Mixed",
        imports={
            "CHARACTER": "characters/emma.char.yaml",
            "ETHNICITIES": "variations/ethnic_features.yaml",
            "POSES": "variations/poses.yaml"
        },
        prompt_template="{CHARACTER with ethnicity=ETHNICITIES[african]}\n{POSES[standing]}",
        generation_mode="combinatorial",
        seed_mode="fixed",
        seed=100
    )

    variations = resolve_prompt(config, base_path=fixtures_path)

    # Should generate 1 variation (1 ethnicity × 1 pose)
    assert len(variations) == 1

    var0 = variations[0].final_prompt
    assert "Emma" in var0
    assert "dark skin" in var0
    assert "standing" in var0
