"""
Tests for PromptGenerator - Phase 6.

Tests combinatorial and random generation modes with:
- Weight-based loop ordering
- Seed management (fixed/progressive/random)
- Selector application
- Integration with normalizer
"""

import pytest
from pathlib import Path
from templating.generators.generator import PromptGenerator
from templating.models.config_models import GenerationConfig, ResolvedContext
from templating.resolvers.template_resolver import TemplateResolver
from templating.normalizers.normalizer import PromptNormalizer


class TestPromptGenerator:
    """Test suite for PromptGenerator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = TemplateResolver()
        self.normalizer = PromptNormalizer()
        self.generator = PromptGenerator(self.resolver, self.normalizer)

    # ===== Combinatorial Mode Tests =====

    def test_combinatorial_basic(self):
        """Test basic combinatorial generation."""
        template = "{Color}, {Size}"
        context = ResolvedContext(
            imports={
                'Color': {'red': 'red', 'blue': 'blue'},
                'Size': {'small': 'small', 'large': 'large'}
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=42,
            seed_mode='fixed',
            max_images=10
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should generate 2×2 = 4 combinations
        assert len(results) == 4

        # Check all combinations exist
        combos = [(r['variations']['Color'], r['variations']['Size']) for r in results]
        assert ('red', 'small') in combos
        assert ('red', 'large') in combos
        assert ('blue', 'small') in combos
        assert ('blue', 'large') in combos

        # Check prompts are normalized
        assert results[0]['prompt'] == 'red, small'

    def test_combinatorial_weight_ordering(self):
        """Test weight-based loop ordering (lower weight = outer loop)."""
        template = "{Outfit[$2]}, {Angle[$10]}"
        context = ResolvedContext(
            imports={
                'Outfit': {'casual': 'casual', 'formal': 'formal'},
                'Angle': {'front': 'front', 'side': 'side'}
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=42,
            seed_mode='progressive',
            max_images=10
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should generate 2×2 = 4 combinations
        assert len(results) == 4

        # Check ordering: Outfit (weight 2) outer, Angle (weight 10) inner
        # Order should be: casual+front, casual+side, formal+front, formal+side
        assert results[0]['variations'] == {'Outfit': 'casual', 'Angle': 'front'}
        assert results[1]['variations'] == {'Outfit': 'casual', 'Angle': 'side'}
        assert results[2]['variations'] == {'Outfit': 'formal', 'Angle': 'front'}
        assert results[3]['variations'] == {'Outfit': 'formal', 'Angle': 'side'}

    def test_combinatorial_three_weights(self):
        """Test ordering with three different weights."""
        template = "{A[$1]}, {B[$5]}, {C[$10]}"
        context = ResolvedContext(
            imports={
                'A': {'a1': 'a1', 'a2': 'a2'},
                'B': {'b1': 'b1', 'b2': 'b2'},
                'C': {'c1': 'c1', 'c2': 'c2'}
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=1,
            seed_mode='fixed',
            max_images=20
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should generate 2×2×2 = 8 combinations
        assert len(results) == 8

        # Check ordering: A (weight 1) outer, B (weight 5) middle, C (weight 10) inner
        # First 4 should all have A=a1
        for i in range(4):
            assert results[i]['variations']['A'] == 'a1'
        # Last 4 should all have A=a2
        for i in range(4, 8):
            assert results[i]['variations']['A'] == 'a2'

        # Within each A group, B should change every 2 iterations
        assert results[0]['variations']['B'] == results[1]['variations']['B']
        assert results[2]['variations']['B'] == results[3]['variations']['B']

        # C should change every iteration (innermost)
        assert results[0]['variations']['C'] != results[1]['variations']['C']

    def test_combinatorial_weight_zero_excluded(self):
        """Test that weight $0 excludes variable from combinatorial."""
        template = "{Color[$2]}, {Quality[$0]}"
        context = ResolvedContext(
            imports={
                'Color': {'red': 'red', 'blue': 'blue'},
                'Quality': {'high': 'high', 'low': 'low'}
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=42,
            seed_mode='fixed',
            max_images=10
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should generate only 2 combinations (for Color only)
        # Quality is random each time
        assert len(results) == 2

        # Color should be deterministic
        colors = [r['variations']['Color'] for r in results]
        assert 'red' in colors
        assert 'blue' in colors

        # Quality should exist (random selection)
        for r in results:
            assert 'Quality' in r['variations']
            assert r['variations']['Quality'] in ['high', 'low']

    def test_combinatorial_max_images_limit(self):
        """Test max_images limit in combinatorial mode."""
        template = "{A}, {B}, {C}"
        context = ResolvedContext(
            imports={
                'A': {str(i): str(i) for i in range(5)},  # 5 values
                'B': {str(i): str(i) for i in range(5)},  # 5 values
                'C': {str(i): str(i) for i in range(5)}   # 5 values
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=1,
            seed_mode='fixed',
            max_images=10  # Limit to 10 (total would be 5×5×5 = 125)
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should stop at max_images
        assert len(results) == 10

    # ===== Random Mode Tests =====

    def test_random_basic(self):
        """Test basic random generation."""
        template = "{Color}, {Size}"
        context = ResolvedContext(
            imports={
                'Color': {'red': 'red', 'blue': 'blue', 'green': 'green'},
                'Size': {'small': 'small', 'large': 'large'}
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='random',
            seed=42,
            seed_mode='fixed',
            max_images=5
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should generate 5 prompts
        assert len(results) == 5

        # All should have Color and Size
        for r in results:
            assert 'Color' in r['variations']
            assert 'Size' in r['variations']
            assert r['variations']['Color'] in ['red', 'blue', 'green']
            assert r['variations']['Size'] in ['small', 'large']

    def test_random_uniqueness(self):
        """Test that random mode generates unique combinations."""
        template = "{A}, {B}"
        context = ResolvedContext(
            imports={
                'A': {'a1': 'a1', 'a2': 'a2'},
                'B': {'b1': 'b1', 'b2': 'b2'}
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='random',
            seed=42,
            seed_mode='fixed',
            max_images=4  # Request all 4 possible combinations
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should generate up to 4 unique combinations
        assert len(results) <= 4

        # All combinations should be unique
        combos = [(r['variations']['A'], r['variations']['B']) for r in results]
        assert len(combos) == len(set(combos))

    # ===== Seed Management Tests =====

    def test_seed_mode_fixed(self):
        """Test fixed seed mode (same seed for all images)."""
        template = "{Color}"
        context = ResolvedContext(
            imports={'Color': {'red': 'red', 'blue': 'blue'}},
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=42,
            seed_mode='fixed',
            max_images=5
        )

        results = self.generator.generate_prompts(template, context, generation)

        # All seeds should be 42
        for r in results:
            assert r['seed'] == 42

    def test_seed_mode_progressive(self):
        """Test progressive seed mode (seed increments)."""
        template = "{Color}"
        context = ResolvedContext(
            imports={'Color': {'red': 'red', 'blue': 'blue'}},
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=100,
            seed_mode='progressive',
            max_images=5
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Seeds should be 100, 101, 102, ...
        assert results[0]['seed'] == 100
        assert results[1]['seed'] == 101

    def test_seed_mode_random(self):
        """Test random seed mode (seed = -1)."""
        template = "{Color}"
        context = ResolvedContext(
            imports={'Color': {'red': 'red', 'blue': 'blue'}},
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=42,  # Ignored in random mode
            seed_mode='random',
            max_images=5
        )

        results = self.generator.generate_prompts(template, context, generation)

        # All seeds should be -1
        for r in results:
            assert r['seed'] == -1

    # ===== Selector Application Tests =====

    def test_selector_limit(self):
        """Test limit selector [N]."""
        template = "{Color[3]}"
        context = ResolvedContext(
            imports={
                'Color': {str(i): f'color{i}' for i in range(10)}  # 10 colors
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=1,
            seed_mode='fixed',
            max_images=10
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should limit to 3 variations
        assert len(results) == 3

    def test_selector_indexes(self):
        """Test index selector [#i,j,k]."""
        template = "{Color[#0,2,4]}"
        context = ResolvedContext(
            imports={
                'Color': {str(i): f'color{i}' for i in range(10)}
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=1,
            seed_mode='fixed',
            max_images=10
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should select indexes 0, 2, 4 = 3 combinations
        assert len(results) == 3

        # Check correct values (color0, color2, color4)
        colors = [r['variations']['Color'] for r in results]
        assert 'color0' in colors
        assert 'color2' in colors
        assert 'color4' in colors

    def test_selector_keys(self):
        """Test key selector [Key1,Key2]."""
        template = "{Haircut[BobCut,LongHair]}"
        context = ResolvedContext(
            imports={
                'Haircut': {
                    'BobCut': 'bob cut',
                    'LongHair': 'long hair',
                    'ShortHair': 'short hair',
                    'Ponytail': 'ponytail'
                }
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=1,
            seed_mode='fixed',
            max_images=10
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should select only BobCut and LongHair
        assert len(results) == 2

        haircuts = [r['variations']['Haircut'] for r in results]
        assert 'bob cut' in haircuts
        assert 'long hair' in haircuts
        assert 'short hair' not in haircuts
        assert 'ponytail' not in haircuts

    def test_selector_with_weight(self):
        """Test combined selector [N;$W]."""
        template = "{Color[3;$5]}"
        context = ResolvedContext(
            imports={
                'Color': {str(i): f'color{i}' for i in range(10)}
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=1,
            seed_mode='fixed',
            max_images=10
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should limit to 3 variations (weight doesn't affect count)
        assert len(results) == 3

    # ===== Integration Tests =====

    def test_integration_with_normalizer(self):
        """Test that prompts are normalized correctly."""
        template = "{Color},,  {Size}  "
        context = ResolvedContext(
            imports={
                'Color': {'red': 'red'},
                'Size': {'large': 'large'}
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=1,
            seed_mode='fixed',
            max_images=1
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Prompt should be normalized (no double commas, trimmed)
        assert results[0]['prompt'] == 'red, large'

    def test_complex_template(self):
        """Test complex template with multiple features."""
        template = "{Style[$1]}, {Subject[$5]}, {Quality[$0]}, detailed"
        context = ResolvedContext(
            imports={
                'Style': {'anime': 'anime', 'realistic': 'realistic'},
                'Subject': {'girl': '1girl', 'boy': '1boy'},
                'Quality': {'high': 'masterpiece', 'low': 'simple'}
            },
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=1,
            seed_mode='progressive',
            max_images=10
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should generate 2×2 = 4 combinations (Quality weight 0 excluded)
        assert len(results) == 4

        # Check weight ordering (Style outer, Subject inner)
        assert results[0]['variations']['Style'] == 'anime'
        assert results[1]['variations']['Style'] == 'anime'
        assert results[2]['variations']['Style'] == 'realistic'
        assert results[3]['variations']['Style'] == 'realistic'

        # Quality should be random but present
        for r in results:
            assert 'Quality' in r['variations']

        # Seeds should be progressive
        assert results[0]['seed'] == 1
        assert results[1]['seed'] == 2
        assert results[2]['seed'] == 3
        assert results[3]['seed'] == 4

    def test_no_variations(self):
        """Test template with no variations (static prompt)."""
        template = "masterpiece, beautiful, detailed"
        context = ResolvedContext(
            imports={},
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=42,
            seed_mode='fixed',
            max_images=5
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should generate 1 prompt
        assert len(results) == 1
        assert results[0]['prompt'] == 'masterpiece, beautiful, detailed'
        assert results[0]['seed'] == 42
        assert results[0]['variations'] == {}

    def test_empty_template(self):
        """Test empty template."""
        template = ""
        context = ResolvedContext(
            imports={},
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=1,
            seed_mode='fixed',
            max_images=1
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should generate 1 empty prompt
        assert len(results) == 1
        assert results[0]['prompt'] == ''

    def test_prompt_output_format(self):
        """Test that output format is correct."""
        template = "{Color}"
        context = ResolvedContext(
            imports={'Color': {'red': 'red'}},
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=42,
            seed_mode='fixed',
            max_images=1
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Check output format
        assert len(results) == 1
        prompt = results[0]
        assert 'prompt' in prompt
        assert 'negative_prompt' in prompt
        assert 'seed' in prompt
        assert 'variations' in prompt
        assert isinstance(prompt['prompt'], str)
        assert isinstance(prompt['negative_prompt'], str)
        assert isinstance(prompt['seed'], int)
        assert isinstance(prompt['variations'], dict)

    def test_multiple_placeholders_same_import(self):
        """Test multiple placeholders referencing same import."""
        template = "{Color}, {Color}"
        context = ResolvedContext(
            imports={'Color': {'red': 'red', 'blue': 'blue'}},
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=1,
            seed_mode='fixed',
            max_images=5
        )

        results = self.generator.generate_prompts(template, context, generation)

        # Should generate 2 combinations (not 2×2 = 4)
        # Because both placeholders use same variation
        assert len(results) == 2

        # Both placeholders should have same value
        for r in results:
            assert r['prompt'] in ['red, red', 'blue, blue']
