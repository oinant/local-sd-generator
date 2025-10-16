"""
Tests for CLI command mapping and help functionality.

These tests verify that all CLI commands are properly mapped and
their help text can be displayed without errors.
"""

import subprocess
import pytest


class TestCLICommands:
    """Test suite for CLI commands mapping."""

    def test_main_help(self):
        """Test that main help command works."""
        result = subprocess.run(
            ["sdgen", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "sd-generator-cli" in result.stdout or "Usage:" in result.stdout

    def test_generate_help(self):
        """Test that 'generate' command help works."""
        result = subprocess.run(
            ["sdgen", "generate", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "generate" in result.stdout.lower()

    def test_list_help(self):
        """Test that 'list' command help works."""
        result = subprocess.run(
            ["sdgen", "list", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "list" in result.stdout.lower()

    def test_validate_help(self):
        """Test that 'validate' command help works."""
        result = subprocess.run(
            ["sdgen", "validate", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "validate" in result.stdout.lower()

    def test_init_help(self):
        """Test that 'init' command help works."""
        result = subprocess.run(
            ["sdgen", "init", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "init" in result.stdout.lower()

    def test_api_help(self):
        """Test that 'api' command help works."""
        result = subprocess.run(
            ["sdgen", "api", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "api" in result.stdout.lower()

    def test_webui_help(self):
        """Test that 'webui' command help works."""
        result = subprocess.run(
            ["sdgen", "webui", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "webui" in result.stdout.lower()

    def test_webui_start_help(self):
        """Test that 'webui start' command help works."""
        result = subprocess.run(
            ["sdgen", "webui", "start", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "start" in result.stdout.lower()
        assert "--dev-mode" in result.stdout

    def test_webui_stop_help(self):
        """Test that 'webui stop' command help works."""
        result = subprocess.run(
            ["sdgen", "webui", "stop", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "stop" in result.stdout.lower()

    def test_webui_restart_help(self):
        """Test that 'webui restart' command help works."""
        result = subprocess.run(
            ["sdgen", "webui", "restart", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "restart" in result.stdout.lower()

    def test_webui_status_help(self):
        """Test that 'webui status' command help works."""
        result = subprocess.run(
            ["sdgen", "webui", "status", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "status" in result.stdout.lower()

    def test_start_help(self):
        """Test that 'start' command help works."""
        result = subprocess.run(
            ["sdgen", "start", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "start" in result.stdout.lower()

    def test_stop_help(self):
        """Test that 'stop' command help works."""
        result = subprocess.run(
            ["sdgen", "stop", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "stop" in result.stdout.lower()

    def test_status_help(self):
        """Test that 'status' command help works."""
        result = subprocess.run(
            ["sdgen", "status", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "status" in result.stdout.lower()

    def test_config_help(self):
        """Test that 'config' command help works."""
        result = subprocess.run(
            ["sdgen", "config", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "config" in result.stdout.lower()


class TestCLICommandErrors:
    """Test suite for CLI command error handling."""

    def test_invalid_command(self):
        """Test that invalid command returns error."""
        result = subprocess.run(
            ["sdgen", "invalid-command"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

    def test_generate_missing_template(self):
        """Test that 'generate' without template returns error."""
        result = subprocess.run(
            ["sdgen", "generate", "-t", "/nonexistent/template.yaml"],
            capture_output=True,
            text=True
        )
        # Should fail because template doesn't exist
        assert result.returncode != 0

    def test_validate_missing_file(self):
        """Test that 'validate' with missing file returns error."""
        result = subprocess.run(
            ["sdgen", "validate", "/nonexistent/template.yaml"],
            capture_output=True,
            text=True
        )
        # Should fail because file doesn't exist
        assert result.returncode != 0

    def test_webui_start_invalid_port(self):
        """Test that 'webui start' with invalid port handles error."""
        result = subprocess.run(
            ["sdgen", "webui", "start", "--backend-port", "invalid"],
            capture_output=True,
            text=True
        )
        # Should fail because port is not a number
        assert result.returncode != 0


class TestCLICommandFlags:
    """Test suite for CLI command flags."""

    def test_webui_start_has_dev_mode_flag(self):
        """Test that 'webui start' has --dev-mode flag."""
        result = subprocess.run(
            ["sdgen", "webui", "start", "--help"],
            capture_output=True,
            text=True
        )
        assert "--dev-mode" in result.stdout

    def test_webui_start_has_backend_port_flag(self):
        """Test that 'webui start' has --backend-port flag."""
        result = subprocess.run(
            ["sdgen", "webui", "start", "--help"],
            capture_output=True,
            text=True
        )
        assert "--backend-port" in result.stdout or "-bp" in result.stdout

    def test_webui_start_has_frontend_port_flag(self):
        """Test that 'webui start' has --frontend-port flag."""
        result = subprocess.run(
            ["sdgen", "webui", "start", "--help"],
            capture_output=True,
            text=True
        )
        assert "--frontend-port" in result.stdout or "-fp" in result.stdout

    def test_webui_start_has_no_reload_flag(self):
        """Test that 'webui start' has --no-reload flag."""
        result = subprocess.run(
            ["sdgen", "webui", "start", "--help"],
            capture_output=True,
            text=True
        )
        assert "--no-reload" in result.stdout

    def test_generate_has_template_flag(self):
        """Test that 'generate' has -t/--template flag."""
        result = subprocess.run(
            ["sdgen", "generate", "--help"],
            capture_output=True,
            text=True
        )
        assert "-t" in result.stdout or "--template" in result.stdout

    def test_generate_has_num_images_flag(self):
        """Test that 'generate' has -n/--num-images flag."""
        result = subprocess.run(
            ["sdgen", "generate", "--help"],
            capture_output=True,
            text=True
        )
        assert "-n" in result.stdout or "--num-images" in result.stdout

    def test_generate_has_dry_run_flag(self):
        """Test that 'generate' has --dry-run flag."""
        result = subprocess.run(
            ["sdgen", "generate", "--help"],
            capture_output=True,
            text=True
        )
        assert "--dry-run" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
