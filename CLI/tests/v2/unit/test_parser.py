"""
Unit tests for ConfigParser (Phase 1).

Tests parsing of YAML dictionaries into config model objects.
"""

import pytest
from pathlib import Path
from templating.v2.loaders.parser import ConfigParser
from templating.v2.models.config_models import (
    TemplateConfig,
    ChunkConfig,
    PromptConfig,
    GenerationConfig
)


class TestConfigParserTemplate:
    """Tests for parsing .template.yaml files."""

    def test_parse_minimal_template(self):
        """Test parsing a minimal template config."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'MinimalTemplate',
            'template': 'masterpiece, {prompt}'
        }
        source_file = Path('/test/template.yaml')

        config = parser.parse_template(data, source_file)

        assert isinstance(config, TemplateConfig)
        assert config.version == '2.0'
        assert config.name == 'MinimalTemplate'
        assert config.template == 'masterpiece, {prompt}'
        assert config.source_file == source_file
        assert config.implements is None
        assert config.parameters == {}
        assert config.imports == {}
        assert config.negative_prompt == ''

    def test_parse_full_template(self):
        """Test parsing a template with all fields."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'FullTemplate',
            'template': 'masterpiece, {prompt}',
            'implements': '../parent.template.yaml',
            'parameters': {'width': 832, 'height': 1216, 'steps': 30},
            'imports': {
                'Character': '../chunks/char.chunk.yaml',
                'Style': '../variations/styles.yaml'
            },
            'negative_prompt': 'low quality, {negprompt}'
        }
        source_file = Path('/test/full.yaml')

        config = parser.parse_template(data, source_file)

        assert config.implements == '../parent.template.yaml'
        assert config.parameters == {'width': 832, 'height': 1216, 'steps': 30}
        assert config.imports == {
            'Character': '../chunks/char.chunk.yaml',
            'Style': '../variations/styles.yaml'
        }
        assert config.negative_prompt == 'low quality, {negprompt}'

    def test_parse_template_missing_required_field(self):
        """Test parsing template with missing required field raises KeyError."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'Incomplete'
            # Missing 'template' field
        }
        source_file = Path('/test/incomplete.yaml')

        with pytest.raises(KeyError):
            parser.parse_template(data, source_file)

    def test_parse_template_defaults_version(self):
        """Test that version defaults to 1.0.0 if not specified."""
        parser = ConfigParser()
        data = {
            # No 'version' field
            'name': 'NoVersion',
            'template': 'test'
        }
        source_file = Path('/test/noversion.yaml')

        config = parser.parse_template(data, source_file)

        assert config.version == '1.0.0'


class TestConfigParserChunk:
    """Tests for parsing .chunk.yaml files."""

    def test_parse_minimal_chunk(self):
        """Test parsing a minimal chunk config."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'type': 'character',
            'template': '1girl, {Main}, {Angle}'
        }
        source_file = Path('/test/chunk.yaml')

        config = parser.parse_chunk(data, source_file)

        assert isinstance(config, ChunkConfig)
        assert config.version == '2.0'
        assert config.type == 'character'
        assert config.template == '1girl, {Main}, {Angle}'
        assert config.source_file == source_file
        assert config.implements is None
        assert config.imports == {}
        assert config.defaults == {}
        assert config.chunks == {}

    def test_parse_full_chunk(self):
        """Test parsing a chunk with all fields."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'type': 'character',
            'template': '1girl, {Main}, {HairCut}',
            'implements': '../parent.chunk.yaml',
            'imports': {
                'Haircuts': '../variations/haircuts.yaml',
                'Poses': '../variations/poses.yaml'
            },
            'defaults': {
                'Main': '30, slim',
                'HairCut': 'BobCut'
            },
            'chunks': {
                'HairCut': 'Haircuts.BobCut',
                'Main': '22, supermodel'
            }
        }
        source_file = Path('/test/full_chunk.yaml')

        config = parser.parse_chunk(data, source_file)

        assert config.implements == '../parent.chunk.yaml'
        assert config.imports == {
            'Haircuts': '../variations/haircuts.yaml',
            'Poses': '../variations/poses.yaml'
        }
        assert config.defaults == {'Main': '30, slim', 'HairCut': 'BobCut'}
        assert config.chunks == {'HairCut': 'Haircuts.BobCut', 'Main': '22, supermodel'}

    def test_parse_chunk_missing_type(self):
        """Test parsing chunk with missing type field raises KeyError."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            # Missing 'type' field
            'template': '1girl'
        }
        source_file = Path('/test/notype.yaml')

        with pytest.raises(KeyError):
            parser.parse_chunk(data, source_file)


