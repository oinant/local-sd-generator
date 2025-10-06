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

    Supports template inheritance via 'extends' field:
        extends: base_template.prompt.yaml
        template: "additional content to append"

    Expected format:
        name: "My Prompt"

        extends: base_template.prompt.yaml  # Optional
        extends_mode: append  # or prepend, replace (default: append)

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

    # Handle template inheritance
    if 'extends' in data:
        base_template_path = filepath.parent / data['extends']
        if not base_template_path.exists():
            raise FileNotFoundError(f"Base template not found: {base_template_path}")

        # Load base template recursively
        base_config_data = _load_prompt_config_recursive(base_template_path)

        # Merge configurations
        extends_mode = data.get('extends_mode', 'append')
        data = _merge_configs(base_config_data, data, extends_mode)

    return _parse_prompt_config(data, filepath)


def _load_prompt_config_recursive(filepath: Path) -> dict:
    """Load a prompt config file recursively, handling extends."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML format in {filepath}: expected dict at root")

    # Handle nested extends
    if 'extends' in data:
        base_template_path = filepath.parent / data['extends']
        if not base_template_path.exists():
            raise FileNotFoundError(f"Base template not found: {base_template_path}")

        base_config_data = _load_prompt_config_recursive(base_template_path)
        extends_mode = data.get('extends_mode', 'append')
        data = _merge_configs(base_config_data, data, extends_mode)

    return data


def _merge_configs(base: dict, override: dict, extends_mode: str) -> dict:
    """
    Merge two config dicts with inheritance.

    Args:
        base: Base configuration
        override: Override configuration
        extends_mode: How to merge templates ('append', 'prepend', 'replace')

    Returns:
        Merged configuration
    """
    import copy
    result = copy.deepcopy(base)

    # Merge each section
    for key, value in override.items():
        if key in ('extends', 'extends_mode'):
            # Skip inheritance metadata
            continue

        if key in ('template', 'prompt'):
            # Special handling for template/prompt based on extends_mode
            base_template = result.get('template') or result.get('prompt', '')
            override_template = value

            if extends_mode == 'append':
                result[key] = base_template + '\n' + override_template
            elif extends_mode == 'prepend':
                result[key] = override_template + '\n' + base_template
            elif extends_mode == 'replace':
                result[key] = override_template
            else:
                raise ValueError(f"Invalid extends_mode: {extends_mode}")

        elif key == 'negative_prompt':
            # Always append negative prompts
            base_neg = result.get('negative_prompt', '')
            if base_neg:
                result[key] = base_neg + '\n' + value
            else:
                result[key] = value

        elif key in ('imports', 'variations', 'generation', 'parameters', 'selector_config', 'output'):
            # Deep merge for nested dicts
            if key not in result:
                result[key] = {}
            if isinstance(value, dict) and isinstance(result[key], dict):
                result[key].update(value)
            else:
                result[key] = value

        elif key == 'name':
            # Override name (child takes precedence)
            result[key] = value

        else:
            # Other fields: override takes precedence
            result[key] = value

    return result


def _parse_prompt_config(data: dict, filepath: Path) -> PromptConfig:
    """Parse a prompt config dict into a PromptConfig object."""

    # Required fields
    if 'name' not in data:
        raise ValueError(f"Missing required field 'name' in {filepath}")

    # Support both 'prompt' (Phase 1) and 'template' (Phase 2)
    prompt_template = None
    if 'prompt' in data:
        prompt_template = data['prompt']
    elif 'template' in data:
        prompt_template = data['template']
    else:
        # Allow missing template if extending (will be inherited)
        if 'extends' not in data:
            raise ValueError(f"Missing required field 'prompt' or 'template' in {filepath}")
        prompt_template = ""

    # Parse imports (Phase 1) or variations (Phase 2)
    # Support both for backward compatibility
    imports = data.get('imports', {})
    if not imports:
        # Try 'variations' for Phase 2 format
        imports = data.get('variations', {})
    if not isinstance(imports, dict):
        raise ValueError(f"'imports' or 'variations' must be a dict in {filepath}")

    # Normalize imports: convert list values to multi-field format, detect inline variations
    normalized_imports = {}
    for key, value in imports.items():
        if isinstance(value, list):
            # Check if list contains file paths or inline values
            if value and isinstance(value[0], str) and ('/' in value[0] or value[0].endswith('.yaml')):
                # List of files - convert to multi-field sources format
                normalized_imports[key] = {
                    'type': 'multi-field',
                    'sources': value,
                    'merge_strategy': 'combine'
                }
            else:
                # Inline list of values
                normalized_imports[key] = {
                    'type': 'inline',
                    'values': value
                }
        elif isinstance(value, dict):
            # Inline dict of key: value variations
            normalized_imports[key] = {
                'type': 'inline',
                'values': value
            }
        else:
            # String path - keep as is
            normalized_imports[key] = value
    imports = normalized_imports

    # Parse generation config
    generation = data.get('generation', {})
    if not isinstance(generation, dict):
        generation = {}

    # Parse selector config
    selector_config = data.get('selector_config', {})
    if not isinstance(selector_config, dict):
        selector_config = {}

    # Parse parameters config (SD API + Hires Fix)
    parameters = data.get('parameters', {})
    if not isinstance(parameters, dict):
        parameters = {}

    # Get base_path from YAML (Phase 2) - relative to the .prompt.yaml file
    yaml_base_path = data.get('base_path', None)

    # Build PromptConfig
    config = PromptConfig(
        name=data['name'],
        imports=imports,
        prompt_template=prompt_template.strip() if isinstance(prompt_template, str) else str(prompt_template).strip(),
        negative_prompt=data.get('negative_prompt', '').strip(),
        generation_mode=generation.get('mode', 'combinatorial'),
        seed_mode=generation.get('seed_mode', 'progressive'),
        seed=generation.get('seed', 42),
        max_images=generation.get('max_images'),
        base_path=yaml_base_path,
        index_base=selector_config.get('index_base', 0),
        strict_mode=selector_config.get('strict_mode', True),
        allow_duplicates=selector_config.get('allow_duplicates', False),
        random_seed=selector_config.get('random_seed'),
        # SD API parameters
        width=parameters.get('width', 512),
        height=parameters.get('height', 512),
        steps=parameters.get('steps', 20),
        cfg_scale=parameters.get('cfg_scale', 7.0),
        sampler=parameters.get('sampler', 'Euler a'),
        batch_size=parameters.get('batch_size', 1),
        batch_count=parameters.get('batch_count', 1),
        # Hires Fix parameters
        enable_hr=parameters.get('enable_hr', False),
        hr_scale=parameters.get('hr_scale', 2.0),
        hr_upscaler=parameters.get('hr_upscaler', 'R-ESRGAN 4x+'),
        denoising_strength=parameters.get('denoising_strength', 0.5),
        hr_second_pass_steps=parameters.get('hr_second_pass_steps')
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
