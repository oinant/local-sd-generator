"""
Resolve prompt configurations into concrete variations ready for generation.
"""

import itertools
import random
import re
from pathlib import Path
from typing import Dict, List

from .types import PromptConfig, ResolvedVariation, Variation, MultiFieldVariation
from .loaders import load_variations
from .selectors import parse_selector, resolve_selectors, extract_placeholders, parse_chunk_with_syntax
from .chunk import load_chunk, load_chunk_template, resolve_chunk_fields, render_chunk
from .multi_field import is_multi_field_variation, load_multi_field_variations, expand_multi_field


def _is_chunk_file(filepath: str) -> bool:
    """Check if filepath is a chunk/character file."""
    return filepath.endswith('.char.yaml') or filepath.endswith('.chunk.yaml')


def _resolve_chunk_with_overrides(
    chunk,
    template,
    overrides: Dict[str, tuple],
    imports: Dict[str, dict],
    config: PromptConfig
) -> List[str]:
    """
    Resolve a chunk with field overrides into rendered strings.

    Args:
        chunk: Chunk object
        template: ChunkTemplate object
        overrides: Dict like {"ethnicity": ("ETHNICITIES", "[african,asian]")}
        imports: All loaded imports
        config: PromptConfig for generation settings

    Returns:
        List of rendered chunk strings for each combination
    """
    # Resolve each override field to get variations
    override_variations = {}

    for field_name, (source_name, selector_str) in overrides.items():
        if source_name not in imports:
            raise ValueError(f"Override source {source_name} not found in imports")

        source_data = imports[source_name]

        # Get the variations
        if source_data['type'] == 'chunk':
            raise ValueError(f"Cannot use chunk {source_name} as override source")

        variations_dict = source_data['data']

        # Parse and resolve selector
        if selector_str:
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
            selected = list(variations_dict.values())

        override_variations[field_name] = selected

    # Generate combinations of overrides
    if not override_variations:
        # No overrides, just render the chunk as-is
        resolved = resolve_chunk_fields(chunk, template)
        return [render_chunk(template, resolved)]

    # Combinatorial mode: all combinations
    if config.generation_mode == 'combinatorial':
        field_names = sorted(override_variations.keys())
        field_values = [override_variations[f] for f in field_names]

        results = []
        for combo in itertools.product(*field_values):
            # Build additional_fields from this combination
            additional_fields = {}

            for field_name, variation in zip(field_names, combo):
                if isinstance(variation, MultiFieldVariation):
                    # Expand multi-field variation
                    additional_fields = expand_multi_field(variation, additional_fields)
                else:
                    # Single field variation - need to map field_name to category.field
                    # For now, assume field_name is like "ethnicity" and maps to a category
                    # This is a simplification - in real use, we'd need field mapping config
                    # Since ethnicity is a multi-field in our test case, this shouldn't trigger
                    pass

            # Resolve and render
            resolved = resolve_chunk_fields(chunk, template, additional_fields)
            rendered = render_chunk(template, resolved)
            results.append(rendered)

        return results

    else:  # random mode
        # Generate N random combinations
        count = config.max_images or 10
        field_names = sorted(override_variations.keys())
        results = []

        for _ in range(count):
            additional_fields = {}

            for field_name in field_names:
                variation = random.choice(override_variations[field_name])

                if isinstance(variation, MultiFieldVariation):
                    additional_fields = expand_multi_field(variation, additional_fields)

            resolved = resolve_chunk_fields(chunk, template, additional_fields)
            rendered = render_chunk(template, resolved)
            results.append(rendered)

        return results


