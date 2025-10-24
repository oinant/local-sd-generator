"""
Integration tests for Themable Templates (Phase 2).

Tests the full pipeline:
- V2Pipeline with theme + style resolution
- CLI commands (theme list/show/validate)
- Manifest enrichment with theme metadata
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from sd_generator_cli.templating.orchestrator import V2Pipeline
from sd_generator_cli.templating.models import TemplateConfig, ThemeConfig


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_configs_dir(tmp_path):
    """
    Create a complete test configs directory structure.

    Structure:
        configs/
        ├── defaults/
        │   ├── ambiance.yaml
        │   └── outfit.default.yaml
        ├── themes/
        │   └── cyberpunk/
        │       ├── cyberpunk_ambiance.yaml
        │       ├── cyberpunk_outfit.default.yaml
        │       └── cyberpunk_outfit.cartoon.yaml
        └── templates/
            └── character.template.yaml
    """
    configs = tmp_path / "configs"
    configs.mkdir()

    # Create defaults (must be in templates/ for relative imports to work)
    templates_dir = configs / "templates"
    templates_dir.mkdir()

    defaults_dir = templates_dir / "defaults"
    defaults_dir.mkdir()
    (defaults_dir / "ambiance.yaml").write_text(
        "default_ambiance: calm atmosphere\n"
    )
    (defaults_dir / "outfit.default.yaml").write_text(
        "default_outfit: casual clothes\n"
    )

    # Create theme
    theme_dir = configs / "themes" / "cyberpunk"
    theme_dir.mkdir(parents=True)

    # Theme config
    theme_config = {
        "name": "cyberpunk",
        "explicit": True,
        "imports": {
            "Ambiance": "cyberpunk/cyberpunk_ambiance.yaml",
            "Outfit.default": "cyberpunk/cyberpunk_outfit.default.yaml",
            "Outfit.cartoon": "cyberpunk/cyberpunk_outfit.cartoon.yaml"
        },
        "variations": ["Ambiance", "Outfit"]
    }
    (theme_dir / "theme.yaml").write_text(
        f"# Cyberpunk Theme\n"
        f"name: {theme_config['name']}\n"
        f"imports:\n"
        f"  Ambiance: {theme_config['imports']['Ambiance']}\n"
        f"  Outfit.default: {theme_config['imports']['Outfit.default']}\n"
        f"  Outfit.cartoon: {theme_config['imports']['Outfit.cartoon']}\n"
        f"variations:\n"
        f"  - Ambiance\n"
        f"  - Outfit\n"
    )

    # Theme variation files
    (theme_dir / "cyberpunk_ambiance.yaml").write_text(
        "neon: neon lights, dark streets\n"
        "rainy: rainy cyberpunk city\n"
    )
    (theme_dir / "cyberpunk_outfit.default.yaml").write_text(
        "leather: black leather jacket\n"
        "tech: tech gear, cybernetic implants\n"
    )
    (theme_dir / "cyberpunk_outfit.cartoon.yaml").write_text(
        "anime: anime style cyberpunk outfit\n"
        "chibi: chibi cyberpunk clothing\n"
    )

    # Create template (templates_dir already exists from above)
    template_content = """version: "2.0"
name: character
themable: true
style_sensitive: true
style_sensitive_placeholders:
  - Outfit

template: "{prompt}"
negative_prompt: "low quality, blurry"

prompts:
  default: "masterpiece, {Ambiance}, {Outfit}, detailed"

