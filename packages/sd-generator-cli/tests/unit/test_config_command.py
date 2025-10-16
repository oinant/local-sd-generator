"""
Tests for config command.

Tests all three modes:
- list: Display all config keys
- read: Read a specific key
- write: Write a value to a key
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

# Import the CLI app
from sd_generator_cli.cli import app

runner = CliRunner()


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Create a temporary config file for testing."""
    config_path = tmp_path / "sdgen_config.json"
    config_data = {
        "api_url": "http://127.0.0.1:7860",
        "configs_dir": "./prompts",
        "output_dir": "./results",
        "webui_token": "abcdefghijklmnopqrstuvwxyz123456"
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)
        f.write('\n')
    return config_path


@pytest.fixture
def config_file_no_token(tmp_path: Path) -> Path:
    """Create a temporary config file without webui_token."""
    config_path = tmp_path / "sdgen_config.json"
    config_data = {
        "api_url": "http://127.0.0.1:7860",
        "configs_dir": "./prompts",
        "output_dir": "./results"
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)
        f.write('\n')
    return config_path


class TestConfigCommandHelp:
    """Test config command help functionality."""

    def test_config_help(self) -> None:
        """Test that 'config' command help works."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "config" in result.stdout.lower()
        assert "read or write" in result.stdout.lower()


class TestConfigCommandList:
    """Test config list mode."""

    def test_config_list_displays_all_keys(self, config_file: Path, monkeypatch: Any) -> None:
        """Test that 'config list' shows all config keys."""
        monkeypatch.chdir(config_file.parent)
        result = runner.invoke(app, ["config", "list"])

        assert result.exit_code == 0
        assert "api_url" in result.stdout
        assert "configs_dir" in result.stdout
        assert "output_dir" in result.stdout
        assert "webui_token" in result.stdout
        assert "http://127.0.0.1:7860" in result.stdout
        assert "./prompts" in result.stdout
        assert "./results" in result.stdout

    def test_config_list_with_flag(self, config_file: Path, monkeypatch: Any) -> None:
        """Test that 'config --list' shows all config keys."""
        monkeypatch.chdir(config_file.parent)
        result = runner.invoke(app, ["config", "--list"])

        assert result.exit_code == 0
        assert "api_url" in result.stdout
        assert "configs_dir" in result.stdout

    def test_config_list_shows_full_webui_token(self, config_file: Path, monkeypatch: Any) -> None:
        """Test that webui_token is displayed in full (not masked)."""
        monkeypatch.chdir(config_file.parent)
        result = runner.invoke(app, ["config", "list"])

        assert result.exit_code == 0
        # Full token should appear (no masking for local tool)
        assert "abcdefghijklmnopqrstuvwxyz123456" in result.stdout

    def test_config_list_shows_not_set_for_missing_token(self, config_file_no_token: Path, monkeypatch: Any) -> None:
        """Test that missing webui_token shows as 'not set'."""
        monkeypatch.chdir(config_file_no_token.parent)
        result = runner.invoke(app, ["config", "list"])

        assert result.exit_code == 0
        assert "webui_token" in result.stdout
        # Should show "not set" or similar
        assert "not set" in result.stdout.lower() or "none" in result.stdout.lower()


class TestConfigCommandRead:
    """Test config read mode."""

    def test_config_read_existing_key(self, config_file: Path, monkeypatch: Any) -> None:
        """Test reading a valid config key."""
        monkeypatch.chdir(config_file.parent)
        result = runner.invoke(app, ["config", "api_url"])

        assert result.exit_code == 0
        assert "http://127.0.0.1:7860" in result.stdout

    def test_config_read_all_keys(self, config_file: Path, monkeypatch: Any) -> None:
        """Test reading all valid config keys."""
        monkeypatch.chdir(config_file.parent)
        keys_to_test = ["api_url", "configs_dir", "output_dir", "webui_token"]

        for key in keys_to_test:
            result = runner.invoke(app, ["config", key])
            assert result.exit_code == 0

    def test_config_read_invalid_key(self, config_file: Path, monkeypatch: Any) -> None:
        """Test reading an invalid key shows error."""
        monkeypatch.chdir(config_file.parent)
        result = runner.invoke(app, ["config", "invalid_key"])

        assert result.exit_code == 1
        assert "does not exist" in result.stdout.lower() or "invalid" in result.stdout.lower()
        # Should list valid keys
        assert "api_url" in result.stdout
        assert "configs_dir" in result.stdout


class TestConfigCommandWrite:
    """Test config write mode."""

    def test_config_write_existing_key(self, config_file: Path, monkeypatch: Any) -> None:
        """Test writing to a valid config key."""
        monkeypatch.chdir(config_file.parent)
        new_url = "http://172.29.128.1:7860"

        result = runner.invoke(app, ["config", "api_url", new_url])

        assert result.exit_code == 0
        assert "set to" in result.stdout.lower()

        # Verify value was actually written
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        assert config_data["api_url"] == new_url

    def test_config_write_all_keys(self, config_file: Path, monkeypatch: Any) -> None:
        """Test writing to all valid config keys."""
        monkeypatch.chdir(config_file.parent)
        test_values = {
            "api_url": "http://192.168.1.1:7860",
            "configs_dir": "./my-configs",
            "output_dir": "./my-results",
            "webui_token": "new-token-12345"
        }

        for key, value in test_values.items():
            result = runner.invoke(app, ["config", key, value])
            assert result.exit_code == 0

        # Verify all values were written
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        for key, value in test_values.items():
            assert config_data[key] == value

    def test_config_write_invalid_key(self, config_file: Path, monkeypatch: Any) -> None:
        """Test writing to invalid key shows error."""
        monkeypatch.chdir(config_file.parent)
        result = runner.invoke(app, ["config", "invalid_key", "some_value"])

        assert result.exit_code == 1
        assert "does not exist" in result.stdout.lower() or "invalid" in result.stdout.lower()
        # Should list valid keys
        assert "api_url" in result.stdout

    def test_config_write_preserves_formatting(self, config_file: Path, monkeypatch: Any) -> None:
        """Test that writing preserves JSON formatting."""
        monkeypatch.chdir(config_file.parent)
        result = runner.invoke(app, ["config", "api_url", "http://new-url:7860"])

        assert result.exit_code == 0

        # Check that file is still valid JSON with proper formatting
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should be valid JSON
        json.loads(content)

        # Should have indentation (pretty-printed)
        assert '  "' in content  # 2-space indentation


class TestConfigCommandErrors:
    """Test config command error handling."""

    def test_config_no_file_shows_error(self, tmp_path: Path, monkeypatch: Any) -> None:
        """Test error when no config file exists."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["config", "list"])

        assert result.exit_code == 1
        assert "no config file" in result.stdout.lower() or "not found" in result.stdout.lower()
        assert "sdgen init" in result.stdout.lower()

    def test_config_read_no_file(self, tmp_path: Path, monkeypatch: Any) -> None:
        """Test error when reading from non-existent config."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["config", "api_url"])

        assert result.exit_code == 1
        assert "no config file" in result.stdout.lower() or "not found" in result.stdout.lower()

    def test_config_write_no_file(self, tmp_path: Path, monkeypatch: Any) -> None:
        """Test error when writing to non-existent config."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["config", "api_url", "http://test:7860"])

        assert result.exit_code == 1
        assert "no config file" in result.stdout.lower() or "not found" in result.stdout.lower()

    def test_config_corrupted_json(self, tmp_path: Path, monkeypatch: Any) -> None:
        """Test error when config file has invalid JSON."""
        config_path = tmp_path / "sdgen_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("{invalid json content")

        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["config", "list"])

        assert result.exit_code == 1
        assert "invalid" in result.stdout.lower()

    def test_config_no_key_provided(self, config_file: Path, monkeypatch: Any) -> None:
        """Test error when no key is provided (without --list)."""
        monkeypatch.chdir(config_file.parent)
        result = runner.invoke(app, ["config"])

        # Should show help or error
        assert result.exit_code != 0


