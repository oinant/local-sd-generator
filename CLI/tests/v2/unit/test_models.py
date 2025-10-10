"""
Unit tests for V2 config models (Phase 1).

Tests dataclass instantiation and basic properties.
"""

import pytest
from pathlib import Path
from templating.models.config_models import (
    TemplateConfig,
    ChunkConfig,
    GenerationConfig,
    PromptConfig,
    ResolvedContext
)
from templating.validators.validation_error import ValidationError, ValidationResult


class TestTemplateConfig:
    """Tests for TemplateConfig dataclass."""

    def test_create_minimal_template_config(self):
        """Test creating a minimal template config with required fields only."""
        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='masterpiece, {prompt}, detailed',
            source_file=Path('/test/template.yaml')
        )

        assert config.version == '2.0'
        assert config.name == 'TestTemplate'
        assert config.template == 'masterpiece, {prompt}, detailed'
        assert config.source_file == Path('/test/template.yaml')
        assert config.implements is None
        assert config.parameters == {}
        assert config.imports == {}
        assert config.negative_prompt == ''

    def test_create_full_template_config(self):
        """Test creating a template config with all fields."""
        config = TemplateConfig(
            version='2.0',
            name='FullTemplate',
            template='masterpiece, {prompt}',
            source_file=Path('/test/full.yaml'),
            implements='../parent.template.yaml',
            parameters={'width': 832, 'height': 1216},
            imports={'Character': '../chunks/char.chunk.yaml'},
            negative_prompt='low quality, {negprompt}'
        )

        assert config.implements == '../parent.template.yaml'
        assert config.parameters == {'width': 832, 'height': 1216}
        assert config.imports == {'Character': '../chunks/char.chunk.yaml'}
        assert config.negative_prompt == 'low quality, {negprompt}'


class TestChunkConfig:
    """Tests for ChunkConfig dataclass."""

    def test_create_minimal_chunk_config(self):
        """Test creating a minimal chunk config."""
        config = ChunkConfig(
            version='2.0',
            type='character',
            template='1girl, {Main}, {Angle}',
            source_file=Path('/test/chunk.yaml')
        )

        assert config.version == '2.0'
        assert config.type == 'character'
        assert config.template == '1girl, {Main}, {Angle}'
        assert config.source_file == Path('/test/chunk.yaml')
        assert config.implements is None
        assert config.imports == {}
        assert config.defaults == {}
        assert config.chunks == {}

    def test_create_full_chunk_config(self):
        """Test creating a chunk config with all fields."""
        config = ChunkConfig(
            version='2.0',
            type='character',
            template='1girl, {Main}, {HairCut}',
            source_file=Path('/test/chunk.yaml'),
            implements='../parent.chunk.yaml',
            imports={'Haircuts': '../variations/haircuts.yaml'},
            defaults={'Main': '30, slim'},
            chunks={'HairCut': 'Haircuts.BobCut'}
        )

        assert config.implements == '../parent.chunk.yaml'
        assert config.imports == {'Haircuts': '../variations/haircuts.yaml'}
        assert config.defaults == {'Main': '30, slim'}
        assert config.chunks == {'HairCut': 'Haircuts.BobCut'}


class TestGenerationConfig:
    """Tests for GenerationConfig dataclass."""

    def test_create_generation_config(self):
        """Test creating a generation config."""
        config = GenerationConfig(
            mode='random',
            seed=42,
            seed_mode='progressive',
            max_images=100
        )

        assert config.mode == 'random'
        assert config.seed == 42
        assert config.seed_mode == 'progressive'
        assert config.max_images == 100


class TestPromptConfig:
    """Tests for PromptConfig dataclass."""

    def test_create_minimal_prompt_config(self):
        """Test creating a minimal prompt config."""
        gen_config = GenerationConfig(
            mode='random',
            seed=42,
            seed_mode='progressive',
            max_images=10
        )

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=gen_config,
            template='1girl, beautiful',
            source_file=Path('/test/prompt.yaml')
        )

        assert config.version == '2.0'
        assert config.name == 'TestPrompt'
        assert config.implements == '../base.template.yaml'
        assert config.generation == gen_config
        assert config.template == '1girl, beautiful'
        assert config.source_file == Path('/test/prompt.yaml')
        assert config.imports == {}
        assert config.negative_prompt is None

    def test_create_full_prompt_config(self):
        """Test creating a prompt config with all fields."""
        gen_config = GenerationConfig(
            mode='combinatorial',
            seed=100,
            seed_mode='fixed',
            max_images=50
        )

        config = PromptConfig(
            version='2.0',
            name='FullPrompt',
            implements='../base.template.yaml',
            generation=gen_config,
            template='@Character, {Place}',
            source_file=Path('/test/prompt.yaml'),
            imports={'Place': ['room', 'garden']},
            negative_prompt='bad quality'
        )

        assert config.imports == {'Place': ['room', 'garden']}
        assert config.negative_prompt == 'bad quality'


