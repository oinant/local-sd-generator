"""
Tests for Configuration Loader & Validator (SF-1)
"""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_loader import (
    load_config_from_file,
    validate_required_fields,
    validate_field_types,
    validate_variation_files,
    validate_placeholders_match,
    validate_filename_keys,
    validate_sampler,
    validate_config,
    load_and_validate_config
)
from config.config_schema import (
    GenerationSessionConfig,
    PromptConfig,
    GenerationConfig,
    ParametersConfig,
    OutputConfig,
    ValidationResult
)


# --- Fixtures ---

@pytest.fixture
def valid_config_data():
    """Valid configuration data"""
    return {
        "version": "1.0",
        "name": "Test Config",
        "description": "Test description",
        "prompt": {
            "template": "masterpiece, {Expression}, beautiful",
            "negative": "low quality"
        },
        "variations": {
            "Expression": "/tmp/expressions.txt"
        },
        "generation": {
            "mode": "combinatorial",
            "seed_mode": "progressive",
            "seed": 42,
            "max_images": 10
        },
        "parameters": {
            "width": 512,
            "height": 768,
            "steps": 30,
            "cfg_scale": 7.0,
            "sampler": "DPM++ 2M Karras",
            "batch_size": 1,
            "batch_count": 1
        },
        "output": {
            "session_name": "test_session",
            "filename_keys": ["Expression"]
        }
    }


@pytest.fixture
def temp_config_file(tmp_path, valid_config_data):
    """Create a temporary config file"""
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(valid_config_data, indent=2))
    return config_file


@pytest.fixture
def temp_variation_file(tmp_path):
    """Create a temporary variation file"""
    var_file = tmp_path / "variations.txt"
    var_file.write_text("happy\nsad\nangry\n")
    return var_file


# --- load_config_from_file Tests ---

def test_load_config_from_file_success(temp_config_file):
    """Test loading valid config file"""
    config = load_config_from_file(temp_config_file)

    assert isinstance(config, GenerationSessionConfig)
    assert config.version == "1.0"
    assert config.name == "Test Config"
    assert config.prompt.template == "masterpiece, {Expression}, beautiful"


def test_load_config_from_file_not_found():
    """Test loading non-existent file raises FileNotFoundError"""
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config_from_file(Path("/nonexistent/config.json"))


def test_load_config_from_file_invalid_json(tmp_path):
    """Test loading invalid JSON raises ValueError"""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ invalid json }")

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_config_from_file(bad_file)


# --- validate_required_fields Tests ---

def test_validate_required_fields_valid():
    """Test validation passes for valid config"""
    config = GenerationSessionConfig(
        version="1.0",
        prompt=PromptConfig(template="test {Var}"),
        variations={"Var": "/path/to/var.txt"}
    )
    result = ValidationResult()

    validate_required_fields(config, result)

    assert result.is_valid


def test_validate_required_fields_missing_version():
    """Test validation fails when version is missing"""
    config = GenerationSessionConfig(
        version="",  # Empty version
        prompt=PromptConfig(template="test"),
        variations={"Var": "/path"}
    )
    result = ValidationResult()

    validate_required_fields(config, result)

    assert not result.is_valid
    assert any("version" in err.field.lower() for err in result.errors)


def test_validate_required_fields_missing_template():
    """Test validation fails when template is missing"""
    config = GenerationSessionConfig(
        version="1.0",
        prompt=PromptConfig(template=""),  # Empty template
        variations={"Var": "/path"}
    )
    result = ValidationResult()

    validate_required_fields(config, result)

    assert not result.is_valid
    assert any("template" in err.field.lower() for err in result.errors)


def test_validate_required_fields_missing_variations():
    """Test validation fails when variations are missing"""
    config = GenerationSessionConfig(
        version="1.0",
        prompt=PromptConfig(template="test"),
        variations={}  # Empty variations
    )
    result = ValidationResult()

    validate_required_fields(config, result)

    assert not result.is_valid
    assert any("variation" in err.field.lower() for err in result.errors)


# --- validate_field_types Tests ---

def test_validate_field_types_valid():
    """Test validation passes for valid field types"""
    config = GenerationSessionConfig()
    result = ValidationResult()

    validate_field_types(config, result)

    assert result.is_valid


def test_validate_field_types_invalid_generation_mode():
    """Test validation fails for invalid generation mode"""
    config = GenerationSessionConfig(
        generation=GenerationConfig(mode="invalid_mode")
    )
    result = ValidationResult()

    validate_field_types(config, result)

    assert not result.is_valid
    assert any("generation.mode" in err.field for err in result.errors)


def test_validate_field_types_invalid_seed_mode():
    """Test validation fails for invalid seed mode"""
    config = GenerationSessionConfig(
        generation=GenerationConfig(seed_mode="invalid_seed_mode")
    )
    result = ValidationResult()

    validate_field_types(config, result)

    assert not result.is_valid
    assert any("generation.seed_mode" in err.field for err in result.errors)


