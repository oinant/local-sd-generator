"""
Tests for Global Configuration System (SF-7)
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from sd_generator_cli.config.global_config import (
    GlobalConfig,
    locate_global_config,
    load_global_config,
    create_default_global_config,
    prompt_user_for_paths,
    ensure_global_config
)


# --- GlobalConfig Tests ---

def test_global_config_defaults():
    """Test GlobalConfig has correct default values"""
    config = GlobalConfig()
    assert config.configs_dir == "./configs"
    assert config.output_dir == "./apioutput"
    assert config.api_url == "http://127.0.0.1:7860"


def test_global_config_custom_values():
    """Test GlobalConfig with custom values"""
    config = GlobalConfig(
        configs_dir="/custom/configs",
        output_dir="/custom/output",
        api_url="http://localhost:8080"
    )
    assert config.configs_dir == "/custom/configs"
    assert config.output_dir == "/custom/output"
    assert config.api_url == "http://localhost:8080"


def test_global_config_to_dict():
    """Test GlobalConfig.to_dict()"""
    config = GlobalConfig(
        configs_dir="/test/configs",
        output_dir="/test/output",
        api_url="http://test:9000"
    )
    data = config.to_dict()
    assert data == {
        "configs_dir": "/test/configs",
        "output_dir": "/test/output",
        "api_url": "http://test:9000"
    }


def test_global_config_from_dict_full():
    """Test GlobalConfig.from_dict() with all fields"""
    data = {
        "configs_dir": "/from/dict/configs",
        "output_dir": "/from/dict/output",
        "api_url": "http://fromdict:7777"
    }
    config = GlobalConfig.from_dict(data)
    assert config.configs_dir == "/from/dict/configs"
    assert config.output_dir == "/from/dict/output"
    assert config.api_url == "http://fromdict:7777"


def test_global_config_from_dict_partial():
    """Test GlobalConfig.from_dict() with missing fields uses defaults"""
    data = {"configs_dir": "/partial/configs"}
    config = GlobalConfig.from_dict(data)
    assert config.configs_dir == "/partial/configs"
    assert config.output_dir == "./apioutput"  # default
    assert config.api_url == "http://127.0.0.1:7860"  # default


def test_global_config_from_dict_empty():
    """Test GlobalConfig.from_dict() with empty dict uses all defaults"""
    config = GlobalConfig.from_dict({})
    assert config.configs_dir == "./configs"
    assert config.output_dir == "./apioutput"
    assert config.api_url == "http://127.0.0.1:7860"


# --- locate_global_config Tests ---

def test_locate_global_config_project_root(tmp_path, monkeypatch):
    """Test locate_global_config finds file in project root"""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Create config in project root
    config_file = tmp_path / ".sdgen_config.json"
    config_file.write_text("{}")

    result = locate_global_config()
    assert result == config_file


def test_locate_global_config_user_home(tmp_path, monkeypatch):
    """Test locate_global_config finds file in user home"""
    # Create temp directories
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    project_dir.mkdir()
    home_dir.mkdir()

    # Change to project directory
    monkeypatch.chdir(project_dir)

    # Mock Path.home() to return our temp home
    with patch("pathlib.Path.home", return_value=home_dir):
        # Create config in home directory
        config_file = home_dir / ".sdgen_config.json"
        config_file.write_text("{}")

        result = locate_global_config()
        assert result == config_file


def test_locate_global_config_project_takes_precedence(tmp_path, monkeypatch):
    """Test project config takes precedence over home config"""
    # Create temp directories
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    project_dir.mkdir()
    home_dir.mkdir()

    # Change to project directory
    monkeypatch.chdir(project_dir)

    # Create configs in both locations
    project_config = project_dir / ".sdgen_config.json"
    home_config = home_dir / ".sdgen_config.json"
    project_config.write_text('{"configs_dir": "project"}')
    home_config.write_text('{"configs_dir": "home"}')

    with patch("pathlib.Path.home", return_value=home_dir):
        result = locate_global_config()
        assert result == project_config


def test_locate_global_config_not_found(tmp_path, monkeypatch):
    """Test locate_global_config returns None when not found"""
    # Create empty directories
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    project_dir.mkdir()
    home_dir.mkdir()

    monkeypatch.chdir(project_dir)

    with patch("pathlib.Path.home", return_value=home_dir):
        result = locate_global_config()
        assert result is None


# --- load_global_config Tests ---

def test_load_global_config_success(tmp_path, monkeypatch):
    """Test load_global_config loads valid config"""
    monkeypatch.chdir(tmp_path)

    config_data = {
        "configs_dir": "/loaded/configs",
        "output_dir": "/loaded/output",
        "api_url": "http://loaded:8888"
    }
    config_file = tmp_path / ".sdgen_config.json"
    config_file.write_text(json.dumps(config_data))

    config = load_global_config()
    assert config.configs_dir == "/loaded/configs"
    assert config.output_dir == "/loaded/output"
    assert config.api_url == "http://loaded:8888"


def test_load_global_config_not_found(tmp_path, monkeypatch):
    """Test load_global_config returns defaults when file not found"""
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    project_dir.mkdir()
    home_dir.mkdir()

    monkeypatch.chdir(project_dir)

    with patch("pathlib.Path.home", return_value=home_dir):
        config = load_global_config()
        assert config.configs_dir == "./configs"
        assert config.output_dir == "./apioutput"
        assert config.api_url == "http://127.0.0.1:7860"


def test_load_global_config_invalid_json(tmp_path, monkeypatch):
    """Test load_global_config raises on invalid JSON"""
    monkeypatch.chdir(tmp_path)

    config_file = tmp_path / ".sdgen_config.json"
    config_file.write_text("{ invalid json }")

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_global_config()


def test_load_global_config_partial_data(tmp_path, monkeypatch):
    """Test load_global_config with partial data uses defaults"""
    monkeypatch.chdir(tmp_path)

    config_data = {"configs_dir": "/only/configs"}
    config_file = tmp_path / ".sdgen_config.json"
    config_file.write_text(json.dumps(config_data))

    config = load_global_config()
    assert config.configs_dir == "/only/configs"
    assert config.output_dir == "./apioutput"
    assert config.api_url == "http://127.0.0.1:7860"


# --- create_default_global_config Tests ---

def test_create_default_global_config_defaults(tmp_path):
    """Test create_default_global_config creates file with defaults"""
    config_file = tmp_path / ".sdgen_config.json"

    create_default_global_config(config_file)

    assert config_file.exists()
    data = json.loads(config_file.read_text())
    assert data["configs_dir"] == "./configs"
    assert data["output_dir"] == "./apioutput"
    assert data["api_url"] == "http://127.0.0.1:7860"


def test_create_default_global_config_custom(tmp_path):
    """Test create_default_global_config with custom config"""
    config_file = tmp_path / ".sdgen_config.json"
    custom_config = GlobalConfig(
        configs_dir="/custom/path",
        output_dir="/custom/output",
        api_url="http://custom:9999"
    )

    create_default_global_config(config_file, custom_config)

    assert config_file.exists()
    data = json.loads(config_file.read_text())
    assert data["configs_dir"] == "/custom/path"
    assert data["output_dir"] == "/custom/output"
    assert data["api_url"] == "http://custom:9999"


def test_create_default_global_config_nested_path(tmp_path):
    """Test create_default_global_config creates parent directories"""
    nested_path = tmp_path / "nested" / "dir" / ".sdgen_config.json"

    create_default_global_config(nested_path)

    assert nested_path.exists()
    assert nested_path.parent.exists()


def test_create_default_global_config_pretty_printed(tmp_path):
    """Test config file is pretty-printed"""
    config_file = tmp_path / ".sdgen_config.json"

    create_default_global_config(config_file)

    content = config_file.read_text()
    assert content.count('\n') > 3  # Should be multi-line
    assert '  ' in content  # Should have indentation


# --- prompt_user_for_paths Tests ---

def test_prompt_user_for_paths_non_interactive():
    """Test prompt_user_for_paths in non-interactive mode"""
    configs_dir, output_dir, api_url = prompt_user_for_paths(interactive=False)

    assert configs_dir == "./configs"
    assert output_dir == "./apioutput"
    assert api_url == "http://127.0.0.1:7860"


def test_prompt_user_for_paths_interactive_defaults(monkeypatch):
    """Test prompt_user_for_paths uses defaults when user presses Enter"""
    # Mock input to return empty strings
    inputs = iter(['', '', ''])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    configs_dir, output_dir, api_url = prompt_user_for_paths(interactive=True)

    assert configs_dir == "./configs"
    assert output_dir == "./apioutput"
    assert api_url == "http://127.0.0.1:7860"


def test_prompt_user_for_paths_interactive_custom(monkeypatch):
    """Test prompt_user_for_paths with custom user input"""
    # Mock input to return custom values
    inputs = iter(['/custom/configs', '/custom/output', 'http://custom:8080'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    configs_dir, output_dir, api_url = prompt_user_for_paths(interactive=True)

    assert configs_dir == "/custom/configs"
    assert output_dir == "/custom/output"
    assert api_url == "http://custom:8080"


def test_prompt_user_for_paths_interactive_mixed(monkeypatch):
    """Test prompt_user_for_paths with some defaults and some custom"""
    # Mock input: custom configs_dir, default output_dir, custom api_url
    inputs = iter(['/my/configs', '', 'http://localhost:9000'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    configs_dir, output_dir, api_url = prompt_user_for_paths(interactive=True)

    assert configs_dir == "/my/configs"
    assert output_dir == "./apioutput"
    assert api_url == "http://localhost:9000"


# --- ensure_global_config Tests ---

def test_ensure_global_config_exists(tmp_path, monkeypatch):
    """Test ensure_global_config loads existing config"""
    monkeypatch.chdir(tmp_path)

    # Create existing config
    config_data = {"configs_dir": "/existing/configs"}
    config_file = tmp_path / ".sdgen_config.json"
    config_file.write_text(json.dumps(config_data))

    config = ensure_global_config(interactive=False)

    assert config.configs_dir == "/existing/configs"


def test_ensure_global_config_creates_non_interactive(tmp_path, monkeypatch):
    """Test ensure_global_config creates config in non-interactive mode"""
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    project_dir.mkdir()
    home_dir.mkdir()

    monkeypatch.chdir(project_dir)

    with patch("pathlib.Path.home", return_value=home_dir):
        config = ensure_global_config(interactive=False)

        # Should create in project root
        config_file = project_dir / ".sdgen_config.json"
        assert config_file.exists()

        # Should have default values
        assert config.configs_dir == "./configs"
        assert config.output_dir == "./apioutput"


def test_ensure_global_config_creates_interactive(tmp_path, monkeypatch):
    """Test ensure_global_config creates config in interactive mode"""
    project_dir = tmp_path / "project"
    home_dir = tmp_path / "home"
    project_dir.mkdir()
    home_dir.mkdir()

    monkeypatch.chdir(project_dir)

    # Mock user input
    inputs = iter(['/interactive/configs', '/interactive/output', 'http://interactive:7000'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    with patch("pathlib.Path.home", return_value=home_dir):
        config = ensure_global_config(interactive=True)

        config_file = project_dir / ".sdgen_config.json"
        assert config_file.exists()

        assert config.configs_dir == "/interactive/configs"
        assert config.output_dir == "/interactive/output"
        assert config.api_url == "http://interactive:7000"


def test_ensure_global_config_force_create(tmp_path, monkeypatch):
    """Test ensure_global_config with force_create recreates config"""
    monkeypatch.chdir(tmp_path)

    # Create existing config
    config_file = tmp_path / ".sdgen_config.json"
    config_file.write_text('{"configs_dir": "/old/configs"}')

    # Force create with new values
    inputs = iter(['/new/configs', '', ''])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    config = ensure_global_config(interactive=True, force_create=True)

    assert config.configs_dir == "/new/configs"

    # Verify file was updated
    data = json.loads(config_file.read_text())
    assert data["configs_dir"] == "/new/configs"
