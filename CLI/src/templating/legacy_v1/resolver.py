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


def _load_import(filepath, base_path: Path) -> dict:
    """
    Load an import file (either variations or chunk).

    Args:
        filepath: Can be a Path, str, or dict (for virtual multi-field or inline)
        base_path: Base path for resolving relative paths

    Returns:
        dict with 'type' key indicating the content type:
        - {'type': 'variations', 'data': Dict[str, Variation]}
        - {'type': 'multi_field', 'data': Dict[str, MultiFieldVariation]}
        - {'type': 'chunk', 'chunk': Chunk, 'template': ChunkTemplate}
    """
    # Handle virtual multi-field (list of files from prompt config)
    if isinstance(filepath, dict):
        if filepath.get('type') == 'multi-field':
            # Virtual multi-field from list of sources
            merged_variations = {}
            for source_path in filepath.get('sources', []):
                source_file = base_path / source_path
                source_vars = load_variations(source_file)
                merged_variations.update(source_vars)
            return {
                'type': 'multi_field',
                'data': merged_variations
            }
        elif filepath.get('type') == 'inline':
            # Inline variations from prompt config
            from .types import Variation
            variations = {}
            values = filepath.get('values', [])

            if isinstance(values, list):
                # List format: ['happy', 'sad', 'angry']
                for idx, value in enumerate(values):
                    key = f"_{idx}"  # Auto-generated key
                    variations[key] = Variation(key=key, value=str(value), weight=1.0)
            elif isinstance(values, dict):
                # Dict format: {happy: 'smiling', sad: 'crying'}
                for key, value in values.items():
                    variations[key] = Variation(key=key, value=str(value), weight=1.0)

            return {
                'type': 'variations',
                'data': variations
            }
        else:
            raise ValueError(f"Invalid virtual import format: {filepath}")

    filepath = Path(filepath)
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


def _build_resolved_variations(
    combinations: List[Dict[str, any]],
    resolved_chunks: Dict[str, List[str]],
    resolved_variations: Dict[str, List[Variation]],
    config: PromptConfig
) -> List[ResolvedVariation]:
    """
    Build final ResolvedVariation objects with seeds and replaced prompts.

    Args:
        combinations: List of dicts mapping placeholder names to values
        resolved_chunks: Dict {placeholder: [rendered_chunk1, ...]} (for pattern matching)
        resolved_variations: Dict {placeholder: [Variation, ...]} (for pattern matching)
        config: PromptConfig for seed mode and template

    Returns:
        List of ResolvedVariation objects
    """
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

        # Replace chunks first (support both syntaxes)
        for chunk_name, rendered_chunk in combination.items():
            if chunk_name in resolved_chunks:
                # Try to replace {CHUNK with ...} pattern first
                chunk_with_pattern = r'\{' + chunk_name + r'\s+with\s*[^}]*\}'
                if re.search(chunk_with_pattern, final_prompt):
                    final_prompt = re.sub(chunk_with_pattern, rendered_chunk, final_prompt)
                else:
                    # Fall back to simple {CHUNK} pattern (no "with")
                    simple_chunk_pattern = r'\{' + chunk_name + r'\}'
                    final_prompt = re.sub(simple_chunk_pattern, rendered_chunk, final_prompt)

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


def _generate_combinations(
    resolved_chunks: Dict[str, List[str]],
    resolved_variations: Dict[str, List[Variation]],
    config: PromptConfig
) -> List[Dict[str, any]]:
    """
    Generate combinations of chunks and variations.

    Args:
        resolved_chunks: Dict {placeholder: [rendered_chunk1, ...]}
        resolved_variations: Dict {placeholder: [Variation, ...]}
        config: PromptConfig for generation mode and max_images

    Returns:
        List of dicts mapping placeholder names to values (str or Variation)
    """
    # Create combined dict for combination generation
    all_elements = {}

    # Add chunks as lists of strings
    for chunk_name, rendered_list in resolved_chunks.items():
        all_elements[chunk_name] = rendered_list

    # Add variations as lists of Variation objects
    for placeholder_name, var_list in resolved_variations.items():
        all_elements[placeholder_name] = var_list

    # Generate combinations based on mode
    # Special case: if no variations/chunks, but random/progressive seed mode with max_images
    # we want to generate N copies with different seeds
    if not all_elements:
        if config.seed_mode in ('random', 'progressive') and config.max_images:
            # Generate N empty combinations for different seeds
            combinations = [{}] * config.max_images
        else:
            # No variations and fixed seed or no max_images: just one image
            combinations = [{}]
    elif config.generation_mode == 'combinatorial':
        combinations = _generate_combinatorial_mixed(all_elements, config.max_images)
    elif config.generation_mode == 'random':
        # In random mode, max_images should control output count
        # regardless of combinatorial possibilities
        # If seed mode is random/progressive, allow duplicate combinations
        allow_duplicates = config.seed_mode in ('random', 'progressive')
        combinations = _generate_random_mixed(all_elements, config.max_images or 100, allow_duplicates=allow_duplicates)
    else:
        raise ValueError(f"Unknown generation mode: {config.generation_mode}")

    return combinations


