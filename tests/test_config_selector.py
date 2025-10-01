"""
Tests for config_selector.py (SF-2)
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "CLI"))

from config.config_selector import (
    ConfigInfo,
    discover_configs,
    display_config_list,
    validate_config_selection,
    prompt_user_selection,
    select_config_interactive,
    list_available_configs
)


class TestConfigInfo:
    """Test ConfigInfo dataclass"""

    def test_display_name_with_name(self):
        """display_name returns name if available"""
        config = ConfigInfo(
            path=Path("test.json"),
            name="Test Config",
            description="Test",
            filename="test.json"
        )
        assert config.display_name == "Test Config"

    def test_display_name_without_name(self):
        """display_name returns filename if name is empty"""
        config = ConfigInfo(
            path=Path("test.json"),
            name="",
            description="Test",
            filename="test.json"
        )
        assert config.display_name == "test.json"


class TestDiscoverConfigs:
    """Test config discovery"""

    def test_discover_valid_configs(self, tmp_path):
        """Discover valid JSON configs"""
        # Create test configs
        config1 = tmp_path / "config1.json"
        config1.write_text(json.dumps({
            "name": "Config 1",
            "description": "First config",
            "version": "1.0"
        }))

        config2 = tmp_path / "config2.json"
        config2.write_text(json.dumps({
            "name": "Config 2",
            "description": "Second config",
            "version": "1.0"
        }))

        configs = discover_configs(tmp_path)

        assert len(configs) == 2
        assert configs[0].filename == "config1.json"
        assert configs[0].name == "Config 1"
        assert configs[0].description == "First config"
        assert configs[1].filename == "config2.json"

    def test_discover_config_without_metadata(self, tmp_path):
        """Discover config without name/description"""
        config = tmp_path / "minimal.json"
        config.write_text(json.dumps({"version": "1.0"}))

        configs = discover_configs(tmp_path)

        assert len(configs) == 1
        assert configs[0].filename == "minimal.json"
        assert configs[0].name == ""
        assert configs[0].description == ""

    def test_discover_invalid_json(self, tmp_path):
        """Discover config with invalid JSON (should not crash)"""
        config = tmp_path / "invalid.json"
        config.write_text("not valid json {")

        configs = discover_configs(tmp_path)

        # Should still find the file, just with empty metadata
        assert len(configs) == 1
        assert configs[0].filename == "invalid.json"
        assert configs[0].name == ""

    def test_discover_empty_directory(self, tmp_path):
        """Discover in empty directory"""
        configs = discover_configs(tmp_path)
        assert len(configs) == 0

    def test_discover_nonexistent_directory(self):
        """Error on nonexistent directory"""
        with pytest.raises(FileNotFoundError):
            discover_configs(Path("/nonexistent/path"))

    def test_discover_not_a_directory(self, tmp_path):
        """Error when path is not a directory"""
        file = tmp_path / "file.txt"
        file.write_text("test")

        with pytest.raises(NotADirectoryError):
            discover_configs(file)

    def test_discover_ignores_non_json(self, tmp_path):
        """Ignores non-JSON files"""
        (tmp_path / "test.txt").write_text("text")
        (tmp_path / "test.md").write_text("markdown")
        (tmp_path / "config.json").write_text(json.dumps({"version": "1.0"}))

        configs = discover_configs(tmp_path)

        assert len(configs) == 1
        assert configs[0].filename == "config.json"

    def test_discover_sorted_by_filename(self, tmp_path):
        """Configs are sorted by filename"""
        (tmp_path / "zebra.json").write_text(json.dumps({"version": "1.0"}))
        (tmp_path / "apple.json").write_text(json.dumps({"version": "1.0"}))
        (tmp_path / "banana.json").write_text(json.dumps({"version": "1.0"}))

        configs = discover_configs(tmp_path)

        assert len(configs) == 3
        assert configs[0].filename == "apple.json"
        assert configs[1].filename == "banana.json"
        assert configs[2].filename == "zebra.json"


class TestDisplayConfigList:
    """Test config list display"""

    def test_display_empty_list(self, capsys):
        """Display empty config list"""
        display_config_list([])

        captured = capsys.readouterr()
        assert "No configuration files found" in captured.out

    def test_display_configs_with_metadata(self, capsys):
        """Display configs with full metadata"""
        configs = [
            ConfigInfo(
                path=Path("test1.json"),
                name="Test Config 1",
                description="First test config",
                filename="test1.json"
            ),
            ConfigInfo(
                path=Path("test2.json"),
                name="Test Config 2",
                description="Second test config",
                filename="test2.json"
            )
        ]

        display_config_list(configs)

        captured = capsys.readouterr()
        assert "Available configurations:" in captured.out
        assert "1. test1.json" in captured.out
        assert "Test Config 1" in captured.out
        assert "First test config" in captured.out
        assert "2. test2.json" in captured.out

    def test_display_configs_without_metadata(self, capsys):
        """Display configs without metadata"""
        configs = [
            ConfigInfo(
                path=Path("minimal.json"),
                name="",
                description="",
                filename="minimal.json"
            )
        ]

        display_config_list(configs)

        captured = capsys.readouterr()
        assert "1. minimal.json" in captured.out


class TestValidateConfigSelection:
    """Test selection validation"""

    def test_valid_selection(self):
        """Valid numeric selection"""
        index = validate_config_selection("1", 3)
        assert index == 0

        index = validate_config_selection("3", 3)
        assert index == 2

    def test_invalid_non_numeric(self):
        """Invalid non-numeric input"""
        with pytest.raises(ValueError, match="Invalid selection"):
            validate_config_selection("abc", 3)

    def test_invalid_too_low(self):
        """Selection below range"""
        with pytest.raises(ValueError, match="must be between"):
            validate_config_selection("0", 3)

    def test_invalid_too_high(self):
        """Selection above range"""
        with pytest.raises(ValueError, match="must be between"):
            validate_config_selection("4", 3)

    def test_invalid_negative(self):
        """Negative selection"""
        with pytest.raises(ValueError, match="must be between"):
            validate_config_selection("-1", 3)


class TestPromptUserSelection:
    """Test interactive user prompting"""

    def test_valid_selection(self, tmp_path):
        """User selects valid config"""
        configs = [
            ConfigInfo(Path("test1.json"), "Test 1", "Desc 1", "test1.json"),
            ConfigInfo(Path("test2.json"), "Test 2", "Desc 2", "test2.json")
        ]

        with patch('builtins.input', return_value="2"):
            selected = prompt_user_selection(configs)

        assert selected == Path("test2.json")

    def test_invalid_then_valid_selection(self, tmp_path):
        """User enters invalid then valid selection"""
        configs = [
            ConfigInfo(Path("test1.json"), "Test 1", "Desc 1", "test1.json")
        ]

        with patch('builtins.input', side_effect=["invalid", "5", "1"]):
            selected = prompt_user_selection(configs)

        assert selected == Path("test1.json")

    def test_empty_input(self):
        """User enters empty input"""
        configs = [
            ConfigInfo(Path("test.json"), "Test", "Desc", "test.json")
        ]

        with patch('builtins.input', return_value=""):
            with pytest.raises(ValueError, match="cancelled"):
                prompt_user_selection(configs)

    def test_keyboard_interrupt(self):
        """User cancels with Ctrl+C"""
        configs = [
            ConfigInfo(Path("test.json"), "Test", "Desc", "test.json")
        ]

        with patch('builtins.input', side_effect=KeyboardInterrupt):
            with pytest.raises(ValueError, match="cancelled"):
                prompt_user_selection(configs)

    def test_eof_error(self):
        """EOF on input (stdin closed)"""
        configs = [
            ConfigInfo(Path("test.json"), "Test", "Desc", "test.json")
        ]

        with patch('builtins.input', side_effect=EOFError):
            with pytest.raises(ValueError, match="cancelled"):
                prompt_user_selection(configs)

    def test_no_configs_available(self):
        """Error when no configs provided"""
        with pytest.raises(ValueError, match="No configurations available"):
            prompt_user_selection([])


class TestSelectConfigInteractive:
    """Test complete interactive flow"""

    def test_successful_selection(self, tmp_path):
        """Complete flow with valid selection"""
        # Create test configs
        (tmp_path / "config1.json").write_text(json.dumps({
            "name": "Config 1",
            "version": "1.0"
        }))
        (tmp_path / "config2.json").write_text(json.dumps({
            "name": "Config 2",
            "version": "1.0"
        }))

        with patch('builtins.input', return_value="2"):
            selected = select_config_interactive(tmp_path)

        assert selected.name == "config2.json"

    def test_no_configs_in_directory(self, tmp_path):
        """Error when directory has no configs"""
        with pytest.raises(ValueError, match="No configuration files found"):
            select_config_interactive(tmp_path)


class TestListAvailableConfigs:
    """Test config listing"""

    def test_list_configs(self, tmp_path, capsys):
        """List available configs"""
        (tmp_path / "test.json").write_text(json.dumps({
            "name": "Test Config",
            "description": "Test description",
            "version": "1.0"
        }))

        list_available_configs(tmp_path)

        captured = capsys.readouterr()
        assert "test.json" in captured.out
        assert "Test Config" in captured.out
        assert "Test description" in captured.out

    def test_list_empty_directory(self, tmp_path, capsys):
        """List empty directory"""
        list_available_configs(tmp_path)

        captured = capsys.readouterr()
        assert "No configuration files found" in captured.out
