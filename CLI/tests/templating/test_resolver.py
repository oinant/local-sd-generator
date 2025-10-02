"""Tests for resolver.py"""

import pytest
from pathlib import Path
from templating.prompt_config import load_prompt_config
from templating.resolver import resolve_prompt


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_resolve_simple_prompt():
    """Resolve a simple prompt configuration."""
    config = load_prompt_config(FIXTURES_DIR / "simple_test.prompt.yaml")
    variations = resolve_prompt(config, base_path=FIXTURES_DIR.parent)

    # happy,sad (2) × random:3 poses = 6 variations
    # Note: random:3 will select 3 random poses
    assert len(variations) >= 2  # At least 2 expressions

    # Check first variation has all required fields
    first = variations[0]
    assert first.index == 0
    assert first.seed == 42  # seed_mode: progressive, starts at 42
    assert "EXPRESSIONS" in first.placeholders
    assert "POSES" in first.placeholders
    assert "masterpiece" in first.final_prompt
    assert first.negative_prompt == "low quality, blurry"


def test_resolve_progressive_seeds():
    """Test progressive seed mode."""
    config = load_prompt_config(FIXTURES_DIR / "simple_test.prompt.yaml")
    variations = resolve_prompt(config, base_path=FIXTURES_DIR.parent)

    # Seeds should increment
    if len(variations) >= 2:
        assert variations[0].seed == 42
        assert variations[1].seed == 43


def test_resolve_placeholders_replaced():
    """Test that placeholders are replaced in final prompt."""
    config = load_prompt_config(FIXTURES_DIR / "simple_test.prompt.yaml")
    variations = resolve_prompt(config, base_path=FIXTURES_DIR.parent)

    # Final prompt should not contain {EXPRESSIONS} or {POSES}
    for v in variations:
        assert "{EXPRESSIONS" not in v.final_prompt
        assert "{POSES" not in v.final_prompt


def test_resolve_combinatorial_mode():
    """Test combinatorial generation mode."""
    # Create a simple config programmatically
    from templating.types import PromptConfig

    config = PromptConfig(
        name="Test",
        imports={
            "A": "fixtures/expressions.yaml",
        },
        prompt_template="{A[happy,sad]}",
        generation_mode="combinatorial",
        seed_mode="fixed",
        seed=100
    )

    variations = resolve_prompt(config, base_path=FIXTURES_DIR.parent)

    # happy,sad = 2 combinations
    assert len(variations) == 2

    # All seeds should be the same (fixed mode)
    assert all(v.seed == 100 for v in variations)


def test_resolve_max_images():
    """Test max_images limit."""
    from templating.types import PromptConfig

    config = PromptConfig(
        name="Test",
        imports={
            "A": "fixtures/expressions.yaml"
        },
        prompt_template="{A}",  # All 5 expressions
        generation_mode="combinatorial",
        seed_mode="progressive",
        seed=1,
        max_images=3
    )

    variations = resolve_prompt(config, base_path=FIXTURES_DIR.parent)

    # Limited to 3 even though there are 5 expressions
    assert len(variations) == 3