class TestConfigCommandRenewToken:
    """Test config renew-token mode."""

    def test_renew_token_generates_new_token(self, config_file: Path, monkeypatch: Any) -> None:
        """Test that renew-token generates a new UUID token."""
        monkeypatch.chdir(config_file.parent)

        # Get original token
        with open(config_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        original_token = original_data.get("webui_token")

        # Run renew-token
        result = runner.invoke(app, ["config", "renew-token"])

        assert result.exit_code == 0
        assert "new webui token generated" in result.stdout.lower()
        assert "webui services need to be restarted" in result.stdout.lower()
        assert "sdgen webui restart" in result.stdout.lower()

        # Verify new token was written
        with open(config_file, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
        new_token = new_data.get("webui_token")

        # Should be different
        assert new_token != original_token
        # Should be a UUID (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
        assert len(new_token) == 36
        assert new_token.count('-') == 4

    def test_renew_token_preserves_other_keys(self, config_file: Path, monkeypatch: Any) -> None:
        """Test that renew-token doesn't change other config keys."""
        monkeypatch.chdir(config_file.parent)

        # Get original config
        with open(config_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)

        original_api_url = original_data["api_url"]
        original_configs_dir = original_data["configs_dir"]
        original_output_dir = original_data["output_dir"]

        # Run renew-token
        result = runner.invoke(app, ["config", "renew-token"])
        assert result.exit_code == 0

        # Verify other keys unchanged
        with open(config_file, 'r', encoding='utf-8') as f:
            new_data = json.load(f)

        assert new_data["api_url"] == original_api_url
        assert new_data["configs_dir"] == original_configs_dir
        assert new_data["output_dir"] == original_output_dir

    def test_renew_token_works_without_existing_token(self, config_file_no_token: Path, monkeypatch: Any) -> None:
        """Test that renew-token works even if no token exists initially."""
        monkeypatch.chdir(config_file_no_token.parent)

        # Verify no token initially
        with open(config_file_no_token, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        assert "webui_token" not in original_data or original_data.get("webui_token") is None

        # Run renew-token
        result = runner.invoke(app, ["config", "renew-token"])
        assert result.exit_code == 0

        # Verify token was created
        with open(config_file_no_token, 'r', encoding='utf-8') as f:
            new_data = json.load(f)

        new_token = new_data.get("webui_token")
        assert new_token is not None
        assert len(new_token) == 36  # UUID format

    def test_renew_token_displays_new_token_in_output(self, config_file: Path, monkeypatch: Any) -> None:
        """Test that renew-token displays the new token in output."""
        monkeypatch.chdir(config_file.parent)

        result = runner.invoke(app, ["config", "renew-token"])

        assert result.exit_code == 0

        # Extract token from output (format: "✓ New WebUI token generated: <token>")
        # The token should be visible in the output
        lines = result.stdout.split('\n')
        token_line = [l for l in lines if "token generated" in l.lower()][0]

        # Should contain a UUID-like string
        import re
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        match = re.search(uuid_pattern, token_line)
        assert match is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
