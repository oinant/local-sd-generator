"""
Resolve prompt configurations into concrete variations ready for generation.
"""

import itertools
import random
import re
from pathlib import Path
from typing import Dict, List

from .types import PromptConfig, ResolvedVariation, Variation
from .loaders import load_variations
from .selectors import parse_selector, resolve_selectors, extract_placeholders


def resolve_prompt(config: PromptConfig, base_path: Path = None) -> List[ResolvedVariation]:
    """
    Resolve a prompt configuration into concrete variations.

    Args:
        config: The PromptConfig to resolve
        base_path: Base path for resolving relative import paths (default: current directory)

    Returns:
        List of ResolvedVariation objects ready for generation

    Raises:
        FileNotFoundError: If variation files can't be found
        ValueError: If configuration is invalid
    """
    if base_path is None:
        base_path = Path.cwd()

    # Step 1: Load all variation files
    loaded_variations: Dict[str, Dict[str, Variation]] = {}
    for placeholder_name, variation_path in config.imports.items():
        full_path = base_path / variation_path
        loaded_variations[placeholder_name] = load_variations(full_path)

    # Step 2: Extract placeholders from prompt template
    placeholders = extract_placeholders(config.prompt_template)

    # Step 3: Resolve selectors for each placeholder
    resolved_variations: Dict[str, List[Variation]] = {}
    for placeholder_name, selector_str in placeholders.items():
        if placeholder_name not in config.imports:
            raise ValueError(
                f"Placeholder {{{placeholder_name}}} used in prompt but not defined in imports"
            )

        variations_dict = loaded_variations[placeholder_name]

        if selector_str:
            # Parse and resolve selectors
            selectors = parse_selector(selector_str)
            selected = resolve_selectors(
                variations_dict,
                selectors,
                index_base=config.index_base,
                strict_mode=config.strict_mode,
                allow_duplicates=config.allow_duplicates,
                random_seed=config.random_seed
            )
        else:
            # No selector = use all
            selected = list(variations_dict.values())

        resolved_variations[placeholder_name] = selected

    # Step 4: Generate combinations
    if config.generation_mode == 'combinatorial':
        combinations = _generate_combinatorial(resolved_variations, config.max_images)
    elif config.generation_mode == 'random':
        combinations = _generate_random(resolved_variations, config.max_images or 100)
    else:
        raise ValueError(f"Unknown generation mode: {config.generation_mode}")

    # Step 5: Generate final prompts with seeds
    result = []
    for idx, combination in enumerate(combinations):
        # Determine seed
        if config.seed_mode == 'fixed':
            seed = config.seed
        elif config.seed_mode == 'progressive':
            seed = config.seed + idx
        elif config.seed_mode == 'random':
            seed = -1  # Convention for random seed
        else:
            raise ValueError(f"Unknown seed mode: {config.seed_mode}")

        # Replace placeholders in template
        final_prompt = config.prompt_template
        for placeholder_name, variation in combination.items():
            pattern = r'\{' + placeholder_name + r'(?:\[[^\]]*\])?' + r'\}'
            final_prompt = re.sub(pattern, variation.value, final_prompt)

        # Create ResolvedVariation
        result.append(ResolvedVariation(
            index=idx,
            seed=seed,
            placeholders={k: v.value for k, v in combination.items()},
            final_prompt=final_prompt,
            negative_prompt=config.negative_prompt
        ))

    return result


def _generate_combinatorial(
    variations: Dict[str, List[Variation]],
    max_images: int = None
) -> List[Dict[str, Variation]]:
    """
    Generate all combinatorial variations.

    Args:
        variations: Dict of placeholder -> list of variations
        max_images: Maximum number of images to generate (None = all)

    Returns:
        List of dicts mapping placeholder names to variations
    """
    if not variations:
        return []

    # Sort placeholders for consistent ordering
    placeholder_names = sorted(variations.keys())

    # Generate cartesian product
    variation_lists = [variations[name] for name in placeholder_names]
    combinations = list(itertools.product(*variation_lists))

    # Limit if needed
    if max_images is not None:
        combinations = combinations[:max_images]

    # Convert to dicts
    result = []
    for combo in combinations:
        result.append(dict(zip(placeholder_names, combo)))

    return result


def _generate_random(
    variations: Dict[str, List[Variation]],
    count: int
) -> List[Dict[str, Variation]]:
    """
    Generate random unique combinations.

    Args:
        variations: Dict of placeholder -> list of variations
        count: Number of combinations to generate

    Returns:
        List of dicts mapping placeholder names to variations
    """
    if not variations:
        return []

    placeholder_names = sorted(variations.keys())
    result = []
    seen = set()

    # Try to generate unique combinations
    max_attempts = count * 10  # Prevent infinite loops
    attempts = 0

    while len(result) < count and attempts < max_attempts:
        combo = {}
        for name in placeholder_names:
            combo[name] = random.choice(variations[name])

        # Create hashable key for uniqueness check
        combo_key = tuple((k, combo[k].key) for k in sorted(combo.keys()))

        if combo_key not in seen:
            seen.add(combo_key)
            result.append(combo)

        attempts += 1

    return result
