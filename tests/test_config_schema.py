"""
Tests for Configuration Schema (SF-1)
"""

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "CLI"))

from config.config_schema import (
    ModelConfig,
    PromptConfig,
    GenerationConfig,
    ParametersConfig,
    OutputConfig,
    GenerationSessionConfig,
    ValidationError,
    ValidationResult
)


# --- ModelConfig Tests ---

def test_model_config_defaults():
    """Test ModelConfig default values"""
    config = ModelConfig()
    assert config.checkpoint is None


def test_model_config_with_checkpoint():
    """Test ModelConfig with checkpoint"""
    config = ModelConfig(checkpoint="anime_v1.safetensors")
    assert config.checkpoint == "anime_v1.safetensors"


# --- PromptConfig Tests ---

def test_prompt_config_defaults():
    """Test PromptConfig default values"""
    config = PromptConfig()
    assert config.template == ""
    assert config.negative == ""


def test_prompt_config_with_values():
    """Test PromptConfig with values"""
    config = PromptConfig(
        template="masterpiece, {Expression}",
        negative="low quality"
    )
    assert config.template == "masterpiece, {Expression}"
    assert config.negative == "low quality"


# --- GenerationConfig Tests ---

def test_generation_config_defaults():
    """Test GenerationConfig default values"""
    config = GenerationConfig()
    assert config.mode == "combinatorial"
    assert config.seed_mode == "progressive"
    assert config.seed == 42
    assert config.max_images == -1


def test_generation_config_custom():
    """Test GenerationConfig with custom values"""
    config = GenerationConfig(
        mode="random",
        seed_mode="fixed",
        seed=1234,
        max_images=50
    )
    assert config.mode == "random"
    assert config.seed_mode == "fixed"
    assert config.seed == 1234
    assert config.max_images == 50


# --- ParametersConfig Tests ---

def test_parameters_config_defaults():
    """Test ParametersConfig default values"""
    config = ParametersConfig()
    assert config.width == 512
    assert config.height == 768
    assert config.steps == 30
    assert config.cfg_scale == 7.0
    assert config.sampler == "DPM++ 2M Karras"
    assert config.batch_size == 1
    assert config.batch_count == 1


def test_parameters_config_custom():
    """Test ParametersConfig with custom values"""
    config = ParametersConfig(
        width=1024,
        height=1024,
        steps=50,
        cfg_scale=9.5,
        sampler="Euler a",
        batch_size=4,
        batch_count=2
    )
    assert config.width == 1024
    assert config.height == 1024
    assert config.steps == 50
    assert config.cfg_scale == 9.5
    assert config.sampler == "Euler a"
    assert config.batch_size == 4
    assert config.batch_count == 2


# --- OutputConfig Tests ---

def test_output_config_defaults():
    """Test OutputConfig default values"""
    config = OutputConfig()
    assert config.session_name is None
    assert config.filename_keys == []


def test_output_config_with_values():
    """Test OutputConfig with values"""
    config = OutputConfig(
        session_name="anime_test",
        filename_keys=["Expression", "Angle"]
    )
    assert config.session_name == "anime_test"
    assert config.filename_keys == ["Expression", "Angle"]


# --- GenerationSessionConfig Tests ---

def test_session_config_defaults():
    """Test GenerationSessionConfig default values"""
    config = GenerationSessionConfig()
    assert config.version == "1.0"
    assert config.name == ""
    assert config.description == ""
    assert isinstance(config.model, ModelConfig)
    assert isinstance(config.prompt, PromptConfig)
    assert config.variations == {}
    assert isinstance(config.generation, GenerationConfig)
    assert isinstance(config.parameters, ParametersConfig)
    assert isinstance(config.output, OutputConfig)


def test_session_config_from_dict_minimal():
    """Test GenerationSessionConfig.from_dict with minimal data"""
    data = {
        "version": "1.0",
        "prompt": {
            "template": "test prompt"
        },
        "variations": {
            "Test": "/path/to/test.txt"
        }
    }

    config = GenerationSessionConfig.from_dict(data)

    assert config.version == "1.0"
    assert config.prompt.template == "test prompt"
    assert config.variations == {"Test": "/path/to/test.txt"}