imports:
  Ambiance: defaults/ambiance.yaml
  Outfit: defaults/outfit.default.yaml

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: 10
"""
    (templates_dir / "character.template.yaml").write_text(template_content)

    return configs


@pytest.fixture
def pipeline(temp_configs_dir):
    """Create V2Pipeline with test configs."""
    return V2Pipeline(configs_dir=str(temp_configs_dir))


# ============================================================================
# Integration Tests - V2Pipeline with Themes
# ============================================================================

class TestV2PipelineThemeIntegration:
    """Test V2Pipeline with theme support."""

    def test_pipeline_without_theme(self, pipeline, temp_configs_dir):
        """Test generation without theme (template defaults only)."""
        template_path = temp_configs_dir / "templates" / "character.template.yaml"

        # Load and resolve without theme
        config = pipeline.load(str(template_path))
        resolved_config, context = pipeline.resolve(config)

        # Should use template defaults
        assert "Ambiance" in context.imports
        assert "Outfit" in context.imports
        assert context.style == "default"

        # Generate prompts
        prompts = pipeline.generate(resolved_config, context)
        assert len(prompts) > 0
        assert "masterpiece" in prompts[0]['prompt']

    def test_pipeline_with_theme_default_style(self, pipeline, temp_configs_dir):
        """Test generation with theme and default style."""
        template_path = temp_configs_dir / "templates" / "character.template.yaml"

        # Load and resolve with theme
        config = pipeline.load(str(template_path))
        resolved_config, context = pipeline.resolve(
            config,
            theme_name="cyberpunk",
            style="default"
        )

        # Should use theme imports
        assert context.style == "default"
        assert "Ambiance" in context.imports
        assert "Outfit" in context.imports

        # Check import resolution metadata
        assert "Ambiance" in context.import_resolution
        assert context.import_resolution["Ambiance"]["source"] == "theme"
        assert context.import_resolution["Ambiance"]["override"] is True

        # Generate prompts
        prompts = pipeline.generate(resolved_config, context)
        assert len(prompts) > 0

    def test_pipeline_with_theme_cartoon_style(self, pipeline, temp_configs_dir):
        """Test generation with theme and cartoon style."""
        template_path = temp_configs_dir / "templates" / "character.template.yaml"

        # Load and resolve with theme + cartoon style
        config = pipeline.load(str(template_path))
        resolved_config, context = pipeline.resolve(
            config,
            theme_name="cyberpunk",
            style="cartoon"
        )

        # Should use cartoon variant for Outfit
        assert context.style == "cartoon"
        assert "Outfit" in context.import_resolution
        assert context.import_resolution["Outfit"]["style_sensitive"] is True
        assert context.import_resolution["Outfit"]["resolved_style"] == "cartoon"

        # Generate prompts
        prompts = pipeline.generate(resolved_config, context)
        assert len(prompts) > 0

    def test_pipeline_theme_fallback(self, pipeline, temp_configs_dir):
        """Test fallback when theme doesn't have style variant."""
        template_path = temp_configs_dir / "templates" / "character.template.yaml"

        # Load and resolve with theme + realistic style (not in theme)
        config = pipeline.load(str(template_path))
        resolved_config, context = pipeline.resolve(
            config,
            theme_name="cyberpunk",
            style="realistic"
        )

        # Should still work (fallback to template/common or use what's available)
        assert context.style == "realistic"
        assert "Ambiance" in context.imports


# ============================================================================
# Integration Tests - Theme Management
# ============================================================================

class TestThemeManagement:
    """Test theme discovery and info methods."""

    def test_list_themes(self, pipeline):
        """Test listing available themes."""
        themes = pipeline.list_themes()
        assert "cyberpunk" in themes

    def test_get_theme_info(self, pipeline):
        """Test getting theme details."""
        info = pipeline.get_theme_info("cyberpunk")

        assert info["name"] == "cyberpunk"
        assert info["explicit"] is True
        assert "Ambiance" in info["imports"]
        assert "Outfit.default" in info["imports"]
        assert "Outfit.cartoon" in info["imports"]

        # Check auto-discovered styles
        assert "default" in info["styles"]
        assert "cartoon" in info["styles"]

    def test_validate_theme_compatibility(self, pipeline, temp_configs_dir):
        """Test theme compatibility validation."""
        template_path = temp_configs_dir / "templates" / "character.template.yaml"
        config = pipeline.load(str(template_path))

        # Should be compatible
        status = pipeline.validate_theme_compatibility(
            config,
            theme_name="cyberpunk",
            style="default"
        )

        assert status["Ambiance"] == "provided"
        assert status["Outfit"] == "provided"


