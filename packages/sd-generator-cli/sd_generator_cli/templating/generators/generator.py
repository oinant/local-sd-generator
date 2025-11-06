"""
Prompt generator for Template System V2.0 - Phase 6.

This module implements combinatorial and random prompt generation
with support for weight-based loop ordering and selector application.
"""

import random
import itertools
from typing import Dict, List, Any, Tuple, Optional

from sd_generator_cli.templating.models.config_models import (
    GenerationConfig,
    ResolvedContext
)
from sd_generator_cli.templating.resolvers.template_resolver import TemplateResolver
from sd_generator_cli.templating.normalizers.normalizer import PromptNormalizer


class PromptGenerator:
    """
    Generates prompts from templates with variations.

    Supports two generation modes:
    - combinatorial: Nested loops with weight-based ordering
    - random: Random combinations with unique selection

    Weight system ($W):
    - Lower weight = outer loop (changes less often)
    - Higher weight = inner loop (changes more often)
    - Weight 0 = excluded from combinatorial (random per image)

    Example:
        {Outfit[$2]}, {Angle[$10]}, {Quality[$0]}
        → Outfit loop (outer), Angle loop (inner), Quality random
    """

    def __init__(self, resolver: Optional[TemplateResolver] = None, normalizer: Optional[PromptNormalizer] = None):
        """
        Initialize the prompt generator.

        Args:
            resolver: TemplateResolver instance (for template resolution)
            normalizer: PromptNormalizer instance (for final normalization)
        """
        self.resolver = resolver or TemplateResolver()
        self.normalizer = normalizer or PromptNormalizer()

    def generate_prompts(
        self,
        template: str,
        context: ResolvedContext,
        generation: GenerationConfig
    ) -> List[Dict[str, Any]]:
        """
        Generate prompts according to generation mode.

        Args:
            template: Template string with placeholders
            context: Resolved context with imports and chunks
            generation: Generation configuration (mode, seed, max_images)

        Returns:
            List of prompt dicts with format:
            {
                'prompt': str,  # Normalized positive prompt
                'negative_prompt': str,  # Normalized negative prompt
                'seed': int,  # Seed for this image
                'variations': Dict[str, str]  # Variation values used
            }
        """
        # Extract variations from imports
        variations_dict = self._extract_variations(template, context)

        if not variations_dict:
            # No variations - single prompt
            return self._generate_single_prompt(template, context, generation)

        # Apply selectors to get selected variations
        selected_variations = self._apply_selectors(template, variations_dict, context)

        if generation.mode == 'combinatorial':
            return self._generate_combinatorial(
                template,
                selected_variations,
                context,
                generation
            )
        else:  # random
            return self._generate_random(
                template,
                selected_variations,
                context,
                generation
            )

    def _extract_variations(
        self,
        template: str,
        context: ResolvedContext
    ) -> Dict[str, Dict[str, str]]:
        """
        Extract variation dicts from context imports.

        Args:
            template: Template string
            context: Resolved context

        Returns:
            Dict mapping placeholder names to variation dicts

        Raises:
            ValueError: If placeholders in template have no corresponding variations
        """
        import re

        # Find all placeholders in template
        placeholder_pattern = re.compile(r'\{(\w+)(?:\[[^\]]+\])?\}')
        placeholder_names = set(placeholder_pattern.findall(template))

        # Track unresolved placeholders
        unresolved = []

        variations = {}
        for name in placeholder_names:
            # Check if this placeholder has variations in imports
            if name in context.imports:
                import_data = context.imports[name]
                if isinstance(import_data, dict):
                    variations[name] = import_data
                else:
                    # Placeholder exists but is not a variation dict
                    unresolved.append(name)
            else:
                # Placeholder not found in imports
                # Check if it was explicitly removed via [Remove] directive
                if name not in context.removed_placeholders:
                    unresolved.append(name)
                # If it was removed, skip it (will resolve to empty string later)

        # Raise error if any placeholders are unresolved
        if unresolved:
            # Build detailed diagnostic for each unresolved placeholder
            diagnostic_lines = []
            diagnostic_lines.append(f"✗ Unresolved placeholders detected: {', '.join(sorted(unresolved))}")
            diagnostic_lines.append("")
            diagnostic_lines.append("Diagnostics:")

            for placeholder in sorted(unresolved):
                diagnostic_lines.append(f"  • {placeholder}:")
                diagnostic_lines.append(f"      → NOT found in loaded imports")
                diagnostic_lines.append(f"      → This placeholder needs to be defined in:")
                if context.theme_name:
                    diagnostic_lines.append(f"         - Theme '{context.theme_name}' imports section (theme.yaml)")
                diagnostic_lines.append(f"         - Template imports section (template.yaml)")
                diagnostic_lines.append(f"         - Prompt imports section (prompt.yaml)")

            diagnostic_lines.append("")
            diagnostic_lines.append(f"Available loaded imports ({len(context.imports)}):")
            diagnostic_lines.append(f"  {', '.join(sorted(context.imports.keys()))}")
            diagnostic_lines.append("")
            diagnostic_lines.append("💡 Tip: Check the debug messages above for [ERROR] or missing [LOAD] messages")

            raise ValueError('\n'.join(diagnostic_lines))

        return variations

    def _apply_selectors(
        self,
        template: str,
        variations_dict: Dict[str, Dict[str, str]],
        context: ResolvedContext
    ) -> Dict[str, List[str]]:
        """
        Apply selectors to get selected variation values.

        Args:
            template: Template string with selectors
            variations_dict: Dict of all variations
            context: Resolved context

        Returns:
            Dict mapping placeholder names to lists of selected values
        """
        import re

        selected = {}

        # Parse template to extract selectors
        placeholder_pattern = re.compile(r'\{(\w+)(?:\[([^\]]+)\])?\}')

        for match in placeholder_pattern.finditer(template):
            name = match.group(1)
            selector_str = match.group(2)

            if name not in variations_dict:
                continue

            variation_dict = variations_dict[name]

            if selector_str:
                # Parse and apply selector
                selector = self.resolver._parse_selectors(selector_str)
                selected_values = self.resolver._apply_selector(
                    variation_dict,
                    selector,
                    {'imports': context.imports}
                )
                selected[name] = selected_values
            else:
                # No selector - use all variations
                selected[name] = list(variation_dict.values())

        return selected

    def _generate_single_prompt(
        self,
        template: str,
        context: ResolvedContext,
        generation: GenerationConfig
    ) -> List[Dict[str, Any]]:
        """
        Generate a single prompt (no variations).

        Args:
            template: Template string
            context: Resolved context
            generation: Generation config

        Returns:
            List with single prompt dict
        """
        # Resolve template (skip chunk injection - already done in Phase 1)
        resolved = self.resolver.resolve_template(
            template,
            {
                'imports': context.imports,
                'chunks': context.chunks,
                'defaults': {}
            },
            skip_chunk_injection=True
        )

        # Normalize
        normalized = self.normalizer.normalize_prompt(resolved)

        return [{
            'prompt': normalized,
            'negative_prompt': '',
            'seed': generation.seed,
            'variations': {}
        }]

    def _generate_combinatorial(
        self,
        template: str,
        selected_variations: Dict[str, List[str]],
        context: ResolvedContext,
        generation: GenerationConfig
    ) -> List[Dict[str, Any]]:
        """
        Generate prompts using combinatorial mode (nested loops).

        Weight-based ordering:
        - Extract weights from template ($W syntax)
        - Sort placeholders by weight (lower = outer loop)
        - Weight 0 = excluded from loops (random per iteration)

        Args:
            template: Template string
            selected_variations: Selected variation values
            context: Resolved context
            generation: Generation config

        Returns:
            List of prompt dicts
        """
        # Extract weights
        weights = self.resolver.extract_weights(template)

        # Separate combinatorial ($W > 0) and non-combinatorial ($W == 0)
        combinatorial_vars = []
        non_combinatorial_vars = []

        for name, variations in selected_variations.items():
            weight = weights.get(name, 1)  # Default weight = 1
            if weight > 0:
                combinatorial_vars.append((name, variations, weight))
            else:
                non_combinatorial_vars.append((name, variations))

        # Sort combinatorial vars by weight (ascending = outer to inner)
        combinatorial_vars.sort(key=lambda x: x[2])

        # Generate all combinations of combinatorial vars
        if combinatorial_vars:
            names = [name for name, _, _ in combinatorial_vars]
            variation_lists = [variations for _, variations, _ in combinatorial_vars]
            combinations = list(itertools.product(*variation_lists))
        else:
            combinations = [()]

        # Generate prompts
        prompts = []

        # Seed-sweep mode: iterate combinations × seeds
        if generation.seed_list:
            image_index = 0
            for combo in combinations:
                # Build variation state for this combination
                variation_state = {}
                for name_idx, name in enumerate(names) if combinatorial_vars else []:
                    variation_state[name] = combo[name_idx]

                # Add random values for non-combinatorial vars (weight 0)
                for name, variations in non_combinatorial_vars:
                    variation_state[name] = random.choice(variations)

                # Test this variation on all seeds in the list
                for seed in generation.seed_list:
                    if generation.max_images > 0 and image_index >= generation.max_images:
                        return prompts

                    # Build context
                    prompt_context = {
                        'imports': context.imports,
                        'chunks': {**context.chunks, **variation_state},
                        'defaults': {}
                    }

                    # Resolve template
                    resolved = self.resolver.resolve_template(template, prompt_context, skip_chunk_injection=True)

                    # Normalize
                    normalized = self.normalizer.normalize_prompt(resolved)

                    prompts.append({
                        'prompt': normalized,
                        'negative_prompt': '',
                        'seed': seed,
                        'variations': variation_state.copy()
                    })

                    image_index += 1

        # Normal mode: iterate combinations once
        else:
            for idx, combo in enumerate(combinations):
                if generation.max_images > 0 and idx >= generation.max_images:
                    break

                # Build variation state for this combination
                variation_state = {}
                for name_idx, name in enumerate(names) if combinatorial_vars else []:
                    variation_state[name] = combo[name_idx]

                # Add random values for non-combinatorial vars (weight 0)
                for name, variations in non_combinatorial_vars:
                    variation_state[name] = random.choice(variations)

                # Build context with variation_state
                prompt_context = {
                    'imports': context.imports,
                    'chunks': {**context.chunks, **variation_state},
                    'defaults': {}
                }

                # Resolve template (skip chunk injection - already done in Phase 1)
                resolved = self.resolver.resolve_template(template, prompt_context, skip_chunk_injection=True)

                # Normalize
                normalized = self.normalizer.normalize_prompt(resolved)

                # Calculate seed
                seed = self._calculate_seed(generation, idx)

                prompts.append({
                    'prompt': normalized,
                    'negative_prompt': '',
                    'seed': seed,
                    'variations': variation_state.copy()
                })

        return prompts

    def _generate_random(
        self,
        template: str,
        selected_variations: Dict[str, List[str]],
        context: ResolvedContext,
        generation: GenerationConfig
    ) -> List[Dict[str, Any]]:
        """
        Generate prompts using random mode.

        Selects random values from each variation, ensuring uniqueness.

        When seed_list is provided, each unique variation combination
        is tested on all seeds in the list.

        Args:
            template: Template string
            selected_variations: Selected variation values
            context: Resolved context
            generation: Generation config

        Returns:
            List of prompt dicts
        """
        prompts: List[Dict[str, Any]] = []
        used_combinations: set[tuple[tuple[str, str], ...]] = set()

        # Seed-sweep mode: pick random combinations, test on all seeds
        if generation.seed_list:
            # Calculate how many unique combinations we need
            num_combinations_needed = generation.max_images // len(generation.seed_list)
            if generation.max_images % len(generation.seed_list) > 0:
                num_combinations_needed += 1

            # Limit attempts to avoid infinite loop
            max_attempts = num_combinations_needed * 10

            for attempt in range(max_attempts):
                if len(used_combinations) >= num_combinations_needed:
                    break

                # Generate random combination
                variation_state = {}
                for name, variations in selected_variations.items():
                    variation_state[name] = random.choice(variations)

                # Check uniqueness
                combo_key = tuple(sorted(variation_state.items()))
                if combo_key in used_combinations:
                    continue

                used_combinations.add(combo_key)

                # Test this combination on all seeds
                for seed in generation.seed_list:
                    if generation.max_images > 0 and len(prompts) >= generation.max_images:
                        return prompts

                    # Build context
                    prompt_context = {
                        'imports': context.imports,
                        'chunks': {**context.chunks, **variation_state},
                        'defaults': {}
                    }

                    # Resolve template
                    resolved = self.resolver.resolve_template(template, prompt_context, skip_chunk_injection=True)

                    # Normalize
                    normalized = self.normalizer.normalize_prompt(resolved)

                    prompts.append({
                        'prompt': normalized,
                        'negative_prompt': '',
                        'seed': seed,
                        'variations': variation_state.copy()
                    })

        # Normal mode: pick random combinations with calculated seeds
        else:
            # Limit attempts to avoid infinite loop
            max_attempts = generation.max_images * 10

            for attempt in range(max_attempts):
                if len(prompts) >= generation.max_images:
                    break

                # Generate random combination (truly random - not seeded)
                # The seed parameter only affects SD image generation, not variation selection
                variation_state = {}
                for name, variations in selected_variations.items():
                    variation_state[name] = random.choice(variations)

                # Check uniqueness
                combo_key = tuple(sorted(variation_state.items()))
                if combo_key in used_combinations:
                    continue

                used_combinations.add(combo_key)

                # Build context
                prompt_context = {
                    'imports': context.imports,
                    'chunks': {**context.chunks, **variation_state},
                    'defaults': {}
                }

                # Resolve template (skip chunk injection - already done in Phase 1)
                resolved = self.resolver.resolve_template(template, prompt_context, skip_chunk_injection=True)

                # Normalize
                normalized = self.normalizer.normalize_prompt(resolved)

                # Calculate seed
                seed = self._calculate_seed(generation, len(prompts))

                prompts.append({
                    'prompt': normalized,
                    'negative_prompt': '',
                    'seed': seed,
                    'variations': variation_state.copy()
                })

        return prompts

    def _calculate_seed(self, generation: GenerationConfig, index: int) -> int:
        """
        Calculate seed for a specific image index.

        Args:
            generation: Generation config
            index: Image index (0-based)

        Returns:
            Seed value

        Seed modes:
        - fixed: Same seed for all images
        - progressive: SEED + index
        - random: -1 (random)
        """
        if generation.seed_mode == 'fixed':
            return generation.seed
        elif generation.seed_mode == 'progressive':
            return generation.seed + index
        else:  # random
            return -1