def test_session_config_from_dict_complete():
    """Test GenerationSessionConfig.from_dict with complete data"""
    data = {
        "version": "1.0",
        "name": "Test Config",
        "description": "Test description",
        "model": {
            "checkpoint": "test.safetensors"
        },
        "prompt": {
            "template": "masterpiece, {Expression}",
            "negative": "low quality"
        },
        "variations": {
            "Expression": "/path/to/expressions.txt"
        },
        "generation": {
            "mode": "random",
            "seed_mode": "fixed",
            "seed": 999,
            "max_images": 25
        },
        "parameters": {
            "width": 1024,
            "height": 768,
            "steps": 40,
            "cfg_scale": 8.5,
            "sampler": "Euler a",
            "batch_size": 2,
            "batch_count": 3
        },
        "output": {
            "session_name": "test_session",
            "filename_keys": ["Expression"]
        }
    }

    config = GenerationSessionConfig.from_dict(data)

    assert config.version == "1.0"
    assert config.name == "Test Config"
    assert config.description == "Test description"
    assert config.model.checkpoint == "test.safetensors"
    assert config.prompt.template == "masterpiece, {Expression}"
    assert config.prompt.negative == "low quality"
    assert config.variations == {"Expression": "/path/to/expressions.txt"}
    assert config.generation.mode == "random"
    assert config.generation.seed_mode == "fixed"
    assert config.generation.seed == 999
    assert config.generation.max_images == 25
    assert config.parameters.width == 1024
    assert config.parameters.height == 768
    assert config.parameters.steps == 40
    assert config.parameters.cfg_scale == 8.5
    assert config.parameters.sampler == "Euler a"
    assert config.parameters.batch_size == 2
    assert config.parameters.batch_count == 3
    assert config.output.session_name == "test_session"
    assert config.output.filename_keys == ["Expression"]


def test_session_config_from_dict_partial():
    """Test GenerationSessionConfig.from_dict uses defaults for missing fields"""
    data = {
        "prompt": {
            "template": "test"
        },
        "variations": {}
    }

    config = GenerationSessionConfig.from_dict(data)

    # Should use defaults
    assert config.version == "1.0"
    assert config.generation.mode == "combinatorial"
    assert config.parameters.width == 512
    assert config.output.session_name is None


def test_session_config_to_dict():
    """Test GenerationSessionConfig.to_dict()"""
    config = GenerationSessionConfig(
        version="1.0",
        name="Test",
        description="Test desc",
        prompt=PromptConfig(template="test {Var}", negative="bad"),
        variations={"Var": "/path/to/var.txt"},
        output=OutputConfig(session_name="test_session", filename_keys=["Var"])
    )

    data = config.to_dict()

    assert data["version"] == "1.0"
    assert data["name"] == "Test"
    assert data["description"] == "Test desc"
    assert data["prompt"]["template"] == "test {Var}"
    assert data["prompt"]["negative"] == "bad"
    assert data["variations"] == {"Var": "/path/to/var.txt"}
    assert data["output"]["session_name"] == "test_session"
    assert data["output"]["filename_keys"] == ["Var"]


def test_session_config_roundtrip():
    """Test from_dict -> to_dict roundtrip preserves data"""
    original_data = {
        "version": "1.0",
        "name": "Roundtrip Test",
        "description": "Testing roundtrip",
        "model": {
            "checkpoint": "model.safetensors"
        },
        "prompt": {
            "template": "test {A}, {B}",
            "negative": "negative"
        },
        "variations": {
            "A": "/a.txt",
            "B": "/b.txt"
        },
        "generation": {
            "mode": "random",
            "seed_mode": "random",
            "seed": 123,
            "max_images": 10
        },
        "parameters": {
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7.5,
            "sampler": "DPM++ 2M",
            "batch_size": 1,
            "batch_count": 1
        },
        "output": {
            "session_name": "test",
            "filename_keys": ["A", "B"]
        }
    }

    config = GenerationSessionConfig.from_dict(original_data)
    reconstructed_data = config.to_dict()

    assert reconstructed_data == original_data


