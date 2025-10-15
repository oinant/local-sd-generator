"""
Unit tests for ConfigParser (Phase 1).

Tests parsing of YAML dictionaries into config model objects.
"""

import pytest
from pathlib import Path
from sd_generator_cli.templating.loaders.parser import ConfigParser
from sd_generator_cli.templating.models.config_models import (
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
            'template': '{prompt}'  # V2.0 Corrected: templates must have {prompt}
        }
        source_file = Path('/test/noversion.yaml')

        config = parser.parse_template(data, source_file)

        assert config.version == '1.0.0'

    def test_parse_template_with_dict_raises_error(self):
        """Test that template field as dict raises helpful ValueError."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'BadTemplate',
            'template': {'prompt': None}  # Dict instead of string
        }
        source_file = Path('/test/badtemplate.yaml')

        with pytest.raises(ValueError) as exc_info:
            parser.parse_template(data, source_file)

        # Check error message contains helpful hint
        error_msg = str(exc_info.value)
        assert 'Expected string, got dict' in error_msg
        assert 'quote them' in error_msg
        assert '{prompt}' in error_msg


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

    def test_parse_chunk_with_dict_template_raises_error(self):
        """Test that chunk template field as dict raises helpful ValueError."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'type': 'character',
            'template': {'Expression': None}  # Dict instead of string
        }
        source_file = Path('/test/badchunk.yaml')

        with pytest.raises(ValueError) as exc_info:
            parser.parse_chunk(data, source_file)

        # Check error message contains helpful hint
        error_msg = str(exc_info.value)
        assert 'Expected string, got dict' in error_msg
        assert 'quote them' in error_msg
        assert '{Expression}' in error_msg


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
            'prompt': '1girl, beautiful'  # V2.0 Corrected: uses 'prompt' not 'template'
        }
        source_file = Path('/test/prompt.yaml')

        config = parser.parse_prompt(data, source_file)

        assert isinstance(config, PromptConfig)
        assert config.version == '2.0'
        assert config.name == 'MinimalPrompt'
        assert config.implements == '../base.template.yaml'
        assert config.prompt == '1girl, beautiful'  # V2.0 Corrected: 'prompt' field
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
            'prompt': '@Character, {Place}',  # V2.0 Corrected: 'prompt' not 'template'
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
            'prompt': 'test'  # V2.0 Corrected: 'prompt' not 'template'
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
            'prompt': 'test'  # V2.0 Corrected: 'prompt' not 'template'
        }
        source_file = Path('/test/incomplete_gen.yaml')

        with pytest.raises(KeyError):
            parser.parse_prompt(data, source_file)

    def test_parse_prompt_with_dict_raises_error(self):
        """Test that prompt field as dict raises helpful ValueError."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'BadPrompt',
            'generation': {
                'mode': 'random',
                'seed': 42,
                'seed_mode': 'progressive',
                'max_images': 10
            },
            'prompt': {'Angle': None}  # Dict instead of string
        }
        source_file = Path('/test/badprompt.yaml')

        with pytest.raises(ValueError) as exc_info:
            parser.parse_prompt(data, source_file)

        # Check error message contains helpful hint
        error_msg = str(exc_info.value)
        assert 'Expected string, got dict' in error_msg
        assert 'quote them' in error_msg
        assert '{Angle}' in error_msg


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
            'template': '{prompt}',  # V2.0 Corrected: templates must have {prompt}
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


class TestV2ValidationRules:
    """Tests for V2.0 corrected validation rules (Template Method Pattern)."""

    def test_template_requires_prompt_placeholder(self):
        """Test that templates must contain {prompt} placeholder."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'BadTemplate',
            'template': 'masterpiece, detailed'  # Missing {prompt}
        }
        source_file = Path('/test/template.yaml')

        with pytest.raises(ValueError) as exc_info:
            parser.parse_template(data, source_file)

        assert 'must contain {prompt} placeholder' in str(exc_info.value)

    def test_template_with_prompt_placeholder_passes(self):
        """Test that template with {prompt} placeholder parses correctly."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'GoodTemplate',
            'template': 'masterpiece, {prompt}, detailed'
        }
        source_file = Path('/test/template.yaml')

        config = parser.parse_template(data, source_file)

        assert config.template == 'masterpiece, {prompt}, detailed'

    def test_chunk_rejects_reserved_placeholder_prompt(self):
        """Test that chunks cannot use {prompt} placeholder."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'type': 'character',
            'template': '1girl, {prompt}, beautiful'  # Reserved placeholder
        }
        source_file = Path('/test/chunk.yaml')

        with pytest.raises(ValueError) as exc_info:
            parser.parse_chunk(data, source_file)

        assert 'cannot use reserved placeholders' in str(exc_info.value)
        assert '{prompt}' in str(exc_info.value)

    def test_chunk_rejects_reserved_placeholder_negprompt(self):
        """Test that chunks cannot use {negprompt} placeholder."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'type': 'character',
            'template': '1girl, {negprompt}'  # Reserved placeholder
        }
        source_file = Path('/test/chunk.yaml')

        with pytest.raises(ValueError) as exc_info:
            parser.parse_chunk(data, source_file)

        assert 'cannot use reserved placeholders' in str(exc_info.value)
        assert '{negprompt}' in str(exc_info.value)

    def test_chunk_rejects_reserved_placeholder_loras(self):
        """Test that chunks cannot use {loras} placeholder."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'type': 'character',
            'template': '1girl, {loras}'  # Reserved placeholder
        }
        source_file = Path('/test/chunk.yaml')

        with pytest.raises(ValueError) as exc_info:
            parser.parse_chunk(data, source_file)

        assert 'cannot use reserved placeholders' in str(exc_info.value)
        assert '{loras}' in str(exc_info.value)

    def test_chunk_allows_custom_placeholders(self):
        """Test that chunks can use custom (non-reserved) placeholders."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'type': 'character',
            'template': '1girl, {Age}, {HairColor}, {Expression}'
        }
        source_file = Path('/test/chunk.yaml')

        config = parser.parse_chunk(data, source_file)

        assert config.template == '1girl, {Age}, {HairColor}, {Expression}'

    def test_prompt_rejects_template_field(self):
        """Test that 'template:' field is rejected in prompt files."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'TestPrompt',
            'generation': {
                'mode': 'random',
                'seed': 42,
                'seed_mode': 'progressive',
                'max_images': 10
            },
            'template': 'should be prompt'  # Wrong field
        }
        source_file = Path('/test/prompt.yaml')

        with pytest.raises(ValueError) as exc_info:
            parser.parse_prompt(data, source_file)

        assert "must use 'prompt:' field, not 'template:'" in str(exc_info.value)

    def test_prompt_with_prompt_field_passes(self):
        """Test parsing with correct 'prompt:' field."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'TestPrompt',
            'generation': {
                'mode': 'random',
                'seed': 42,
                'seed_mode': 'progressive',
                'max_images': 10
            },
            'prompt': '1girl, beautiful'  # Correct field
        }
        source_file = Path('/test/prompt.yaml')

        config = parser.parse_prompt(data, source_file)

        assert config.prompt == '1girl, beautiful'
        assert hasattr(config, 'template')  # Should have optional template field for resolved result

    def test_prompt_rejects_variations_field(self):
        """Test that 'variations:' field is rejected in V2.0 (should use 'imports:')."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'TestPrompt',
            'generation': {
                'mode': 'random',
                'seed': 42,
                'seed_mode': 'progressive',
                'max_images': 10
            },
            'prompt': '1girl, {HairCut}',
            'variations': {  # Wrong field in V2.0
                'HairCut': '../variations/haircuts.yaml'
            }
        }
        source_file = Path('/test/prompt.yaml')

        with pytest.raises(ValueError) as exc_info:
            parser.parse_prompt(data, source_file)

        error_msg = str(exc_info.value)
        assert "V2.0 Template System uses 'imports:' field, not 'variations:'" in error_msg
        assert "Please rename 'variations:' to 'imports:'" in error_msg
        assert 'HairCut' in error_msg  # Should show example

    def test_prompt_with_imports_field_passes(self):
        """Test that 'imports:' field works correctly in V2.0."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'TestPrompt',
            'generation': {
                'mode': 'random',
                'seed': 42,
                'seed_mode': 'progressive',
                'max_images': 10
            },
            'prompt': '1girl, {HairCut}',
            'imports': {  # Correct field in V2.0
                'HairCut': '../variations/haircuts.yaml'
            }
        }
        source_file = Path('/test/prompt.yaml')

        config = parser.parse_prompt(data, source_file)

        assert config.prompt == '1girl, {HairCut}'
        assert config.imports == {'HairCut': '../variations/haircuts.yaml'}
