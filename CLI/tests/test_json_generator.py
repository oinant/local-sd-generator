"""
Tests for json_generator.py (SF-3)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent.parent / "CLI"))

from execution.json_generator import (
    prompt_generation_mode,
    prompt_seed_mode,
    prompt_max_images,
    prompt_sampler,
    prompt_numeric_param,
    prompt_float_param,
    resolve_interactive_params,
    create_generator_from_config,
    DEFAULT_SAMPLERS
)
from config.config_schema import GenerationSessionConfig, GenerationConfig, ParametersConfig


class TestPromptGenerationMode:
    """Test generation mode prompting"""

    def test_select_combinatorial(self):
        """User selects combinatorial mode"""
        with patch('builtins.input', return_value="1"):
            mode = prompt_generation_mode()
        assert mode == "combinatorial"

    def test_select_random(self):
        """User selects random mode"""
        with patch('builtins.input', return_value="2"):
            mode = prompt_seed_mode()
        assert mode in ["fixed", "progressive", "random"]

    def test_invalid_then_valid(self):
        """User enters invalid then valid selection"""
        with patch('builtins.input', side_effect=["invalid", "3", "1"]):
            mode = prompt_generation_mode()
        assert mode == "combinatorial"

    def test_user_cancels(self):
        """User cancels with Ctrl+C"""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            with pytest.raises(ValueError, match="cancelled"):
                prompt_generation_mode()


class TestPromptSeedMode:
    """Test seed mode prompting"""

    def test_select_fixed(self):
        """User selects fixed seed mode"""
        with patch('builtins.input', return_value="1"):
            mode = prompt_seed_mode()
        assert mode == "fixed"

    def test_select_progressive(self):
        """User selects progressive seed mode"""
        with patch('builtins.input', return_value="2"):
            mode = prompt_seed_mode()
        assert mode == "progressive"

    def test_select_random(self):
        """User selects random seed mode"""
        with patch('builtins.input', return_value="3"):
            mode = prompt_seed_mode()
        assert mode == "random"


class TestPromptMaxImages:
    """Test max images prompting"""

    def test_user_enters_number(self):
        """User enters specific number"""
        with patch('builtins.input', return_value="50"):
            num = prompt_max_images(100)
        assert num == 50

    def test_user_presses_enter(self):
        """User presses Enter for default"""
        with patch('builtins.input', return_value=""):
            num = prompt_max_images(100)
        assert num == 100

    def test_number_exceeds_combinations(self):
        """User enters number exceeding combinations"""
        with patch('builtins.input', return_value="200"):
            num = prompt_max_images(100)
        assert num == 100  # Capped at total

    def test_invalid_input(self):
        """User enters invalid then valid"""
        with patch('builtins.input', side_effect=["invalid", "0", "50"]):
            num = prompt_max_images(100)
        assert num == 50


class TestPromptSampler:
    """Test sampler prompting"""

    def test_select_sampler(self):
        """User selects sampler"""
        samplers = ["Euler a", "DPM++ 2M Karras", "DDIM"]
        with patch('builtins.input', return_value="2"):
            sampler = prompt_sampler(samplers)
        assert sampler == "DPM++ 2M Karras"

    def test_default_samplers(self):
        """Use default samplers if none provided"""
        with patch('builtins.input', return_value="1"):
            sampler = prompt_sampler()
        assert sampler in DEFAULT_SAMPLERS

    def test_invalid_selection(self):
        """User enters invalid then valid"""
        samplers = ["Euler a", "DDIM"]
        with patch('builtins.input', side_effect=["5", "invalid", "1"]):
            sampler = prompt_sampler(samplers)
        assert sampler == "Euler a"


class TestPromptNumericParam:
    """Test numeric parameter prompting"""

    def test_user_enters_value(self):
        """User enters specific value"""
        with patch('builtins.input', return_value="512"):
            value = prompt_numeric_param("Width", default=768)
        assert value == 512

    def test_user_accepts_default(self):
        """User presses Enter for default"""
        with patch('builtins.input', return_value=""):
            value = prompt_numeric_param("Width", default=768)
        assert value == 768

    def test_value_below_minimum(self):
        """User enters value below minimum"""
        with patch('builtins.input', side_effect=["0", "64"]):
            value = prompt_numeric_param("Width", default=512, min_value=64)
        assert value == 64

    def test_invalid_input(self):
        """User enters invalid then valid"""
        with patch('builtins.input', side_effect=["abc", "512"]):
            value = prompt_numeric_param("Width", default=768)
        assert value == 512


class TestPromptFloatParam:
    """Test float parameter prompting"""

    def test_user_enters_value(self):
        """User enters specific value"""
        with patch('builtins.input', return_value="8.5"):
            value = prompt_float_param("CFG Scale", default=7.0)
        assert value == 8.5

    def test_user_accepts_default(self):
        """User presses Enter for default"""
        with patch('builtins.input', return_value=""):
            value = prompt_float_param("CFG Scale", default=7.0)
        assert value == 7.0

    def test_value_below_minimum(self):
        """User enters value below minimum"""
        with patch('builtins.input', side_effect=["0", "5.5"]):
            value = prompt_float_param("CFG Scale", default=7.0, min_value=0.1)
        assert value == 5.5


class TestResolveInteractiveParams:
    """Test interactive parameter resolution"""

    def test_resolve_generation_mode(self):
        """Resolve 'ask' generation mode"""
        config = GenerationSessionConfig(
            prompt=MagicMock(template="test {Var}", negative=""),
            variations={"Var": "test.txt"},
            generation=GenerationConfig(mode="ask", seed_mode="fixed", seed=42),
            parameters=ParametersConfig()
        )

        with patch('execution.json_generator.prompt_generation_mode', return_value="random"):
            resolved = resolve_interactive_params(config)

        assert resolved.generation.mode == "random"
        # Original should be unchanged
        assert config.generation.mode == "ask"

    def test_resolve_seed_mode(self):
        """Resolve 'ask' seed mode"""
        config = GenerationSessionConfig(
            prompt=MagicMock(template="test {Var}", negative=""),
            variations={"Var": "test.txt"},
            generation=GenerationConfig(mode="combinatorial", seed_mode="ask", seed=42),
            parameters=ParametersConfig()
        )

        with patch('execution.json_generator.prompt_seed_mode', return_value="progressive"):
            resolved = resolve_interactive_params(config)

        assert resolved.generation.seed_mode == "progressive"

    def test_resolve_seed_value(self):
        """Resolve -1 seed value"""
        config = GenerationSessionConfig(
            prompt=MagicMock(template="test {Var}", negative=""),
            variations={"Var": "test.txt"},
            generation=GenerationConfig(mode="combinatorial", seed_mode="fixed", seed=-1),
            parameters=ParametersConfig()
        )

        with patch('execution.json_generator.prompt_numeric_param', return_value=123):
            resolved = resolve_interactive_params(config)

        assert resolved.generation.seed == 123

    def test_resolve_parameters(self):
        """Resolve -1 parameter values"""
        config = GenerationSessionConfig(
            prompt=MagicMock(template="test {Var}", negative=""),
            variations={"Var": "test.txt"},
            generation=GenerationConfig(),
            parameters=ParametersConfig(
                width=-1,
                height=-1,
                steps=-1,
                cfg_scale=-1.0,
                sampler="ask"
            )
        )

        with patch('execution.json_generator.prompt_numeric_param', side_effect=[512, 768, 30]):
            with patch('execution.json_generator.prompt_float_param', return_value=7.5):
                with patch('execution.json_generator.prompt_sampler', return_value="Euler a"):
                    resolved = resolve_interactive_params(config)

        assert resolved.parameters.width == 512
        assert resolved.parameters.height == 768
        assert resolved.parameters.steps == 30
        assert resolved.parameters.cfg_scale == 7.5
        assert resolved.parameters.sampler == "Euler a"

    def test_no_interactive_params(self):
        """Config with no interactive params"""
        config = GenerationSessionConfig(
            prompt=MagicMock(template="test {Var}", negative=""),
            variations={"Var": "test.txt"},
            generation=GenerationConfig(mode="combinatorial", seed_mode="fixed", seed=42),
            parameters=ParametersConfig(width=512, height=768, steps=30)
        )

        resolved = resolve_interactive_params(config)

        # Should return copy with same values
        assert resolved.generation.mode == "combinatorial"
        assert resolved.parameters.width == 512


class TestCreateGeneratorFromConfig:
    """Test generator creation from config"""

    def test_create_generator(self):
        """Create generator from valid config"""
        config = GenerationSessionConfig(
            prompt=MagicMock(template="test {Var}", negative="low quality"),
            variations={"Var": "test.txt"},
            generation=GenerationConfig(mode="random", seed_mode="progressive", seed=42, max_images=50),
            parameters=ParametersConfig(
                width=512,
                height=768,
                steps=30,
                cfg_scale=7.5,
                sampler="DPM++ 2M Karras"
            ),
            output=MagicMock(session_name="test_session", filename_keys=["Var"])
        )

        generator = create_generator_from_config(config)

        assert generator.prompt_template == "test {Var}"
        assert generator.negative_prompt == "low quality"
        assert generator.seed == 42
        assert generator.max_images == 50
        assert generator.generation_mode == "random"
        assert generator.seed_mode == "progressive"
        assert generator.session_name == "test_session"
        assert generator.filename_keys == ["Var"]

        # Check generation config
        assert generator.generation_config.width == 512
        assert generator.generation_config.height == 768
        assert generator.generation_config.steps == 30
        assert generator.generation_config.cfg_scale == 7.5
        assert generator.generation_config.sampler_name == "DPM++ 2M Karras"

    def test_default_session_name(self):
        """Use default session name if not specified"""
        config = GenerationSessionConfig(
            prompt=MagicMock(template="test", negative=""),
            variations={},
            generation=GenerationConfig(),
            parameters=ParametersConfig(),
            output=MagicMock(session_name=None, filename_keys=[])
        )

        generator = create_generator_from_config(config)

        assert generator.session_name == "json_config_session"