class TestConfigParserPrompt:
    """Tests for parsing .prompt.yaml files."""

    def test_parse_minimal_prompt(self):
        """Test parsing a minimal prompt config."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'MinimalPrompt',
            'implements': '../base.template.yaml',
            'generation': {
                'mode': 'random',
                'seed': 42,
                'seed_mode': 'progressive',
                'max_images': 10
            },
            'template': '1girl, beautiful'
        }
        source_file = Path('/test/prompt.yaml')

        config = parser.parse_prompt(data, source_file)

        assert isinstance(config, PromptConfig)
        assert config.version == '2.0'
        assert config.name == 'MinimalPrompt'
        assert config.implements == '../base.template.yaml'
        assert config.template == '1girl, beautiful'
        assert config.source_file == source_file

        # Check generation config
        assert isinstance(config.generation, GenerationConfig)
        assert config.generation.mode == 'random'
        assert config.generation.seed == 42
        assert config.generation.seed_mode == 'progressive'
        assert config.generation.max_images == 10

        assert config.imports == {}
        assert config.negative_prompt is None

    def test_parse_full_prompt(self):
        """Test parsing a prompt with all fields."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'FullPrompt',
            'implements': '../base.template.yaml',
            'generation': {
                'mode': 'combinatorial',
                'seed': 100,
                'seed_mode': 'fixed',
                'max_images': 50
            },
            'imports': {
                'Character': '../chunks/character.chunk.yaml',
                'Place': ['room', 'garden']
            },
            'template': '@Character, {Place}',
            'negative_prompt': 'bad quality'
        }
        source_file = Path('/test/full_prompt.yaml')

        config = parser.parse_prompt(data, source_file)

        assert config.imports == {
            'Character': '../chunks/character.chunk.yaml',
            'Place': ['room', 'garden']
        }
        assert config.negative_prompt == 'bad quality'

    def test_parse_prompt_missing_generation(self):
        """Test parsing prompt with missing generation field raises KeyError."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'NoGen',
            'implements': '../base.template.yaml',
            # Missing 'generation' field
            'template': 'test'
        }
        source_file = Path('/test/nogen.yaml')

        with pytest.raises(KeyError):
            parser.parse_prompt(data, source_file)

    def test_parse_prompt_missing_generation_field(self):
        """Test parsing prompt with incomplete generation config raises KeyError."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'IncompleteGen',
            'implements': '../base.template.yaml',
            'generation': {
                'mode': 'random',
                'seed': 42
                # Missing 'seed_mode' and 'max_images'
            },
            'template': 'test'
        }
        source_file = Path('/test/incomplete_gen.yaml')

        with pytest.raises(KeyError):
            parser.parse_prompt(data, source_file)


class TestConfigParserVariations:
    """Tests for parsing variation files (.yaml)."""

    def test_parse_variations_dict(self):
        """Test parsing a valid variations dictionary."""
        parser = ConfigParser()
        data = {
            'BobCut': 'bob cut, chin-length hair',
            'LongHair': 'long flowing hair, waist-length',
            'Pixie': 'pixie cut, short spiky hair'
        }

        variations = parser.parse_variations(data)

        assert isinstance(variations, dict)
        assert len(variations) == 3
        assert variations['BobCut'] == 'bob cut, chin-length hair'
        assert variations['LongHair'] == 'long flowing hair, waist-length'
        assert variations['Pixie'] == 'pixie cut, short spiky hair'

    def test_parse_variations_converts_to_strings(self):
        """Test that all keys and values are converted to strings."""
        parser = ConfigParser()
        data = {
            1: 'numeric key',
            'key2': 123,
            'key3': True
        }

        variations = parser.parse_variations(data)

        # All keys and values should be strings
        assert variations['1'] == 'numeric key'
        assert variations['key2'] == '123'
        assert variations['key3'] == 'True'

    def test_parse_variations_not_dict_raises_error(self):
        """Test parsing non-dict data raises ValueError."""
        parser = ConfigParser()
        data = ['item1', 'item2', 'item3']  # List instead of dict

        with pytest.raises(ValueError, match="Variations file must be a YAML dictionary"):
            parser.parse_variations(data)

    def test_parse_variations_empty_dict(self):
        """Test parsing an empty variations dictionary."""
        parser = ConfigParser()
        data = {}

        variations = parser.parse_variations(data)

        assert variations == {}


class TestConfigParserEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_template_with_none_values(self):
        """Test parsing template with None values for optional fields."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'Test',
            'template': 'test',
            'implements': None,
            'parameters': None,
            'imports': None,
            'negative_prompt': None
        }
        source_file = Path('/test/none_values.yaml')

        config = parser.parse_template(data, source_file)

        # None values should be handled gracefully
        assert config.implements is None
        assert config.parameters == {}  # get() with default
        assert config.imports == {}
        assert config.negative_prompt == ''

    def test_parse_chunk_with_empty_strings(self):
        """Test parsing chunk with empty string values."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'type': '',  # Empty type
            'template': ''  # Empty template
        }
        source_file = Path('/test/empty_strings.yaml')

        config = parser.parse_chunk(data, source_file)

        # Empty strings should be preserved
        assert config.type == ''
        assert config.template == ''
