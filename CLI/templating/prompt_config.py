"""
Loader for .prompt.yaml configuration files.
"""

from pathlib import Path
from typing import Union
import yaml

from .types import PromptConfig


def load_prompt_config(filepath: Union[str, Path]) -> PromptConfig:
    """
    Load a prompt configuration from a .prompt.yaml file.

    Expected format:
        name: "My Prompt"

        imports:
          EXPRESSIONS: variations/expressions.yaml
          POSES: variations/poses.yaml

        prompt: |
          beautiful girl, {EXPRESSIONS[happy,sad]}, {POSES[random:5]}

        negative_prompt: |
          low quality, blurry

        generation:
          mode: combinatorial  # or random
          seed_mode: progressive  # or fixed, random
          seed: 42
          max_images: 100

        selector_config:  # Optional
          index_base: 0
          strict_mode: true
          allow_duplicates: false
          random_seed: null

    Args:
        filepath: Path to the .prompt.yaml file

    Returns:
        PromptConfig object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If YAML format is invalid or required fields are missing
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt config file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML format in {filepath}: expected dict at root")

    # Required fields
    if 'name' not in data:
        raise ValueError(f"Missing required field 'name' in {filepath}")
    if 'prompt' not in data:
        raise ValueError(f"Missing required field 'prompt' in {filepath}")

    # Parse imports
    imports = data.get('imports', {})
    if not isinstance(imports, dict):
        raise ValueError(f"'imports' must be a dict in {filepath}")

    # Parse generation config
    generation = data.get('generation', {})
    if not isinstance(generation, dict):
        generation = {}

    # Parse selector config
    selector_config = data.get('selector_config', {})
    if not isinstance(selector_config, dict):
        selector_config = {}

    # Build PromptConfig
    config = PromptConfig(
        name=data['name'],
        imports=imports,
        prompt_template=data['prompt'].strip(),
        negative_prompt=data.get('negative_prompt', '').strip(),
        generation_mode=generation.get('mode', 'combinatorial'),
        seed_mode=generation.get('seed_mode', 'progressive'),
        seed=generation.get('seed', 42),
        max_images=generation.get('max_images'),
        index_base=selector_config.get('index_base', 0),
        strict_mode=selector_config.get('strict_mode', True),
        allow_duplicates=selector_config.get('allow_duplicates', False),
        random_seed=selector_config.get('random_seed')
    )

    # Validate generation mode
    if config.generation_mode not in ['combinatorial', 'random']:
        raise ValueError(
            f"Invalid generation mode '{config.generation_mode}' in {filepath}. "
            f"Expected 'combinatorial' or 'random'"
        )

    # Validate seed mode
    if config.seed_mode not in ['fixed', 'progressive', 'random']:
        raise ValueError(
            f"Invalid seed mode '{config.seed_mode}' in {filepath}. "
            f"Expected 'fixed', 'progressive', or 'random'"
        )

    return config