# --- ValidationError Tests ---

def test_validation_error_basic():
    """Test ValidationError creation"""
    error = ValidationError("field.name", "Error message")
    assert error.field == "field.name"
    assert error.message == "Error message"
    assert error.suggestion is None


def test_validation_error_with_suggestion():
    """Test ValidationError with suggestion"""
    error = ValidationError(
        "field.name",
        "Error message",
        "Try this instead"
    )
    assert error.field == "field.name"
    assert error.message == "Error message"
    assert error.suggestion == "Try this instead"


def test_validation_error_str():
    """Test ValidationError string formatting"""
    error = ValidationError("test.field", "Something wrong")
    assert str(error) == "test.field: Something wrong"


def test_validation_error_str_with_suggestion():
    """Test ValidationError string formatting with suggestion"""
    error = ValidationError("test.field", "Something wrong", "Fix it like this")
    result = str(error)
    assert "test.field: Something wrong" in result
    assert "→ Fix it like this" in result


# --- ValidationResult Tests ---

def test_validation_result_empty():
    """Test empty ValidationResult is valid"""
    result = ValidationResult()
    assert result.is_valid
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_validation_result_add_error():
    """Test adding error to ValidationResult"""
    result = ValidationResult()
    result.add_error("field", "error message")

    assert not result.is_valid
    assert len(result.errors) == 1
    assert result.errors[0].field == "field"
    assert result.errors[0].message == "error message"


def test_validation_result_add_warning():
    """Test adding warning to ValidationResult"""
    result = ValidationResult()
    result.add_warning("field", "warning message")

    assert result.is_valid  # Warnings don't affect validity
    assert len(result.warnings) == 1
    assert result.warnings[0].field == "field"
    assert result.warnings[0].message == "warning message"


def test_validation_result_multiple_errors():
    """Test multiple errors"""
    result = ValidationResult()
    result.add_error("field1", "error 1")
    result.add_error("field2", "error 2", "suggestion 2")

    assert not result.is_valid
    assert len(result.errors) == 2
    assert result.errors[0].field == "field1"
    assert result.errors[1].field == "field2"
    assert result.errors[1].suggestion == "suggestion 2"


def test_validation_result_get_error_messages():
    """Test get_error_messages()"""
    result = ValidationResult()
    result.add_error("field1", "error 1")
    result.add_error("field2", "error 2", "fix this")

    messages = result.get_error_messages()
    assert len(messages) == 2
    assert "field1: error 1" in messages[0]
    assert "field2: error 2" in messages[1]


def test_validation_result_get_warning_messages():
    """Test get_warning_messages()"""
    result = ValidationResult()
    result.add_warning("field1", "warning 1")
    result.add_warning("field2", "warning 2")

    messages = result.get_warning_messages()
    assert len(messages) == 2


def test_validation_result_str_with_errors():
    """Test ValidationResult string formatting with errors"""
    result = ValidationResult()
    result.add_error("field1", "error 1")
    result.add_error("field2", "error 2")

    output = str(result)
    assert "Validation Errors:" in output
    assert "field1" in output
    assert "field2" in output


def test_validation_result_str_with_warnings():
    """Test ValidationResult string formatting with warnings"""
    result = ValidationResult()
    result.add_warning("field1", "warning 1")

    output = str(result)
    assert "Warnings:" in output
    assert "field1" in output


def test_validation_result_str_with_both():
    """Test ValidationResult string formatting with both errors and warnings"""
    result = ValidationResult()
    result.add_error("field1", "error 1")
    result.add_warning("field2", "warning 1")

    output = str(result)
    assert "Validation Errors:" in output
    assert "Warnings:" in output
    assert "field1" in output
    assert "field2" in output