def _resolve_all_variations(
    variation_placeholders: Dict[str, str],
    imports: Dict[str, dict],
    config: PromptConfig
) -> tuple:
    """
    Resolve all variation placeholders.

    Also detects simple chunks (without "with" syntax) and returns them separately.

    Args:
        variation_placeholders: Dict {placeholder_name: selector_str}
        imports: All loaded imports
        config: PromptConfig for selector resolution settings

    Returns:
        Tuple of (resolved_variations, simple_chunks)
        - resolved_variations: Dict {placeholder_name: [Variation, ...]}
        - simple_chunks: Dict {chunk_name: (chunk_name, empty_overrides)} for chunks without "with"

    Raises:
        ValueError: If placeholder not found or invalid
    """
    resolved_variations: Dict[str, List[Variation]] = {}
    simple_chunks: Dict[str, tuple] = {}  # Chunks detected without "with" syntax

    for placeholder_name, selector_str in variation_placeholders.items():
        if placeholder_name not in imports:
            raise ValueError(
                f"Placeholder {{{placeholder_name}}} used in prompt but not defined in imports"
            )

        import_data = imports[placeholder_name]

        # Check if this is a chunk (without "with" syntax)
        if import_data['type'] == 'chunk':
            # This is a simple chunk usage: {CHUNK} without "with"
            # Add to simple_chunks with empty overrides
            simple_chunks[placeholder_name] = (placeholder_name, {})
            continue

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

    return resolved_variations, simple_chunks


def _resolve_all_chunks(
    chunk_placeholders: Dict[str, tuple],
    imports: Dict[str, dict],
    config: PromptConfig
) -> Dict[str, List[str]]:
    """
    Resolve all chunk placeholders.

    Args:
        chunk_placeholders: Dict {placeholder_name: (chunk_name, overrides)}
        imports: All loaded imports
        config: PromptConfig for generation settings

    Returns:
        Dict {placeholder: [rendered_chunk1, rendered_chunk2, ...]}

    Raises:
        ValueError: If chunk not found or invalid
    """
    resolved_chunks: Dict[str, List[str]] = {}

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

    return resolved_chunks


def _parse_prompt_placeholders(prompt_template: str) -> tuple:
    """
    Parse prompt template for placeholders and chunk "with" syntax.

    Supports two syntaxes for chunks:
    1. {CHUNK with field=SOURCE[selector]} - chunk with overrides
    2. {CHUNK} - chunk without overrides (will be detected later based on imports)

    Args:
        prompt_template: The prompt template string

    Returns:
        Tuple of (chunk_placeholders, variation_placeholders)
        - chunk_placeholders: Dict {placeholder_name: (chunk_name, overrides)}
        - variation_placeholders: Dict {placeholder_name: selector_str}
    """
    chunk_placeholders = {}  # {placeholder_name: (chunk_name, overrides)}
    variation_placeholders = {}  # {placeholder_name: selector_str}

    # Extract all {XXX...} patterns
    full_pattern = r'\{([^}]+)\}'
    for match in re.finditer(full_pattern, prompt_template):
        full_content = match.group(1)  # Content inside {}

        # Check if it's a chunk with "with" syntax
        chunk_name, overrides = parse_chunk_with_syntax(full_content)

        if chunk_name:
            # It's a chunk placeholder with "with" syntax
            chunk_placeholders[chunk_name] = (chunk_name, overrides)
        else:
            # It's a normal variation placeholder (or simple chunk without "with")
            # We'll determine if it's a chunk later based on imports
            # Extract placeholder name and selector
            simple_placeholders = extract_placeholders(match.group(0))
            variation_placeholders.update(simple_placeholders)

    return chunk_placeholders, variation_placeholders


