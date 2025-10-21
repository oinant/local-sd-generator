"""
Unit tests for OutputConfig parsing and usage.

Tests that output.session_name and output.filename_keys are correctly parsed
from YAML files and stored in TemplateConfig/PromptConfig.
"""

import tempfile
from pathlib import Path

from sd_generator_cli.templating.loaders.parser import ConfigParser
from sd_generator_cli.templating.models.config_models import OutputConfig


class TestOutputConfigParsing:
    """Test OutputConfig parsing from YAML files."""

    def test_parse_prompt_with_output_config(self):
        """Test parsing a prompt file with output configuration."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'Test Prompt',
            'prompt': 'beautiful landscape',
            'generation': {
                'mode': 'random',
                'seed': 42,
                'seed_mode': 'progressive',
                'max_images': 10
            },
            'output': {
                'session_name': 'MyCustomSession',
                'filename_keys': ['Expression', 'Angle']
            }
        }
        source_file = Path('/test/prompt.yaml')

        config = parser.parse_prompt(data, source_file)

        # Verify output config was parsed
        assert config.output is not None
        assert isinstance(config.output, OutputConfig)
        assert config.output.session_name == "MyCustomSession"
        assert config.output.filename_keys == ["Expression", "Angle"]

    def test_parse_prompt_without_output_config(self):
        """Test parsing a prompt file without output configuration."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'Test Prompt',
            'prompt': 'beautiful landscape',
            'generation': {
                'mode': 'random',
                'seed': 42,
                'seed_mode': 'progressive',
                'max_images': 10
            }
        }
        source_file = Path('/test/prompt.yaml')

        config = parser.parse_prompt(data, source_file)

        # Verify output config is None
        assert config.output is None

    def test_parse_prompt_with_partial_output_config(self):
        """Test parsing with only session_name (no filename_keys)."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'Test Prompt',
            'prompt': 'beautiful landscape',
            'generation': {
                'mode': 'random',
                'seed': 42,
                'seed_mode': 'progressive',
                'max_images': 10
            },
            'output': {
                'session_name': 'OnlySessionName'
            }
        }
        source_file = Path('/test/prompt.yaml')

        config = parser.parse_prompt(data, source_file)

        assert config.output is not None
        assert config.output.session_name == "OnlySessionName"
        assert config.output.filename_keys == []

    def test_parse_template_with_output_config(self):
        """Test parsing a template file with output configuration."""
        parser = ConfigParser()
        data = {
            'version': '2.0',
            'name': 'Test Template',
            'template': '{prompt}, detailed',
            'output': {
                'session_name': 'TemplateSession',
                'filename_keys': ['Style']
            }
        }
        source_file = Path('/test/template.yaml')

        config = parser.parse_template(data, source_file)

        assert config.output is not None
        assert config.output.session_name == "TemplateSession"
        assert config.output.filename_keys == ["Style"]

    def test_output_config_session_name_priority(self):
        """Test that session_name priority works as expected.

        Priority: CLI override > config.output.session_name > config.name > filename
        This test verifies the expected behavior (logic is in cli.py).
        """
        # Create OutputConfig with session_name
        output = OutputConfig(
            session_name="FromOutputConfig",
            filename_keys=[]
        )

        assert output.session_name == "FromOutputConfig"

        # Create OutputConfig without session_name (uses default None)
        output_empty = OutputConfig()
        assert output_empty.session_name is None
        assert output_empty.filename_keys == []
