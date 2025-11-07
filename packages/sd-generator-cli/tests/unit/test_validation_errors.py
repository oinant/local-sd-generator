"""
Unit tests for validation error messages added in commit 8dd57e5.

Tests validation of:
- Unresolved placeholders in templates (generator.py)
- Clear error messages with available variations
"""

import pytest
from pathlib import Path
from sd_generator_cli.templating.generators.generator import PromptGenerator
from sd_generator_cli.templating.models.config_models import GenerationConfig, ResolvedContext
from sd_generator_cli.templating.resolvers.template_resolver import TemplateResolver
from sd_generator_cli.templating.normalizers.normalizer import PromptNormalizer


class TestUnresolvedPlaceholderValidation:
    """Test validation of unresolved placeholders in templates."""

    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = TemplateResolver()
        self.normalizer = PromptNormalizer()
        self.generator = PromptGenerator(self.resolver, self.normalizer)

    def test_unresolved_placeholder_raises_error(self):
        """Test that unresolved placeholders raise clear error."""
        template = "masterpiece, {Expression}, {Missing}"
        context = ResolvedContext(
            imports={
                'Expression': {'happy': 'smiling', 'sad': 'crying'}
                # 'Missing' placeholder has no corresponding import
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

        with pytest.raises(ValueError) as exc_info:
            self.generator.generate_prompts(template, context, generation)

        error_msg = str(exc_info.value)
        # New format: "✗ Unresolved placeholders detected: Missing"
        assert "Unresolved placeholders" in error_msg
        assert "Missing" in error_msg
        assert "Expression" in error_msg  # Available import

    def test_multiple_unresolved_placeholders_listed(self):
        """Test that multiple unresolved placeholders are listed."""
        template = "{First}, {Second}, {Third}"
        context = ResolvedContext(
            imports={
                'Second': {'a': 'value a'}
                # 'First' and 'Third' are missing
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

        with pytest.raises(ValueError) as exc_info:
            self.generator.generate_prompts(template, context, generation)

        error_msg = str(exc_info.value)
        # Should list both missing placeholders
        assert "Unresolved placeholders" in error_msg
        assert "First" in error_msg
        assert "Third" in error_msg
        assert "Second" in error_msg  # Available import

    def test_placeholder_with_selector_but_no_import_raises_error(self):
        """Test that placeholder with selector but no import raises error."""
        template = "{Color[BobCut,LongHair]}"
        context = ResolvedContext(
            imports={
                # 'Color' is not defined
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

        with pytest.raises(ValueError) as exc_info:
            self.generator.generate_prompts(template, context, generation)

        error_msg = str(exc_info.value)
        assert "Unresolved placeholders" in error_msg
        assert "Color" in error_msg

    def test_all_placeholders_resolved_no_error(self):
        """Test that having all placeholders resolved does not raise error."""
        template = "{Expression}, {Angle}"
        context = ResolvedContext(
            imports={
                'Expression': {'happy': 'smiling'},
                'Angle': {'front': 'front view'}
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

        # Should not raise error
        results = self.generator.generate_prompts(template, context, generation)
        assert len(results) == 1  # 1×1 = 1 combination

    def test_placeholder_with_non_dict_import_raises_error(self):
        """Test that placeholder with non-dict import value raises error."""
        template = "{Expression}"
        context = ResolvedContext(
            imports={
                'Expression': 'not a dict'  # Should be dict
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

        with pytest.raises(ValueError) as exc_info:
            self.generator.generate_prompts(template, context, generation)

        error_msg = str(exc_info.value)
        assert "Unresolved placeholders" in error_msg
        assert "Expression" in error_msg

    def test_empty_context_with_placeholders_raises_error(self):
        """Test that placeholders with empty context raise error."""
        template = "{Any}"
        context = ResolvedContext(
            imports={},  # Empty
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=42,
            seed_mode='fixed',
            max_images=10
        )

        with pytest.raises(ValueError) as exc_info:
            self.generator.generate_prompts(template, context, generation)

        error_msg = str(exc_info.value)
        assert "Unresolved placeholders" in error_msg
        assert "Any" in error_msg

    def test_template_with_no_placeholders_no_error(self):
        """Test that template with no placeholders does not raise error."""
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
            max_images=1
        )

        # Should not raise error
        results = self.generator.generate_prompts(template, context, generation)
        assert len(results) == 1
        assert results[0]['prompt'] == 'masterpiece, beautiful, detailed'

    def test_placeholder_with_weight_but_no_import_raises_error(self):
        """Test that placeholder with weight selector but no import raises error."""
        template = "{Color[$10]}"
        context = ResolvedContext(
            imports={},
            chunks={},
            parameters={}
        )
        generation = GenerationConfig(
            mode='combinatorial',
            seed=42,
            seed_mode='fixed',
            max_images=10
        )

        with pytest.raises(ValueError) as exc_info:
            self.generator.generate_prompts(template, context, generation)

        error_msg = str(exc_info.value)
        assert "Unresolved placeholders" in error_msg
        assert "Color" in error_msg

    def test_complex_template_partial_resolution_raises_error(self):
        """Test complex template with some resolved and some unresolved placeholders."""
        template = "{Style}, {Subject}, {Quality}, {Missing1}, {Missing2}"
        context = ResolvedContext(
            imports={
                'Style': {'anime': 'anime style'},
                'Subject': {'girl': '1girl'},
                'Quality': {'high': 'masterpiece'}
                # 'Missing1' and 'Missing2' not defined
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

        with pytest.raises(ValueError) as exc_info:
            self.generator.generate_prompts(template, context, generation)

        error_msg = str(exc_info.value)
        assert "Unresolved placeholders" in error_msg
        assert "Missing1" in error_msg
        assert "Missing2" in error_msg
        # Available imports should be listed
        assert "Quality" in error_msg
        assert "Style" in error_msg
        assert "Subject" in error_msg