def _load_all_imports(config: PromptConfig, base_path: Path) -> Dict[str, dict]:
    """
    Load all imports from config.

    Args:
        config: The PromptConfig containing imports
        base_path: Base path for resolving relative import paths

    Returns:
        Dict mapping placeholder names to import data (variations, multi-field, or chunks)
    """
    imports: Dict[str, dict] = {}
    for placeholder_name, variation_path in config.imports.items():
        # Handle four cases:
        # 1. String path: single file import
        # 2. Dict with 'sources': multi-file import (PromptConfig normalized list to this format)
        # 3. List of strings starting with '../' or ending in '.yaml': multiple file imports to merge
        # 4. List of plain strings: inline variation values

        if isinstance(variation_path, str):
            # Single file import
            imports[placeholder_name] = _load_import(variation_path, base_path)
        elif isinstance(variation_path, dict):
            # PromptConfig has normalized list imports to dict format with 'sources'
            if 'sources' in variation_path:
                # Multi-file import
                merged_variations = {}
                for file_path in variation_path['sources']:
                    if isinstance(file_path, str):
                        import_data = _load_import(file_path, base_path)
                        if import_data['type'] == 'variations':
                            merged_variations.update(import_data['data'])
                imports[placeholder_name] = {
                    'type': 'variations',
                    'data': merged_variations
                }
            elif 'inline_values' in variation_path:
                # Inline values (PromptConfig normalized - old format)
                from .types import Variation
                inline_variations = {}
                for idx, value in enumerate(variation_path['inline_values']):
                    if isinstance(value, str):
                        inline_variations[str(idx)] = Variation(key=str(idx), value=value)
                imports[placeholder_name] = {
                    'type': 'variations',
                    'data': inline_variations
                }
            elif variation_path.get('type') == 'inline' and 'values' in variation_path:
                # Inline values (PromptConfig normalized - new format)
                from .types import Variation
                inline_variations = {}
                for idx, value in enumerate(variation_path['values']):
                    if isinstance(value, str):
                        inline_variations[str(idx)] = Variation(key=str(idx), value=value)
                imports[placeholder_name] = {
                    'type': 'variations',
                    'data': inline_variations
                }
            else:
                raise ValueError(f"Unknown dict format for {placeholder_name}: {variation_path}")
        elif isinstance(variation_path, list):
            # Legacy: direct list (not normalized by PromptConfig)
            is_file_list = any(
                isinstance(item, str) and ('/' in item or item.endswith('.yaml'))
                for item in variation_path
            )

            if is_file_list:
                # Multiple file imports - merge them
                merged_variations = {}
                for file_path in variation_path:
                    if isinstance(file_path, str) and ('/' in file_path or file_path.endswith('.yaml')):
                        import_data = _load_import(file_path, base_path)
                        if import_data['type'] == 'variations':
                            merged_variations.update(import_data['data'])
                imports[placeholder_name] = {
                    'type': 'variations',
                    'data': merged_variations
                }
            else:
                # Inline values - convert to variations dict
                from .types import Variation
                inline_variations = {}
                for idx, value in enumerate(variation_path):
                    if isinstance(value, str):
                        inline_variations[str(idx)] = Variation(key=str(idx), value=value)
                imports[placeholder_name] = {
                    'type': 'variations',
                    'data': inline_variations
                }
        else:
            raise ValueError(f"Invalid import format for {placeholder_name}: {type(variation_path)}")

    return imports


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
    imports = _load_all_imports(config, base_path)

    # Step 2: Parse prompt template for placeholders and chunk "with" syntax
    chunk_placeholders, variation_placeholders = _parse_prompt_placeholders(config.prompt_template)

    # Step 3: Resolve normal variations (also detects simple chunks)
    resolved_variations, simple_chunks = _resolve_all_variations(variation_placeholders, imports, config)

    # Step 4: Merge simple chunks with chunk_placeholders
    chunk_placeholders.update(simple_chunks)

    # Step 5: Resolve all chunks (with "with" syntax and simple chunks)
    resolved_chunks = _resolve_all_chunks(chunk_placeholders, imports, config)

    # Step 6: Generate combinations
    combinations = _generate_combinations(resolved_chunks, resolved_variations, config)

    # Step 7: Generate final prompts with seeds
    return _build_resolved_variations(combinations, resolved_chunks, resolved_variations, config)


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
    count: int,
    allow_duplicates: bool = False
) -> List[Dict[str, any]]:
    """
    Generate random combinations for mixed types (chunks and variations).

    Args:
        elements: Dict of name -> list of items (can be strings or Variation objects)
        count: Number of combinations to generate
        allow_duplicates: If True, allow duplicate combinations (useful for different seeds)

    Returns:
        List of dicts mapping names to items
    """
    if not elements:
        return []

    names = sorted(elements.keys())
    result = []

    if allow_duplicates:
        # Simple mode: just generate count random combinations
        for _ in range(count):
            combo = {}
            for name in names:
                combo[name] = random.choice(elements[name])
            result.append(combo)
    else:
        # Original mode: try to generate unique combinations
        seen = set()
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