class TestResolvedContext:
    """Tests for ResolvedContext dataclass."""

    def test_create_minimal_resolved_context(self):
        """Test creating a minimal resolved context."""
        context = ResolvedContext(
            imports={'Angle': {'Front': 'front view', 'Side': 'side view'}},
            chunks={},
            parameters={'width': 832}
        )

        assert context.imports == {'Angle': {'Front': 'front view', 'Side': 'side view'}}
        assert context.chunks == {}
        assert context.parameters == {'width': 832}
        assert context.variation_state == {}

    def test_create_full_resolved_context(self):
        """Test creating a resolved context with all fields."""
        chunk_config = ChunkConfig(
            version='2.0',
            type='character',
            template='1girl',
            source_file=Path('/test/chunk.yaml')
        )

        context = ResolvedContext(
            imports={'Angle': {'Front': 'front view'}},
            chunks={'Character': chunk_config},
            parameters={'width': 832},
            variation_state={'Angle': 'Front'}
        )

        assert context.chunks == {'Character': chunk_config}
        assert context.variation_state == {'Angle': 'Front'}


class TestValidationError:
    """Tests for ValidationError dataclass."""

    def test_create_minimal_validation_error(self):
        """Test creating a minimal validation error."""
        error = ValidationError(
            type='structure',
            message='Missing required field: version'
        )

        assert error.type == 'structure'
        assert error.message == 'Missing required field: version'
        assert error.file is None
        assert error.line is None
        assert error.name is None
        assert error.details is None

    def test_create_full_validation_error(self):
        """Test creating a validation error with all fields."""
        error = ValidationError(
            type='path',
            message='File not found',
            file=Path('/test/missing.yaml'),
            line=10,
            name='imports.Angle',
            details={'expected': '../variations/angles.yaml'}
        )

        assert error.type == 'path'
        assert error.file == Path('/test/missing.yaml')
        assert error.line == 10
        assert error.name == 'imports.Angle'
        assert error.details == {'expected': '../variations/angles.yaml'}

    def test_validation_error_to_dict(self):
        """Test converting validation error to dictionary."""
        error = ValidationError(
            type='template',
            message='Reserved placeholder not allowed',
            file=Path('/test/chunk.yaml'),
            name='prompt'
        )

        error_dict = error.to_dict()

        assert error_dict['type'] == 'template'
        assert error_dict['message'] == 'Reserved placeholder not allowed'
        assert error_dict['file'] == '/test/chunk.yaml'
        assert error_dict['name'] == 'prompt'
        assert error_dict['line'] is None


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_create_valid_result(self):
        """Test creating a validation result with no errors."""
        result = ValidationResult(
            is_valid=True,
            errors=[]
        )

        assert result.is_valid is True
        assert result.errors == []
        assert result.error_count == 0

    def test_create_invalid_result(self):
        """Test creating a validation result with errors."""
        errors = [
            ValidationError(type='structure', message='Error 1'),
            ValidationError(type='path', message='Error 2'),
            ValidationError(type='template', message='Error 3')
        ]

        result = ValidationResult(
            is_valid=False,
            errors=errors
        )

        assert result.is_valid is False
        assert len(result.errors) == 3
        assert result.error_count == 3

    def test_validation_result_to_json(self):
        """Test converting validation result to JSON."""
        errors = [
            ValidationError(type='structure', message='Error 1'),
            ValidationError(type='path', message='Error 2')
        ]

        result = ValidationResult(is_valid=False, errors=errors)
        json_output = result.to_json()

        assert 'errors' in json_output
        assert 'count' in json_output
        assert json_output['count'] == 2
        assert len(json_output['errors']) == 2
        assert json_output['errors'][0]['type'] == 'structure'
        assert json_output['errors'][1]['type'] == 'path'
