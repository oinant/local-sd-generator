"""
Test duplicate placeholders in templates.

Verifies that when the same placeholder appears multiple times in a template,
all occurrences are replaced with the SAME value.
"""

import tempfile
from pathlib import Path

from sd_generator_cli.templating.orchestrator import V2Pipeline


def test_duplicate_placeholder_in_prompt():
    """Test that duplicate placeholders get the same value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create variations file
        variations_file = tmpdir_path / "expressions.yaml"
        variations_file.write_text("""
happy: smiling, joyful
sad: crying, depressed
angry: furious, mad
""")

        # Create prompt with DUPLICATE placeholder
        prompt_file = tmpdir_path / "test.prompt.yaml"
        prompt_file.write_text(f"""
version: '2.0'
name: 'Duplicate Placeholder Test'

imports:
  Expression: {variations_file.name}

prompt: |
  {{Expression}}, detailed portrait, text panel showing "{{Expression}}"

generation:
  mode: combinatorial
  seed: 42
  seed_mode: fixed
  max_images: -1
""")

        # Generate prompts
        pipeline = V2Pipeline(configs_dir=str(tmpdir_path))
        config = pipeline.load(str(prompt_file))
        resolved_config, context = pipeline.resolve(config)
        prompts = pipeline.generate(resolved_config, context)

        # Should have 3 prompts (happy, sad, angry)
        assert len(prompts) == 3

        # Check each prompt has the SAME value for both placeholders
        for prompt_dict in prompts:
            prompt = prompt_dict['prompt']
            variations = prompt_dict['variations']

            # Extract the expression value (already resolved)
            expression_value = variations['Expression']

            # The prompt should contain the expression value TWICE
            assert prompt.count(expression_value) == 2, \
                f"Expected '{expression_value}' to appear twice in prompt: {prompt}"

            # Check the exact format
            assert f'{expression_value}, detailed portrait, text panel showing "{expression_value}"' in prompt


def test_duplicate_placeholder_with_selectors():
    """Test that duplicate placeholders with selectors work correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create variations file
        variations_file = tmpdir_path / "colors.yaml"
        variations_file.write_text("""
red: bright red
blue: deep blue
green: vibrant green
yellow: golden yellow
""")

        # Create prompt with duplicate placeholder AND selector
        prompt_file = tmpdir_path / "test.prompt.yaml"
        prompt_file.write_text(f"""
version: '2.0'
name: 'Duplicate with Selector Test'

imports:
  Color: {variations_file.name}

prompt: |
  {{Color[red,blue]}}, background: {{Color[red,blue]}}

generation:
  mode: combinatorial
  seed: 42
  seed_mode: fixed
  max_images: -1
""")

        # Generate prompts
        pipeline = V2Pipeline(configs_dir=str(tmpdir_path))
        config = pipeline.load(str(prompt_file))
        resolved_config, context = pipeline.resolve(config)
        prompts = pipeline.generate(resolved_config, context)

        # Should have 2 prompts (red, blue)
        assert len(prompts) == 2

        # Check each prompt
        for prompt_dict in prompts:
            prompt = prompt_dict['prompt']
            variations = prompt_dict['variations']

            # Get the color value (already resolved)
            color_value = variations['Color']

            # The prompt should contain the color value TWICE
            assert prompt.count(color_value) == 2, \
                f"Expected '{color_value}' to appear twice in prompt: {prompt}"

            # Check the exact format
            expected_prompt = f'{color_value}, background: {color_value}'
            assert expected_prompt in prompt


def test_three_duplicate_placeholders():
    """Test using the same placeholder THREE times."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create variations file
        variations_file = tmpdir_path / "moods.yaml"
        variations_file.write_text("""
calm: peaceful, serene
excited: energetic, hyper
""")

        # Create prompt with TRIPLE placeholder
        prompt_file = tmpdir_path / "test.prompt.yaml"
        prompt_file.write_text(f"""
version: '2.0'
name: 'Triple Placeholder Test'

imports:
  Mood: {variations_file.name}

prompt: |
  {{Mood}}, portrait with {{Mood}} expression, {{Mood}} atmosphere

generation:
  mode: combinatorial
  seed: 42
  seed_mode: fixed
  max_images: -1
""")

        # Generate prompts
        pipeline = V2Pipeline(configs_dir=str(tmpdir_path))
        config = pipeline.load(str(prompt_file))
        resolved_config, context = pipeline.resolve(config)
        prompts = pipeline.generate(resolved_config, context)

        # Should have 2 prompts (calm, excited)
        assert len(prompts) == 2

        # Check each prompt has the value THREE times
        for prompt_dict in prompts:
            prompt = prompt_dict['prompt']
            variations = prompt_dict['variations']

            # Get the mood value (already resolved)
            mood_value = variations['Mood']

            # The prompt should contain the mood value THREE times
            assert prompt.count(mood_value) == 3, \
                f"Expected '{mood_value}' to appear 3 times in prompt: {prompt}"