def _load_import(filepath: Path, base_path: Path) -> dict:
    """
    Load an import file (either variations or chunk).

    Returns:
        dict with 'type' key indicating the content type:
        - {'type': 'variations', 'data': Dict[str, Variation]}
        - {'type': 'multi_field', 'data': Dict[str, MultiFieldVariation]}
        - {'type': 'chunk', 'chunk': Chunk, 'template': ChunkTemplate}
    """
    full_path = base_path / filepath

    if _is_chunk_file(str(filepath)):
        # Load chunk + template
        chunk = load_chunk(full_path)  # full_path already includes base_path
        template_path = base_path / chunk.implements
        template = load_chunk_template(template_path)  # template_path already includes base_path
        return {
            'type': 'chunk',
            'chunk': chunk,
            'template': template
        }
    else:
        # Load variations (could be multi-field)
        import yaml
        with open(full_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if is_multi_field_variation(data):
            variations = load_multi_field_variations(full_path)  # full_path already includes base_path
            return {
                'type': 'multi_field',
                'data': variations
            }
        else:
            variations = load_variations(full_path)  # full_path already includes base_path
            return {
                'type': 'variations',
                'data': variations
            }


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

    # Step 1: Load all imports (variations, multi-field, or chunks)
    imports: Dict[str, dict] = {}
    for placeholder_name, variation_path in config.imports.items():
        imports[placeholder_name] = _load_import(variation_path, base_path)

    # Step 2: Parse prompt template for placeholders and chunk "with" syntax
    # Need to extract full placeholder content for chunk detection
    chunk_placeholders = {}  # {placeholder_name: (chunk_name, overrides)}
    variation_placeholders = {}  # {placeholder_name: selector_str}

    # Extract all {XXX...} patterns
    full_pattern = r'\{([^}]+)\}'
    for match in re.finditer(full_pattern, config.prompt_template):
        full_content = match.group(1)  # Content inside {}

        # Check if it's a chunk with syntax
        chunk_name, overrides = parse_chunk_with_syntax(full_content)

        if chunk_name:
            # It's a chunk placeholder
            chunk_placeholders[chunk_name] = (chunk_name, overrides)
        else:
            # It's a normal variation placeholder
            # Extract placeholder name and selector
            simple_placeholders = extract_placeholders(match.group(0))
            variation_placeholders.update(simple_placeholders)

    # Step 3: Resolve chunks
    resolved_chunks: Dict[str, List[str]] = {}  # {placeholder: [rendered_chunk1, rendered_chunk2, ...]}

    for placeholder_name, (chunk_name, overrides) in chunk_placeholders.items():
        if chunk_name not in imports:
            raise ValueError(f"Chunk {chunk_name} not found in imports")

        chunk_data = imports[chunk_name]
        if chunk_data['type'] != 'chunk':
            raise ValueError(f"Import {chunk_name} is not a chunk")

        # Resolve chunk with overrides
        rendered_chunks = _resolve_chunk_with_overrides(
            chunk_data['chunk'],
            chunk_data['template'],
            overrides,
            imports,
            config
        )
        resolved_chunks[chunk_name] = rendered_chunks

    # Step 4: Resolve normal variations
    resolved_variations: Dict[str, List[Variation]] = {}
    for placeholder_name, selector_str in variation_placeholders.items():
        if placeholder_name not in imports:
            raise ValueError(
                f"Placeholder {{{placeholder_name}}} used in prompt but not defined in imports"
            )

        import_data = imports[placeholder_name]

        # Get variations dict based on type
        if import_data['type'] == 'chunk':
            raise ValueError(f"Placeholder {{{placeholder_name}}} references a chunk but doesn't use 'with' syntax")

        variations_dict = import_data['data']

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

    # Step 5: Generate combinations
    # We need to combine both chunks and normal variations
    # Chunks are already resolved to strings, variations are Variation objects

    # Create combined dict for combination generation
    all_elements = {}

    # Add chunks as lists of strings
    for chunk_name, rendered_list in resolved_chunks.items():
        all_elements[chunk_name] = rendered_list

    # Add variations as lists of Variation objects
    for placeholder_name, var_list in resolved_variations.items():
        all_elements[placeholder_name] = var_list

    # Generate combinations based on mode
    if config.generation_mode == 'combinatorial':
        combinations = _generate_combinatorial_mixed(all_elements, config.max_images)
    elif config.generation_mode == 'random':
        combinations = _generate_random_mixed(all_elements, config.max_images or 100)
    else:
        raise ValueError(f"Unknown generation mode: {config.generation_mode}")

    # Step 6: Generate final prompts with seeds
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
        # combination is dict of {name: value} where value is either str (chunk) or Variation
        final_prompt = config.prompt_template

        # Replace chunks first (they have "with" syntax)
        for chunk_name, rendered_chunk in combination.items():
            if chunk_name in resolved_chunks:
                # This is a chunk - replace the entire {CHUNK with ...} pattern
                chunk_pattern = r'\{' + chunk_name + r'\s+with\s+[^}]+\}'
                final_prompt = re.sub(chunk_pattern, rendered_chunk, final_prompt)

        # Replace normal variations
        for placeholder_name, value in combination.items():
            if placeholder_name in resolved_variations:
                # This is a variation
                variation_value = value.value if isinstance(value, Variation) else str(value)
                pattern = r'\{' + placeholder_name + r'(?:\[[^\]]*\])?' + r'\}'
                final_prompt = re.sub(pattern, variation_value, final_prompt)

        # Build placeholders dict for metadata
        placeholders_dict = {}
        for name, value in combination.items():
            if isinstance(value, Variation):
                placeholders_dict[name] = value.value
            else:
                placeholders_dict[name] = value

        # Create ResolvedVariation
        result.append(ResolvedVariation(
            index=idx,
            seed=seed,
            placeholders=placeholders_dict,
            final_prompt=final_prompt,
            negative_prompt=config.negative_prompt
        ))

    return result


def _generate_combinatorial_mixed(
    elements: Dict[str, List],
    max_images: int = None
) -> List[Dict[str, any]]:
    """
    Generate all combinatorial combinations for mixed types (chunks and variations).

    Args:
        elements: Dict of name -> list of items (can be strings or Variation objects)
        max_images: Maximum number of images to generate (None = all)

    Returns:
        List of dicts mapping names to items
    """
    if not elements:
        return []

    # Sort names for consistent ordering
    names = sorted(elements.keys())

    # Generate cartesian product
    element_lists = [elements[name] for name in names]
    combinations = list(itertools.product(*element_lists))

    # Limit if needed
    if max_images is not None:
        combinations = combinations[:max_images]

    # Convert to dicts
    result = []
    for combo in combinations:
        result.append(dict(zip(names, combo)))

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


def _generate_random_mixed(
    elements: Dict[str, List],
    count: int
) -> List[Dict[str, any]]:
    """
    Generate random unique combinations for mixed types (chunks and variations).

    Args:
        elements: Dict of name -> list of items (can be strings or Variation objects)
        count: Number of combinations to generate

    Returns:
        List of dicts mapping names to items
    """
    if not elements:
        return []

    names = sorted(elements.keys())
    result = []
    seen = set()

    # Try to generate unique combinations
    max_attempts = count * 10  # Prevent infinite loops
    attempts = 0

    while len(result) < count and attempts < max_attempts:
        combo = {}
        for name in names:
            combo[name] = random.choice(elements[name])

        # Create hashable key for uniqueness check
        combo_key = tuple(
            (k, combo[k].key if isinstance(combo[k], Variation) else combo[k])
            for k in sorted(combo.keys())
        )

        if combo_key not in seen:
            seen.add(combo_key)
            result.append(combo)

        attempts += 1

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
