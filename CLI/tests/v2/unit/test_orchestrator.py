"""
Tests for V2Pipeline orchestrator - Phase 6.

Tests the full pipeline integration:
- Load and parse configs
- Resolve inheritance and imports
- Generate prompts with variations
- End-to-end pipeline
"""

import pytest
import tempfile
from pathlib import Path
from templating.v2.orchestrator import V2Pipeline
from templating.v2.models.config_models import (
    PromptConfig,
    GenerationConfig,
    ResolvedContext
)


class TestV2Pipeline:
    """Test suite for V2Pipeline orchestrator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pipeline = V2Pipeline()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ===== Helper Methods =====

    def create_variation_file(self, name: str, variations: dict) -> Path:
        """Create a variation file in temp directory."""
        path = Path(self.temp_dir) / f"{name}.variations.yaml"
        content = "version: '2.0'\n"
        content += "variations:\n"
        for key, value in variations.items():
            content += f"  {key}: {value}\n"
        path.write_text(content)
        return path

    def create_template_file(self, name: str, template: str, **kwargs) -> Path:
        """Create a template file in temp directory."""
        path = Path(self.temp_dir) / f"{name}.template.yaml"
        content = f"version: '2.0'\nname: {name}\ntemplate: '{template}'\n"
        for key, value in kwargs.items():
            if key == 'parameters':
                content += "parameters:\n"
                for pk, pv in value.items():
                    content += f"  {pk}: {pv}\n"
            else:
                content += f"{key}: {value}\n"
        path.write_text(content)
        return path

    def create_prompt_file(
        self,
        name: str,
        template: str,
        generation: dict,
        implements: str = None,
        **kwargs
    ) -> Path:
        """Create a prompt file in temp directory."""
        path = Path(self.temp_dir) / f"{name}.prompt.yaml"
        content = f"version: '2.0'\nname: {name}\n"
        if implements:
            content += f"implements: {implements}\n"
        content += f"template: '{template}'\n"
        content += "generation:\n"
        for key, value in generation.items():
            if isinstance(value, str):
                content += f"  {key}: '{value}'\n"
            else:
                content += f"  {key}: {value}\n"
        for key, value in kwargs.items():
            if key == 'imports':
                content += "imports:\n"
                for ik, iv in value.items():
                    content += f"  {ik}: {iv}\n"
            elif key == 'parameters':
                content += "parameters:\n"
                for pk, pv in value.items():
                    content += f"  {pk}: {pv}\n"
        path.write_text(content)
        return path

    # ===== Load Tests =====

    def test_load_valid_prompt(self):
        """Test loading a valid standalone prompt config (no implements)."""
        # Create minimal standalone prompt file
        prompt_path = self.create_prompt_file(
            'test',
            '{Color}',
            {
                'mode': 'combinatorial',
                'seed': 42,
                'seed_mode': 'fixed',
                'max_images': 5
            },
            parameters={'steps': 20, 'cfg_scale': 7.0}
        )

        # Load
        config = self.pipeline.load(str(prompt_path))

        # Verify
        assert config.name == 'test'
        assert config.implements is None  # Standalone prompt
        assert config.template == '{Color}'
        assert config.generation.mode == 'combinatorial'
        assert config.generation.seed == 42
        assert config.parameters == {'steps': 20, 'cfg_scale': 7.0}

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            self.pipeline.load('/nonexistent/path.yaml')

    # ===== Resolve Tests =====

    def test_resolve_context(self):
        """Test resolving context from config."""
        # Create mock config with already-resolved data
        config = PromptConfig(
            version='2.0',
            name='test',
            implements='base',
            template='{Color}',
            source_file=Path('/fake/path.yaml'),
            generation=GenerationConfig(
                mode='combinatorial',
                seed=42,
                seed_mode='fixed',
                max_images=5
            )
        )

        # Mock the inheritance resolver
        original_resolve = self.pipeline.inheritance_resolver.resolve_implements
        self.pipeline.inheritance_resolver.resolve_implements = lambda x: config

        # Mock the import resolver to return test imports
        original_import_resolve = self.pipeline.import_resolver.resolve_imports
        self.pipeline.import_resolver.resolve_imports = lambda c, chain: {
            'Color': {'red': 'red', 'blue': 'blue'}
        }

        try:
            # Resolve
            context = self.pipeline.resolve(config)

            # Verify
            assert 'Color' in context.imports
            assert context.imports['Color'] == {'red': 'red', 'blue': 'blue'}
        finally:
            # Restore
            self.pipeline.inheritance_resolver.resolve_implements = original_resolve
            self.pipeline.import_resolver.resolve_imports = original_import_resolve

    # ===== Generate Tests =====

    def test_generate_prompts_combinatorial(self):
        """Test generating prompts in combinatorial mode."""
        config = PromptConfig(
            version='2.0',
            name='test',
            implements='base',
            template='{Color}, {Size}',
            source_file=Path('/fake/path.yaml'),
            generation=GenerationConfig(
                mode='combinatorial',
                seed=1,
                seed_mode='progressive',
                max_images=10
            )
        )

        context = ResolvedContext(
            imports={
                'Color': {'red': 'red', 'blue': 'blue'},
                'Size': {'small': 'small', 'large': 'large'}
            },
            chunks={},
            parameters={}
        )

        # Generate
        prompts = self.pipeline.generate(config, context)

        # Verify
        assert len(prompts) == 4  # 2×2 combinations

        # Check all combinations exist
        combos = [(p['variations']['Color'], p['variations']['Size']) for p in prompts]
        assert ('red', 'small') in combos
        assert ('red', 'large') in combos
        assert ('blue', 'small') in combos
        assert ('blue', 'large') in combos

        # Check progressive seeds
        assert prompts[0]['seed'] == 1
        assert prompts[1]['seed'] == 2
        assert prompts[2]['seed'] == 3
        assert prompts[3]['seed'] == 4

    def test_generate_prompts_random(self):
        """Test generating prompts in random mode."""
        config = PromptConfig(
            version='2.0',
            name='test',
            implements='base',
            template='{Color}',
            source_file=Path('/fake/path.yaml'),
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='random',
                max_images=5
            )
        )

        context = ResolvedContext(
            imports={'Color': {'red': 'red', 'blue': 'blue', 'green': 'green'}},
            chunks={},
            parameters={}
        )

        # Generate
        prompts = self.pipeline.generate(config, context)

        # Verify - may be less than 5 if only 3 unique values
        assert len(prompts) <= 5
        assert len(prompts) >= 1

        # All seeds should be -1 (random)
        for p in prompts:
            assert p['seed'] == -1

    def test_generate_with_negative_prompt(self):
        """Test that negative prompt is added and normalized."""
        config = PromptConfig(
            version='2.0',
            name='test',
            implements='base',
            template='{Color}',
            source_file=Path('/fake/path.yaml'),
            negative_prompt='low quality,, bad',
            generation=GenerationConfig(
                mode='combinatorial',
                seed=1,
                seed_mode='fixed',
                max_images=5
            )
        )

        context = ResolvedContext(
            imports={'Color': {'red': 'red'}},
            chunks={},
            parameters={}
        )

        # Generate
        prompts = self.pipeline.generate(config, context)

        # Verify negative prompt is normalized
        assert prompts[0]['negative_prompt'] == 'low quality, bad'

    def test_generate_with_parameters(self):
        """Test that parameters are included in output."""
        config = PromptConfig(
            version='2.0',
            name='test',
            implements='base',
            template='{Color}',
            source_file=Path('/fake/path.yaml'),
            generation=GenerationConfig(
                mode='combinatorial',
                seed=1,
                seed_mode='fixed',
                max_images=5
            )
        )

        context = ResolvedContext(
            imports={'Color': {'red': 'red'}},
            chunks={},
            parameters={'steps': 20, 'cfg_scale': 7.5}
        )

        # Generate
        prompts = self.pipeline.generate(config, context)

        # Verify parameters are included
        assert 'parameters' in prompts[0]
        assert prompts[0]['parameters']['steps'] == 20
        assert prompts[0]['parameters']['cfg_scale'] == 7.5

    # ===== Helper Method Tests =====

    def test_merge_parameters(self):
        """Test merging parameters from inheritance chain."""
        # Create mock Template configs (they have parameters field)
        from templating.v2.models.config_models import TemplateConfig

        base = TemplateConfig(
            version='2.0',
            name='base',
            implements='',
            template='',
            source_file=Path('/fake/base.yaml'),
            parameters={'steps': 20, 'width': 512}
        )

        child = TemplateConfig(
            version='2.0',
            name='child',
            implements='base',
            template='',
            source_file=Path('/fake/child.yaml'),
            parameters={'steps': 30}  # Override steps
        )

        # Merge
        merged = self.pipeline._merge_parameters([base, child])

        # Verify
        assert merged['steps'] == 30  # Child overrides
        assert merged['width'] == 512  # Inherited from base

    def test_validate_template(self):
        """Test template validation."""
        template = "{Color}"
        context = ResolvedContext(
            imports={'Color': {'red': 'red'}},
            chunks={},
            parameters={}
        )

        # Valid template
        assert self.pipeline.validate_template(template, context) is True

        # Template with missing import still returns True
        # (template resolution returns empty string for missing placeholders)
        invalid_template = "{NonExistent}"
        assert self.pipeline.validate_template(invalid_template, context) is True

    def test_get_available_variations(self):
        """Test getting available variations."""
        template = "{Color}, {Size}"
        context = ResolvedContext(
            imports={
                'Color': {'red': 'red', 'blue': 'blue'},
                'Size': {'small': 'small', 'large': 'large'}
            },
            chunks={},
            parameters={}
        )

        variations = self.pipeline.get_available_variations(template, context)

        # Verify
        assert 'Color' in variations
        assert 'Size' in variations
        assert variations['Color'] == ['red', 'blue']
        assert variations['Size'] == ['small', 'large']

    def test_calculate_total_combinations(self):
        """Test calculating total combinations."""
        template = "{A}, {B}, {C}"
        context = ResolvedContext(
            imports={
                'A': {'a1': 'a1', 'a2': 'a2'},  # 2 values
                'B': {'b1': 'b1', 'b2': 'b2', 'b3': 'b3'},  # 3 values
                'C': {'c1': 'c1'}  # 1 value
            },
            chunks={},
            parameters={}
        )

        total = self.pipeline.calculate_total_combinations(template, context)

        # Should be 2 × 3 × 1 = 6
        assert total == 6

    def test_calculate_total_combinations_no_variations(self):
        """Test calculating combinations with no variations."""
        template = "static prompt"
        context = ResolvedContext(
            imports={},
            chunks={},
            parameters={}
        )

        total = self.pipeline.calculate_total_combinations(template, context)

        # Should be 1 (static prompt)
        assert total == 1

    # ===== Integration Tests =====

    def test_end_to_end_mock(self):
        """Test end-to-end pipeline with mocked components."""
        # Create a minimal config
        config = PromptConfig(
            version='2.0',
            name='test',
            implements='base',
            template='{Color}',
            source_file=Path(self.temp_dir) / 'test.prompt.yaml',
            generation=GenerationConfig(
                mode='combinatorial',
                seed=42,
                seed_mode='fixed',
                max_images=5
            )
        )

        # Mock load to return our config
        original_load = self.pipeline.load
        self.pipeline.load = lambda x: config

        # Mock resolve to return simple context
        original_resolve = self.pipeline.resolve
        self.pipeline.resolve = lambda x: ResolvedContext(
            imports={'Color': {'red': 'red', 'blue': 'blue'}},
            chunks={},
            parameters={}
        )

        try:
            # Run pipeline
            prompts = self.pipeline.run('fake_path.yaml')

            # Verify
            assert len(prompts) == 2
            assert all(p['prompt'] in ['red', 'blue'] for p in prompts)
            assert all(p['seed'] == 42 for p in prompts)
        finally:
            # Restore
            self.pipeline.load = original_load
            self.pipeline.resolve = original_resolve

    def test_complex_pipeline_with_weights(self):
        """Test complex pipeline with weight ordering."""
        config = PromptConfig(
            version='2.0',
            name='complex',
            implements='base',
            template='{Style[$1]}, {Subject[$5]}',
            source_file=Path('/fake/path.yaml'),
            generation=GenerationConfig(
                mode='combinatorial',
                seed=1,
                seed_mode='progressive',
                max_images=10
            )
        )

        context = ResolvedContext(
            imports={
                'Style': {'anime': 'anime', 'realistic': 'realistic'},
                'Subject': {'girl': '1girl', 'boy': '1boy'}
            },
            chunks={},
            parameters={'steps': 20}
        )

        # Generate
        prompts = self.pipeline.generate(config, context)

        # Verify weight ordering
        # Style (weight 1) should be outer loop
        assert prompts[0]['variations']['Style'] == 'anime'
        assert prompts[1]['variations']['Style'] == 'anime'
        assert prompts[2]['variations']['Style'] == 'realistic'
        assert prompts[3]['variations']['Style'] == 'realistic'

        # Subject (weight 5) should be inner loop
        assert prompts[0]['variations']['Subject'] == '1girl'
        assert prompts[1]['variations']['Subject'] == '1boy'

        # Progressive seeds
        assert prompts[0]['seed'] == 1
        assert prompts[1]['seed'] == 2

    def test_pipeline_with_selectors(self):
        """Test pipeline with selectors applied."""
        config = PromptConfig(
            version='2.0',
            name='selector_test',
            implements='base',
            template='{Color[red,blue]}',
            source_file=Path('/fake/path.yaml'),
            generation=GenerationConfig(
                mode='combinatorial',
                seed=1,
                seed_mode='fixed',
                max_images=10
            )
        )

        context = ResolvedContext(
            imports={
                'Color': {'red': 'red', 'blue': 'blue', 'green': 'green', 'yellow': 'yellow'}
            },
            chunks={},
            parameters={}
        )

        # Generate
        prompts = self.pipeline.generate(config, context)

        # Verify only red and blue are selected
        assert len(prompts) == 2
        colors = [p['variations']['Color'] for p in prompts]
        assert 'red' in colors
        assert 'blue' in colors
        assert 'green' not in colors
        assert 'yellow' not in colors

    def test_output_format_completeness(self):
        """Test that all required fields are in output."""
        config = PromptConfig(
            version='2.0',
            name='test',
            implements='base',
            template='{Color}',
            source_file=Path('/fake/path.yaml'),
            negative_prompt='bad quality',
            generation=GenerationConfig(
                mode='combinatorial',
                seed=42,
                seed_mode='fixed',
                max_images=5
            )
        )

        context = ResolvedContext(
            imports={'Color': {'red': 'red'}},
            chunks={},
            parameters={'steps': 20}
        )

        # Generate
        prompts = self.pipeline.generate(config, context)

        # Verify all required fields
        prompt = prompts[0]
        assert 'prompt' in prompt
        assert 'negative_prompt' in prompt
        assert 'seed' in prompt
        assert 'variations' in prompt
        assert 'parameters' in prompt

        # Verify types
        assert isinstance(prompt['prompt'], str)
        assert isinstance(prompt['negative_prompt'], str)
        assert isinstance(prompt['seed'], int)
        assert isinstance(prompt['variations'], dict)
        assert isinstance(prompt['parameters'], dict)