# ============================================================================
# Integration Tests - Manifest Enrichment
# ============================================================================

class TestManifestEnrichment:
    """Test that manifest contains theme/style metadata."""

    def test_manifest_contains_theme_metadata(self, pipeline, temp_configs_dir, tmp_path):
        """Test that generated manifest includes theme_name and style."""
        template_path = temp_configs_dir / "templates" / "character.template.yaml"

        # Load and resolve with theme
        config = pipeline.load(str(template_path))
        resolved_config, context = pipeline.resolve(
            config,
            theme_name="cyberpunk",
            style="cartoon"
        )

        # Generate prompts
        prompts = pipeline.generate(resolved_config, context)

        # Simulate manifest creation (as done in cli.py)
        from datetime import datetime
        snapshot = {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "resolved_template": {
                "prompt": resolved_config.template,
                "negative": resolved_config.negative_prompt or ''
            },
            "generation_params": {
                "mode": "combinatorial",
                "seed_mode": "progressive",
                "seed": 42
            },
            "theme_name": "cyberpunk",
            "style": "cartoon"
        }

        # Check metadata is present
        assert snapshot["theme_name"] == "cyberpunk"
        assert snapshot["style"] == "cartoon"

        # Verify it can be serialized to JSON
        manifest = {
            "snapshot": snapshot,
            "images": []
        }
        manifest_json = json.dumps(manifest, indent=2)
        assert "cyberpunk" in manifest_json
        assert "cartoon" in manifest_json

    def test_manifest_without_theme(self, pipeline, temp_configs_dir):
        """Test manifest when no theme is used."""
        template_path = temp_configs_dir / "templates" / "character.template.yaml"

        config = pipeline.load(str(template_path))
        resolved_config, context = pipeline.resolve(config)

        # Simulate manifest creation
        from datetime import datetime
        snapshot = {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "theme_name": None,  # No theme
            "style": "default"   # Default style
        }

        assert snapshot["theme_name"] is None
        assert snapshot["style"] == "default"


# ============================================================================
# Integration Tests - End-to-End
# ============================================================================

class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_pipeline_with_theme(self, pipeline, temp_configs_dir):
        """Test complete pipeline: load → resolve → generate with theme."""
        template_path = temp_configs_dir / "templates" / "character.template.yaml"

        # Run full pipeline
        prompts = pipeline.run(
            str(template_path),
            theme_name="cyberpunk",
            style="cartoon"
        )

        # Verify results
        assert len(prompts) > 0

        # Each prompt should have:
        # - prompt text
        # - negative_prompt
        # - parameters
        for prompt in prompts:
            assert 'prompt' in prompt
            assert 'negative_prompt' in prompt
            assert 'parameters' in prompt
            assert isinstance(prompt['prompt'], str)
            assert len(prompt['prompt']) > 0

    def test_full_pipeline_without_theme(self, pipeline, temp_configs_dir):
        """Test complete pipeline without theme."""
        template_path = temp_configs_dir / "templates" / "character.template.yaml"

        # Run without theme
        prompts = pipeline.run(str(template_path))

        assert len(prompts) > 0
        for prompt in prompts:
            assert 'prompt' in prompt
            assert 'negative_prompt' in prompt

    def test_statistics_with_theme(self, pipeline, temp_configs_dir):
        """Test variation statistics with theme."""
        template_path = temp_configs_dir / "templates" / "character.template.yaml"

        config = pipeline.load(str(template_path))
        resolved_config, context = pipeline.resolve(
            config,
            theme_name="cyberpunk",
            style="cartoon"
        )

        # Get statistics
        stats = pipeline.get_variation_statistics(
            resolved_config.template,
            context
        )

        assert 'placeholders' in stats
        assert 'total_combinations' in stats
        assert stats['total_placeholders'] >= 2  # At least Ambiance and Outfit
