"""
Unit tests for CLI argument parsing.

Tests that CLI options are correctly parsed without executing actual generation.
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path

from sd_generator_cli.cli import app


@pytest.fixture
def runner():
    """Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_generate_impl():
    """Mock the internal _generate_impl function to prevent actual execution."""
    with patch('sd_generator_cli.cli._generate_impl') as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_template_file(tmp_path):
    """Create a minimal valid template file."""
    template = tmp_path / "test.prompt.yaml"
    template.write_text("""
version: "2.0"
prompt: "test prompt"
negative: "test negative"
""")
    return template


class TestSeedsOption:
    """Test --seeds option parsing."""

    def test_seeds_explicit_list(self, runner, mock_generate_impl, mock_template_file):
        """Test --seeds with explicit list: 1000,1005,1008"""
        result = runner.invoke(app, [
            "generate",
            "-t", str(mock_template_file),
            "--seeds", "1000,1005,1008",
            "--dry-run"
        ])

        assert result.exit_code == 0, f"CLI failed: {result.stdout}"

        # Verify _generate_impl was called with seeds parameter
        assert mock_generate_impl.called
        call_kwargs = mock_generate_impl.call_args.kwargs
        assert "seeds" in call_kwargs
        assert call_kwargs["seeds"] == "1000,1005,1008"

    def test_seeds_range(self, runner, mock_generate_impl, mock_template_file):
        """Test --seeds with range: 1000-1019"""
        result = runner.invoke(app, [
            "generate",
            "-t", str(mock_template_file),
            "--seeds", "1000-1019",
            "--dry-run"
        ])

        assert result.exit_code == 0, f"CLI failed: {result.stdout}"

        call_kwargs = mock_generate_impl.call_args.kwargs
        assert call_kwargs["seeds"] == "1000-1019"

    def test_seeds_count_start(self, runner, mock_generate_impl, mock_template_file):
        """Test --seeds with count#start: 20#1000"""
        result = runner.invoke(app, [
            "generate",
            "-t", str(mock_template_file),
            "--seeds", "20#1000",
            "--dry-run"
        ])

        assert result.exit_code == 0, f"CLI failed: {result.stdout}"

        call_kwargs = mock_generate_impl.call_args.kwargs
        assert call_kwargs["seeds"] == "20#1000"

    def test_no_seeds_option(self, runner, mock_generate_impl, mock_template_file):
        """Test generate without --seeds (should work with default None)."""
        result = runner.invoke(app, [
            "generate",
            "-t", str(mock_template_file),
            "--dry-run"
        ])

        assert result.exit_code == 0, f"CLI failed: {result.stdout}"

        call_kwargs = mock_generate_impl.call_args.kwargs
        assert "seeds" in call_kwargs
        assert call_kwargs["seeds"] is None


class TestOtherOptions:
    """Test other CLI options to ensure they still work."""

    def test_template_option(self, runner, mock_generate_impl, mock_template_file):
        """Test -t/--template option."""
        result = runner.invoke(app, [
            "generate",
            "-t", str(mock_template_file),
            "--dry-run"
        ])

        assert result.exit_code == 0
        assert mock_generate_impl.called

    def test_num_images_option(self, runner, mock_generate_impl, mock_template_file):
        """Test -n option."""
        result = runner.invoke(app, [
            "generate",
            "-t", str(mock_template_file),
            "-n", "50",
            "--dry-run"
        ])

        assert result.exit_code == 0
        call_kwargs = mock_generate_impl.call_args.kwargs
        assert call_kwargs["num_images"] == 50

    def test_theme_option(self, runner, mock_generate_impl, mock_template_file):
        """Test --theme option."""
        result = runner.invoke(app, [
            "generate",
            "-t", str(mock_template_file),
            "--theme", "cyberpunk",
            "--dry-run"
        ])

        assert result.exit_code == 0
        call_kwargs = mock_generate_impl.call_args.kwargs
        assert call_kwargs["theme_name"] == "cyberpunk"

    def test_use_fixed_option(self, runner, mock_generate_impl, mock_template_file):
        """Test --use-fixed option."""
        result = runner.invoke(app, [
            "generate",
            "-t", str(mock_template_file),
            "--use-fixed", "hair:blonde",
            "--dry-run"
        ])

        assert result.exit_code == 0
        call_kwargs = mock_generate_impl.call_args.kwargs
        assert call_kwargs["use_fixed"] == "hair:blonde"


class TestCLIHelp:
    """Test CLI help messages."""

    def test_generate_help(self, runner):
        """Test that generate --help works and mentions --seeds."""
        result = runner.invoke(app, ["generate", "--help"])

        assert result.exit_code == 0
        assert "--seeds" in result.stdout
        assert "seed-sweep" in result.stdout.lower()

    def test_main_help(self, runner):
        """Test main --help works."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "generate" in result.stdout