def test_validate_field_types_negative_width():
    """Test validation fails for negative width (not -1)"""
    config = GenerationSessionConfig(
        parameters=ParametersConfig(width=-5)
    )
    result = ValidationResult()

    validate_field_types(config, result)

    assert not result.is_valid
    assert any("width" in err.field.lower() for err in result.errors)


def test_validate_field_types_ask_value_allowed():
    """Test validation allows -1 (ask) for numeric parameters"""
    config = GenerationSessionConfig(
        parameters=ParametersConfig(
            width=-1,
            height=-1,
            steps=-1,
            cfg_scale=-1.0,
            batch_size=-1,
            batch_count=-1
        )
    )
    result = ValidationResult()

    validate_field_types(config, result)

    # Should be valid (no errors about these fields)
    numeric_errors = [err for err in result.errors
                      if any(field in err.field for field in
                             ["width", "height", "steps", "cfg_scale", "batch_size", "batch_count"])]
    assert len(numeric_errors) == 0


# --- validate_variation_files Tests ---

def test_validate_variation_files_valid(tmp_path):
    """Test validation passes for existing files"""
    var_file = tmp_path / "test.txt"
    var_file.write_text("test")

    config = GenerationSessionConfig(
        variations={"Test": str(var_file)}
    )
    result = ValidationResult()

    validate_variation_files(config, result)

    assert result.is_valid


def test_validate_variation_files_missing_file():
    """Test validation fails for missing file"""
    config = GenerationSessionConfig(
        variations={"Test": "/nonexistent/file.txt"}
    )
    result = ValidationResult()

    validate_variation_files(config, result)

    assert not result.is_valid
    assert any("not found" in err.message.lower() for err in result.errors)


def test_validate_variation_files_is_directory(tmp_path):
    """Test validation fails when path is directory"""
    directory = tmp_path / "not_a_file"
    directory.mkdir()

    config = GenerationSessionConfig(
        variations={"Test": str(directory)}
    )
    result = ValidationResult()

    validate_variation_files(config, result)

    assert not result.is_valid
    assert any("not a file" in err.message.lower() for err in result.errors)


def test_validate_variation_files_multiple_files(tmp_path):
    """Test validation with multiple variation files"""
    file1 = tmp_path / "var1.txt"
    file2 = tmp_path / "var2.txt"
    file1.write_text("test1")
    file2.write_text("test2")

    config = GenerationSessionConfig(
        variations={
            "Var1": str(file1),
            "Var2": str(file2)
        }
    )
    result = ValidationResult()

    validate_variation_files(config, result)

    assert result.is_valid


# --- validate_placeholders_match Tests ---

def test_validate_placeholders_match_valid(tmp_path):
    """Test validation passes when placeholders match variations"""
    config = GenerationSessionConfig(
        prompt=PromptConfig(template="test {Expr}, {Angle}"),
        variations={
            "Expr": "/path/expr.txt",
            "Angle": "/path/angle.txt"
        }
    )
    result = ValidationResult()

    validate_placeholders_match(config, result)

    # Should have no errors, only possibly warnings
    assert result.is_valid


def test_validate_placeholders_match_missing_variation():
    """Test validation fails when placeholder has no variation"""
    config = GenerationSessionConfig(
        prompt=PromptConfig(template="test {Expression}, {Missing}"),
        variations={
            "Expression": "/path/expr.txt"
        }
    )
    result = ValidationResult()

    validate_placeholders_match(config, result)

    assert not result.is_valid
    assert any("Missing" in err.field for err in result.errors)


def test_validate_placeholders_match_unused_variation():
    """Test validation warns when variation is unused"""
    config = GenerationSessionConfig(
        prompt=PromptConfig(template="test {Expression}"),
        variations={
            "Expression": "/path/expr.txt",
            "Unused": "/path/unused.txt"
        }
    )
    result = ValidationResult()

    validate_placeholders_match(config, result)

    assert result.is_valid  # Just warning
    assert any("Unused" in warn.field for warn in result.warnings)


def test_validate_placeholders_match_no_placeholders():
    """Test validation when prompt has no placeholders"""
    config = GenerationSessionConfig(
        prompt=PromptConfig(template="static prompt, no placeholders"),
        variations={
            "SomeVar": "/path/var.txt"
        }
    )
    result = ValidationResult()

    validate_placeholders_match(config, result)

    # Should warn about unused variation
    assert len(result.warnings) > 0


# --- validate_filename_keys Tests ---

