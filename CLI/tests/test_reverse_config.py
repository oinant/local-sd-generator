"""
Tests for reverse_config.py tool
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from reverse_config import (
    parse_session_config,
    extract_placeholders,
    generate_json_config
)


class TestParseSessionConfig:
    """Test session_config.txt parsing"""

    def test_parse_basic_config(self, tmp_path):
        """Parse basic session config"""
        config_file = tmp_path / "session_config.txt"
        config_file.write_text("""
============================================================
SESSION CONFIGURATION
============================================================

Date de génération: 2025-09-28 20:33:33
Nom de session: test_session
URL API: http://127.0.0.1:7860

----------------------------------------
PROMPTS
----------------------------------------
Prompt de base:
Test prompt with {Placeholder}

Prompt négatif:
low quality

----------------------------------------
PARAMÈTRES DE GÉNÉRATION
----------------------------------------
steps: 30
cfg_scale: 7.5
width: 512
height: 768
sampler_name: Euler a
batch_size: 1
n_iter: 1

----------------------------------------
INFORMATIONS ADDITIONNELLES
----------------------------------------
seed_principal: 42
nombre_images_demandees: 10
        """)

        config = parse_session_config(config_file)

        assert config["session_name"] == "test_session"
        assert config["date"] == "2025-09-28 20:33:33"
        assert "{Placeholder}" in config["prompt_template"]
        assert config["negative_prompt"] == "low quality"
        assert config["parameters"]["steps"] == 30
        assert config["parameters"]["cfg_scale"] == 7.5
        assert config["additional_info"]["seed_principal"] == 42


class TestExtractPlaceholders:
    """Test placeholder extraction"""

    def test_extract_single_placeholder(self):
        """Extract single placeholder"""
        prompt = "Test {Placeholder} here"
        placeholders = extract_placeholders(prompt)
        assert placeholders == ["Placeholder"]

    def test_extract_multiple_placeholders(self):
        """Extract multiple placeholders"""
        prompt = "{First}, {Second}, test {Third}"
        placeholders = extract_placeholders(prompt)
        assert placeholders == ["First", "Second", "Third"]

    def test_extract_with_options(self):
        """Extract placeholders with options"""
        prompt = "{Placeholder:5} and {Other:#|1|2|3}"
        placeholders = extract_placeholders(prompt)
        assert placeholders == ["Placeholder", "Other"]

    def test_no_placeholders(self):
        """No placeholders in prompt"""
        prompt = "Plain text prompt"
        placeholders = extract_placeholders(prompt)
        assert placeholders == []


class TestGenerateJsonConfig:
    """Test JSON config generation"""

    def test_generate_from_session(self, tmp_path):
        """Generate config from session directory"""
        # Create mock session directory
        session_dir = tmp_path / "test_session"
        session_dir.mkdir()

        # Create session_config.txt
        config_file = session_dir / "session_config.txt"
        config_file.write_text("""
============================================================
SESSION CONFIGURATION
============================================================

Nom de session: test_gen
Date de génération: 2025-10-01

----------------------------------------
PROMPTS
----------------------------------------
Prompt de base:
{Expression}, portrait

Prompt négatif:
bad quality

----------------------------------------
PARAMÈTRES DE GÉNÉRATION
----------------------------------------
steps: 20
cfg_scale: 7.0
width: 512
height: 512
sampler_name: DPM++ 2M
batch_size: 1
n_iter: 1

----------------------------------------
INFORMATIONS ADDITIONNELLES
----------------------------------------
seed_principal: 123
nombre_images_demandees: 5
        """)

        # Generate config (dry-run)
        config = generate_json_config(
            session_dir=session_dir,
            dry_run=True
        )

        # Verify config structure
        assert config["version"] == "1.0"
        assert "test_gen" in config["name"]
        assert "{Expression}" in config["prompt"]["template"]
        assert config["prompt"]["negative"] == "bad quality"
        assert "Expression" in config["variations"]
        assert config["generation"]["seed"] == 123
        assert config["generation"]["max_images"] == 5
        assert config["parameters"]["steps"] == 20
        assert config["parameters"]["width"] == 512

    def test_missing_session_config(self, tmp_path):
        """Error when session_config.txt missing"""
        session_dir = tmp_path / "empty_session"
        session_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            generate_json_config(session_dir, dry_run=True)
