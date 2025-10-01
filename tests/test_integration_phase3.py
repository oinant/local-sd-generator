"""
Integration Tests for Phase 3 - JSON Config Execution System

Tests the complete flow: config selection → validation → execution
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "CLI"))

from config.config_selector import discover_configs, select_config_interactive
from execution.json_generator import (
    resolve_interactive_params,
    create_generator_from_config,
    run_generation_from_config
)
from config.config_schema import GenerationSessionConfig


class TestConfigSelectionFlow:
    """Test config discovery and selection flow"""

    def test_discover_and_select(self, tmp_path):
        """Test complete discovery and selection"""
        # Create test configs
        config1 = tmp_path / "test1.json"
        config1.write_text(json.dumps({
            "version": "1.0",
            "name": "Test Config 1",
            "description": "First test",
            "prompt": {"template": "test {Var}"},
            "variations": {"Var": "test.txt"}
        }))

        config2 = tmp_path / "test2.json"
        config2.write_text(json.dumps({
            "version": "1.0",
            "name": "Test Config 2",
            "description": "Second test",
            "prompt": {"template": "test {Var}"},
            "variations": {"Var": "test.txt"}
        }))

        # Discover
        configs = discover_configs(tmp_path)
        assert len(configs) == 2

        # Mock user selecting config 2
        with patch('builtins.input', return_value="2"):
            selected = select_config_interactive(tmp_path)

        assert selected.name == "test2.json"


class TestInteractiveResolutionFlow:
    """Test interactive parameter resolution flow"""

    def test_resolve_all_interactive_params(self):
        """Test resolving all 'ask' and -1 parameters"""
        config_dict = {
            "version": "1.0",
            "prompt": {
                "template": "test {Var}",
                "negative": "bad"
            },
            "variations": {
                "Var": "test.txt"
            },
            "generation": {
                "mode": "ask",
                "seed_mode": "ask",
                "seed": -1,
                "max_images": -1
            },
            "parameters": {
                "width": -1,
                "height": -1,
                "steps": -1,
                "cfg_scale": -1.0,
                "sampler": "ask",
                "batch_size": 1,
                "batch_count": 1
            }
        }

        config = GenerationSessionConfig.from_dict(config_dict)

        # Mock all interactive prompts
        with patch('execution.json_generator.prompt_generation_mode', return_value="random"):
            with patch('execution.json_generator.prompt_seed_mode', return_value="progressive"):
                with patch('execution.json_generator.prompt_numeric_param', side_effect=[42, 512, 768, 30]):
                    with patch('execution.json_generator.prompt_float_param', return_value=7.5):
                        with patch('execution.json_generator.prompt_sampler', return_value="Euler a"):
                            resolved = resolve_interactive_params(config)

        # Verify all resolved
        assert resolved.generation.mode == "random"
        assert resolved.generation.seed_mode == "progressive"
        assert resolved.generation.seed == 42
        assert resolved.parameters.width == 512
        assert resolved.parameters.height == 768
        assert resolved.parameters.steps == 30
        assert resolved.parameters.cfg_scale == 7.5
        assert resolved.parameters.sampler == "Euler a"

    def test_resolve_partial_interactive_params(self):
        """Test resolving only some interactive params"""
        config_dict = {
            "version": "1.0",
            "prompt": {
                "template": "test {Var}",
                "negative": "bad"
            },
            "variations": {
                "Var": "test.txt"
            },
            "generation": {
                "mode": "combinatorial",  # Not 'ask'
                "seed_mode": "ask",        # Ask
                "seed": 42,                 # Fixed
                "max_images": 50            # Fixed
            },
            "parameters": {
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.0,
                "sampler": "ask",  # Ask
                "batch_size": 1,
                "batch_count": 1
            }
        }

        config = GenerationSessionConfig.from_dict(config_dict)

        with patch('execution.json_generator.prompt_seed_mode', return_value="fixed"):
            with patch('execution.json_generator.prompt_sampler', return_value="DPM++ 2M"):
                resolved = resolve_interactive_params(config)

        # Verify only 'ask' params were changed
        assert resolved.generation.mode == "combinatorial"  # Unchanged
        assert resolved.generation.seed_mode == "fixed"      # Changed
        assert resolved.generation.seed == 42                 # Unchanged
        assert resolved.parameters.sampler == "DPM++ 2M"     # Changed
        assert resolved.parameters.width == 512              # Unchanged


class TestGeneratorCreationFlow:
    """Test generator creation from config"""

    def test_create_generator_with_all_params(self):
        """Test creating generator with complete config"""
        config_dict = {
            "version": "1.0",
            "name": "Test Config",
            "prompt": {
                "template": "beautiful {Subject}, {Style}",
                "negative": "low quality"
            },
            "variations": {
                "Subject": "/path/to/subjects.txt",
                "Style": "/path/to/styles.txt"
            },
            "generation": {
                "mode": "random",
                "seed_mode": "progressive",
                "seed": 123,
                "max_images": 100
            },
            "parameters": {
                "width": 768,
                "height": 512,
                "steps": 25,
                "cfg_scale": 8.0,
                "sampler": "Euler a",
                "batch_size": 2,
                "batch_count": 1
            },
            "output": {
                "session_name": "test_session",
                "filename_keys": ["Subject", "Style"]
            }
        }

        config = GenerationSessionConfig.from_dict(config_dict)
        generator = create_generator_from_config(config)

        # Verify generator params
        assert generator.prompt_template == "beautiful {Subject}, {Style}"
        assert generator.negative_prompt == "low quality"
        assert generator.seed == 123
        assert generator.max_images == 100
        assert generator.generation_mode == "random"
        assert generator.seed_mode == "progressive"
        assert generator.session_name == "test_session"
        assert generator.filename_keys == ["Subject", "Style"]

        # Verify generation config
        assert generator.generation_config.width == 768
        assert generator.generation_config.height == 512
        assert generator.generation_config.steps == 25
        assert generator.generation_config.cfg_scale == 8.0
        assert generator.generation_config.sampler_name == "Euler a"
        assert generator.generation_config.batch_size == 2


class TestEndToEndConfigExecution:
    """Test complete config-to-generation flow (mocked API)"""

    def test_complete_flow_with_valid_config(self, tmp_path):
        """Test full execution with valid config (mocked generation)"""
        # Create variation files
        subjects_file = tmp_path / "subjects.txt"
        subjects_file.write_text("girl\nboy\ncat")

        styles_file = tmp_path / "styles.txt"
        styles_file.write_text("anime\nrealistic")

        # Create config
        config_file = tmp_path / "test_config.json"
        config_data = {
            "version": "1.0",
            "name": "Integration Test",
            "description": "Test config for integration testing",
            "prompt": {
                "template": "{Subject}, {Style}",
                "negative": "bad"
            },
            "variations": {
                "Subject": str(subjects_file),
                "Style": str(styles_file)
            },
            "generation": {
                "mode": "combinatorial",
                "seed_mode": "fixed",
                "seed": 42,
                "max_images": 6  # 3 subjects × 2 styles = 6
            },
            "parameters": {
                "width": 512,
                "height": 512,
                "steps": 20,
                "cfg_scale": 7.0,
                "sampler": "Euler a",
                "batch_size": 1,
                "batch_count": 1
            },
            "output": {
                "session_name": "integration_test",
                "filename_keys": ["Subject", "Style"]
            }
        }
        config_file.write_text(json.dumps(config_data, indent=2))

        # Mock the generator's run method
        mock_generator = MagicMock()
        mock_generator.run.return_value = (6, 6)  # 6 success, 6 total
        mock_generator.session_name = "integration_test"
        mock_generator.start_time = None
        mock_generator.end_time = None

        with patch('execution.json_generator.create_generator_from_config', return_value=mock_generator):
            result = run_generation_from_config(config_file)

        # Verify result
        assert result["success_count"] == 6
        assert result["total_count"] == 6
        assert result["session_name"] == "integration_test"
        assert result["config_name"] == "Integration Test"

        # Verify generator was called
        mock_generator.run.assert_called_once()

    def test_flow_with_interactive_params(self, tmp_path):
        """Test flow with interactive parameter resolution"""
        # Create variation file
        vars_file = tmp_path / "vars.txt"
        vars_file.write_text("option1\noption2")

        # Create config with interactive params
        config_file = tmp_path / "interactive_config.json"
        config_data = {
            "version": "1.0",
            "name": "Interactive Test",
            "prompt": {
                "template": "{Option}",
                "negative": "bad"
            },
            "variations": {
                "Option": str(vars_file)
            },
            "generation": {
                "mode": "ask",
                "seed_mode": "ask",
                "seed": 42,
                "max_images": -1
            },
            "parameters": {
                "width": 512,
                "height": 512,
                "steps": 20,
                "cfg_scale": 7.0,
                "sampler": "Euler a",
                "batch_size": 1,
                "batch_count": 1
            },
            "output": {
                "session_name": "interactive_test"
            }
        }
        config_file.write_text(json.dumps(config_data, indent=2))

        # Mock interactive prompts
        mock_generator = MagicMock()
        mock_generator.run.return_value = (2, 2)
        mock_generator.session_name = "interactive_test"
        mock_generator.start_time = None
        mock_generator.end_time = None

        with patch('execution.json_generator.prompt_generation_mode', return_value="combinatorial"):
            with patch('execution.json_generator.prompt_seed_mode', return_value="progressive"):
                with patch('execution.json_generator.prompt_max_images', return_value=2):
                    with patch('execution.json_generator.create_generator_from_config', return_value=mock_generator):
                        result = run_generation_from_config(config_file)

        assert result["success_count"] == 2
        assert result["total_count"] == 2

    def test_flow_with_invalid_config(self, tmp_path):
        """Test flow fails gracefully with invalid config"""
        # Create config with missing required field
        config_file = tmp_path / "invalid_config.json"
        config_data = {
            "version": "1.0",
            # Missing prompt.template
            "variations": {}
        }
        config_file.write_text(json.dumps(config_data, indent=2))

        # Should raise ValueError during validation
        with pytest.raises(ValueError, match="validation failed"):
            run_generation_from_config(config_file)

    def test_flow_with_missing_variation_file(self, tmp_path):
        """Test flow fails with missing variation file"""
        config_file = tmp_path / "config.json"
        config_data = {
            "version": "1.0",
            "prompt": {
                "template": "{Missing}"
            },
            "variations": {
                "Missing": "/nonexistent/file.txt"
            },
            "generation": {
                "mode": "combinatorial",
                "seed_mode": "fixed",
                "seed": 42
            },
            "parameters": {
                "width": 512,
                "height": 512,
                "steps": 20,
                "cfg_scale": 7.0,
                "sampler": "Euler a"
            }
        }
        config_file.write_text(json.dumps(config_data, indent=2))

        # Should fail validation
        with pytest.raises(ValueError, match="validation failed"):
            run_generation_from_config(config_file)


class TestCLIIntegration:
    """Test CLI entry point integration (without actual execution)"""

    def test_cli_help(self):
        """Test CLI help message"""
        from generator_cli import parse_arguments

        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.argv', ['generator_cli.py', '--help']):
                parse_arguments()

        assert exc_info.value.code == 0

    def test_cli_argument_parsing(self):
        """Test CLI argument parsing"""
        from generator_cli import parse_arguments

        # Test --config
        with patch('sys.argv', ['generator_cli.py', '--config', 'test.json']):
            args = parse_arguments()
            assert args.config == Path('test.json')

        # Test --list
        with patch('sys.argv', ['generator_cli.py', '--list']):
            args = parse_arguments()
            assert args.list is True

        # Test --api-url
        with patch('sys.argv', ['generator_cli.py', '--api-url', 'http://localhost:8000']):
            args = parse_arguments()
            assert args.api_url == 'http://localhost:8000'