def test_validate_filename_keys_valid():
    """Test validation passes for valid filename_keys"""
    config = GenerationSessionConfig(
        variations={
            "Expression": "/path/expr.txt",
            "Angle": "/path/angle.txt"
        },
        output=OutputConfig(filename_keys=["Expression", "Angle"])
    )
    result = ValidationResult()

    validate_filename_keys(config, result)

    assert result.is_valid


def test_validate_filename_keys_empty():
    """Test validation passes for empty filename_keys"""
    config = GenerationSessionConfig(
        variations={"Test": "/path/test.txt"},
        output=OutputConfig(filename_keys=[])
    )
    result = ValidationResult()

    validate_filename_keys(config, result)

    assert result.is_valid


def test_validate_filename_keys_invalid_key():
    """Test validation fails when filename_key not in variations"""
    config = GenerationSessionConfig(
        variations={"Expression": "/path/expr.txt"},
        output=OutputConfig(filename_keys=["Expression", "InvalidKey"])
    )
    result = ValidationResult()

    validate_filename_keys(config, result)

    assert not result.is_valid
    assert any("InvalidKey" in err.message for err in result.errors)


# --- validate_sampler Tests ---

def test_validate_sampler_ask_mode():
    """Test validation passes for 'ask' sampler"""
    config = GenerationSessionConfig(
        parameters=ParametersConfig(sampler="ask")
    )
    result = ValidationResult()

    validate_sampler(config, result)

    assert result.is_valid


def test_validate_sampler_no_api_list():
    """Test validation passes when no API sampler list provided"""
    config = GenerationSessionConfig(
        parameters=ParametersConfig(sampler="DPM++ 2M Karras")
    )
    result = ValidationResult()

    validate_sampler(config, result, available_samplers=None)

    assert result.is_valid


def test_validate_sampler_valid_sampler():
    """Test validation passes for valid sampler from API"""
    config = GenerationSessionConfig(
        parameters=ParametersConfig(sampler="Euler a")
    )
    result = ValidationResult()
    available = ["Euler a", "DPM++ 2M Karras", "DDIM"]

    validate_sampler(config, result, available_samplers=available)

    assert result.is_valid


def test_validate_sampler_invalid_sampler():
    """Test validation fails for invalid sampler"""
    config = GenerationSessionConfig(
        parameters=ParametersConfig(sampler="NonExistentSampler")
    )
    result = ValidationResult()
    available = ["Euler a", "DPM++ 2M Karras", "DDIM"]

    validate_sampler(config, result, available_samplers=available)

    assert not result.is_valid
    assert any("sampler" in err.field.lower() for err in result.errors)


# --- validate_config Tests ---

def test_validate_config_complete_valid(tmp_path):
    """Test complete validation of valid config"""
    var_file = tmp_path / "test.txt"
    var_file.write_text("test")

    config = GenerationSessionConfig(
        version="1.0",
        prompt=PromptConfig(template="test {Var}"),
        variations={"Var": str(var_file)},
        generation=GenerationConfig(mode="combinatorial", seed_mode="progressive"),
        output=OutputConfig(filename_keys=["Var"])
    )

    result = validate_config(config)

    assert result.is_valid


def test_validate_config_multiple_errors():
    """Test validation catches multiple errors"""
    config = GenerationSessionConfig(
        version="",  # Missing version
        prompt=PromptConfig(template=""),  # Missing template
        variations={},  # Missing variations
        generation=GenerationConfig(mode="invalid_mode")  # Invalid mode
    )

    result = validate_config(config)

    assert not result.is_valid
    assert len(result.errors) >= 3  # At least version, template, variations, mode


# --- load_and_validate_config Tests ---

def test_load_and_validate_config_success(tmp_path):
    """Test loading and validating valid config"""
    var_file = tmp_path / "var.txt"
    var_file.write_text("test")

    config_data = {
        "version": "1.0",
        "prompt": {
            "template": "test {Var}",
            "negative": "bad"
        },
        "variations": {
            "Var": str(var_file)
        },
        "generation": {
            "mode": "combinatorial",
            "seed_mode": "progressive",
            "seed": 42,
            "max_images": 10
        },
        "parameters": {
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7.0,
            "sampler": "DPM++ 2M Karras",
            "batch_size": 1,
            "batch_count": 1
        },
        "output": {
            "session_name": "test",
            "filename_keys": ["Var"]
        }
    }

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))

    config, result = load_and_validate_config(config_file)

    assert isinstance(config, GenerationSessionConfig)
    assert result.is_valid


def test_load_and_validate_config_invalid(tmp_path):
    """Test loading and validating invalid config"""
    config_data = {
        "version": "",  # Invalid
        "prompt": {
            "template": ""  # Invalid
        },
        "variations": {}  # Invalid
    }

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))

    config, result = load_and_validate_config(config_file)

    assert isinstance(config, GenerationSessionConfig)
    assert not result.is_valid
    assert len(result.errors) > 0
