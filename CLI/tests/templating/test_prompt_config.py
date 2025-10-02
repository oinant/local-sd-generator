"""Tests for prompt_config.py"""

import pytest
from pathlib import Path
from templating.prompt_config import load_prompt_config


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_prompt_config():
    """Load a basic prompt config."""
    config = load_prompt_config(FIXTURES_DIR / "simple_test.prompt.yaml")

    assert config.name == "Simple Test"
    assert len(config.imports) == 2
    assert "EXPRESSIONS" in config.imports
    assert "POSES" in config.imports
    assert "masterpiece" in config.prompt_template
    assert config.negative_prompt == "low quality, blurry"
    assert config.generation_mode == "combinatorial"
    assert config.seed_mode == "progressive"
    assert config.seed == 42


def test_load_nonexistent_config():
    """Loading a non-existent config raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_prompt_config(FIXTURES_DIR / "nonexistent.prompt.yaml")


def test_config_defaults():
    """Test default values in config."""
    config = load_prompt_config(FIXTURES_DIR / "simple_test.prompt.yaml")

    assert config.index_base == 0
    assert config.strict_mode is True
    assert config.allow_duplicates is False
    assert config.random_seed is None
