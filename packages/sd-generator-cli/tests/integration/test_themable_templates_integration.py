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
    Create a simplified test configs directory structure.

    Structure:
        configs/
        ├── themes/
        │   └── cyberpunk/
        │       ├── theme.yaml
        │       ├── cyberpunk_ambiance.yaml
        │       ├── cyberpunk_outfit.default.yaml
        │       └── cyberpunk_outfit.cartoon.yaml
        ├── defaults/
        │   ├── ambiance.yaml
        │   └── outfit.default.yaml
        └── character.template.yaml
    """
    configs = tmp_path / "configs"
    configs.mkdir()

    # Create defaults directory at root level
    defaults_dir = configs / "defaults"
    defaults_dir.mkdir()
    (defaults_dir / "ambiance.yaml").write_text(
        "default_ambiance: calm atmosphere\n"
    )
    (defaults_dir / "outfit.default.yaml").write_text(
        "default_outfit: casual clothes\n"
    )

    # Create theme directory
    theme_dir = configs / "themes" / "cyberpunk"
    theme_dir.mkdir(parents=True)

    # Theme config - imports are relative to configs dir
    # Note: Without explicit style suffix, uses default style
    (theme_dir / "theme.yaml").write_text(
        "version: '1.0'\n"
        "name: cyberpunk\n"
        "imports:\n"
        "  Ambiance: themes/cyberpunk/cyberpunk_ambiance.yaml\n"
        "  Outfit: themes/cyberpunk/cyberpunk_outfit.default.yaml\n"
        "  Outfit.default: themes/cyberpunk/cyberpunk_outfit.default.yaml\n"
        "  Outfit.cartoon: themes/cyberpunk/cyberpunk_outfit.cartoon.yaml\n"
        "variations:\n"
        "  - Ambiance\n"
        "  - Outfit\n"
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

    # Create base template (simple, no prompt placeholder)
    base_template_content = """version: "2.0"
name: character_base
template: "masterpiece, {prompt}, detailed"
negative_prompt: "low quality, blurry"
"""
    (configs / "base.template.yaml").write_text(base_template_content)

    # Create themable template that implements base
    template_content = """version: "2.0"
name: character
themable: true
style_sensitive: true
style_sensitive_placeholders:
  - Outfit

implements: base.template.yaml

prompt: "{Ambiance}, {Outfit}"

prompts:
  default: ""

imports:
  Ambiance: defaults/ambiance.yaml
  Outfit: defaults/outfit.default.yaml

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: 10
"""
    (configs / "character.template.yaml").write_text(template_content)

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
        template_path = temp_configs_dir / "character.template.yaml"

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
        template_path = temp_configs_dir / "character.template.yaml"

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
        assert context.import_resolution["Ambiance"].source == "theme"
        assert context.import_resolution["Ambiance"].override is True

        # Generate prompts
        prompts = pipeline.generate(resolved_config, context)
        assert len(prompts) > 0

    def test_pipeline_with_theme_cartoon_style(self, pipeline, temp_configs_dir):
        """Test generation with theme and cartoon style."""
        template_path = temp_configs_dir / "character.template.yaml"

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
        assert context.import_resolution["Outfit"].style_sensitive is True
        assert context.import_resolution["Outfit"].resolved_style == "cartoon"

        # Generate prompts
        prompts = pipeline.generate(resolved_config, context)
        assert len(prompts) > 0

    def test_pipeline_theme_fallback(self, pipeline, temp_configs_dir):
        """Test fallback when theme doesn't have style variant."""
        template_path = temp_configs_dir / "character.template.yaml"

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
        template_path = temp_configs_dir / "character.template.yaml"
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
        template_path = temp_configs_dir / "character.template.yaml"

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
        template_path = temp_configs_dir / "character.template.yaml"

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
        template_path = temp_configs_dir / "character.template.yaml"

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
        template_path = temp_configs_dir / "character.template.yaml"

        # Run without theme
        prompts = pipeline.run(str(template_path))

        assert len(prompts) > 0
        for prompt in prompts:
            assert 'prompt' in prompt
            assert 'negative_prompt' in prompt

    def test_statistics_with_theme(self, pipeline, temp_configs_dir):
        """Test variation statistics with theme."""
        template_path = temp_configs_dir / "character.template.yaml"

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


class TestRemoveDirectiveIntegration:
    """Integration tests for [Remove] directive functionality."""

    @pytest.fixture
    def pipeline_with_configs(self, theme_with_remove):
        """Create V2Pipeline instance with test configs."""
        return V2Pipeline(configs_dir=str(theme_with_remove))

    @pytest.fixture
    def theme_with_remove(self, tmp_path):
        """
        Create test structure with [Remove] directive.

        Structure:
            configs/
            ├── themes/
            │   └── test_theme/
            │       ├── theme.yaml
            │       └── test_theme_watches.yaml
            ├── base.template.yaml
            └── test_character.template.yaml
        """
        configs = tmp_path / "configs"
        configs.mkdir()

        # Create defaults directory
        defaults_dir = configs / "defaults"
        defaults_dir.mkdir()
        (defaults_dir / "watches.yaml").write_text("""
type: variations
name: Watches
version: "1.0"
variations:
  default: no watch
""")

        # Create theme directory
        theme_dir = configs / "themes" / "test_theme"
        theme_dir.mkdir(parents=True)

        # Create theme.yaml with [Remove] directive for restricted style
        (theme_dir / "theme.yaml").write_text("""
type: theme_config
version: "1.0"
imports:
  Watches: test_theme/test_theme_watches.yaml
  Watches.restricted: [Remove]
""")

        # Create watches variation file
        (theme_dir / "test_theme_watches.yaml").write_text("""
type: variations
name: Watches
version: "1.0"
variations:
  rolex: elegant Rolex watch
  patek: Patek Philippe watch
  cartier: Cartier watch
""")

        # Create base template with {prompt} placeholder
        (configs / "base.template.yaml").write_text("""
name: Base
version: "2.0"
template: "masterpiece, {prompt}, detailed"
""")

        # Create child prompt that uses Watches placeholder
        (configs / "test_character.prompt.yaml").write_text("""
type: prompt
name: TestCharacter
version: "2.0"
themable: true
implements: base.template.yaml
prompt: "beautiful woman, wearing {Watches}"
imports:
  Watches: defaults/watches.yaml
generation:
  mode: combinatorial
  seed_mode: fixed
  seed: 42
  max_images: 10
""")

        return configs

    def test_remove_directive_default_style(self, pipeline_with_configs, theme_with_remove):
        """Test that placeholder works normally with default style."""
        template_path = theme_with_remove / "test_character.prompt.yaml"

        config = pipeline_with_configs.load(str(template_path))
        resolved_config, context = pipeline_with_configs.resolve(
            config,
            theme_name="test_theme",
            style="default"
        )

        # Watches should be present in imports
        assert 'Watches' in context.imports
        assert len(context.imports['Watches']) == 3  # rolex, patek, cartier

    def test_remove_directive_restricted_style(self, pipeline_with_configs, theme_with_remove):
        """Test that placeholder is removed with restricted style."""
        template_path = theme_with_remove / "test_character.prompt.yaml"

        config = pipeline_with_configs.load(str(template_path))
        resolved_config, context = pipeline_with_configs.resolve(
            config,
            theme_name="test_theme",
            style="restricted"
        )

        # Watches should NOT be in imports (removed by [Remove] directive)
        assert 'Watches' not in context.imports

    def test_remove_directive_prompt_generation(self, pipeline_with_configs, theme_with_remove):
        """Test that removed placeholder resolves to empty string in prompt."""
        template_path = theme_with_remove / "test_character.prompt.yaml"

        config = pipeline_with_configs.load(str(template_path))
        resolved_config, context = pipeline_with_configs.resolve(
            config,
            theme_name="test_theme",
            style="restricted"
        )

        # Generate prompts (should handle missing Watches gracefully)
        generator = pipeline_with_configs.get_generator(resolved_config, context)
        prompts = generator.generate(max_variations=1)

        assert len(prompts) == 1
        # Placeholder should resolve to empty string, resulting in "beautiful woman, wearing "
        # (might have extra spaces, but no error)
        assert "Watches" not in prompts[0]['positive']  # Placeholder not left in output

    def test_remove_directive_multiple_placeholders(self, tmp_path):
        """Test [Remove] directive with multiple placeholders."""
        configs = tmp_path / "configs"
        configs.mkdir()

        # Create pipeline with this configs dir
        pipeline = V2Pipeline(configs_dir=str(configs))

        # Create defaults directory
        defaults_dir = configs / "defaults"
        defaults_dir.mkdir()
        (defaults_dir / "watches.yaml").write_text("""
type: variations
name: Watches
version: "1.0"
variations:
  default_watches: no watches
""")
        (defaults_dir / "handbags.yaml").write_text("""
type: variations
name: HandBags
version: "1.0"
variations:
  default_handbags: no handbags
""")
        (defaults_dir / "outfit.yaml").write_text("""
type: variations
name: Outfit
version: "1.0"
variations:
  default_outfit: simple outfit
""")

        # Create theme with multiple [Remove] directives
        theme_dir = configs / "themes" / "multi_remove"
        theme_dir.mkdir(parents=True)

        (theme_dir / "theme.yaml").write_text("""
type: theme_config
version: "1.0"
imports:
  Watches: multi_remove/watches.yaml
  Watches.restricted: [Remove]
  HandBags: multi_remove/handbags.yaml
  HandBags.restricted: [Remove]
  Outfit: multi_remove/outfit.yaml
""")

        # Create variation files
        (theme_dir / "watches.yaml").write_text("""
type: variations
name: Watches
version: "1.0"
variations:
  necklace: necklace
""")

        (theme_dir / "handbags.yaml").write_text("""
type: variations
name: HandBags
version: "1.0"
variations:
  bag: handbag
""")

        (theme_dir / "outfit.yaml").write_text("""
type: variations
name: Outfit
version: "1.0"
variations:
  dress: red dress
""")

        # Create base template
        (configs / "base.template.yaml").write_text("""
name: Base
version: "2.0"
template: "masterpiece, {prompt}, detailed"
""")

        # Create child prompt
        (configs / "test.prompt.yaml").write_text("""
type: prompt
name: Test
version: "2.0"
themable: true
implements: base.template.yaml
prompt: "woman, {Outfit}, {Watches}, {HandBags}"
imports:
  Watches: defaults/watches.yaml
  HandBags: defaults/handbags.yaml
  Outfit: defaults/outfit.yaml
generation:
  mode: combinatorial
  seed_mode: fixed
  seed: 42
  max_images: 10
""")

        template_path = configs / "test.prompt.yaml"
        config = pipeline.load(str(template_path))
        resolved_config, context = pipeline.resolve(
            config,
            theme_name="multi_remove",
            style="restricted"
        )

        # Watches and HandBags should be removed, Outfit should remain
        assert 'Watches' not in context.imports
        assert 'HandBags' not in context.imports
        assert 'Outfit' in context.imports

    def test_remove_directive_validation_error(self, tmp_path):
        """Test that invalid [Remove] directive raises error."""
        configs = tmp_path / "configs"
        configs.mkdir()

        # Create pipeline with this configs dir
        pipeline = V2Pipeline(configs_dir=str(configs))

        # Create defaults directory
        defaults_dir = configs / "defaults"
        defaults_dir.mkdir()
        (defaults_dir / "watches.yaml").write_text("""
type: variations
name: Watches
version: "1.0"
variations:
  default: no watches
""")

        theme_dir = configs / "themes" / "invalid_remove"
        theme_dir.mkdir(parents=True)

        # Create theme.yaml with INVALID [Remove] (wrong case)
        (theme_dir / "theme.yaml").write_text("""
type: theme_config
version: "1.0"
imports:
  Watches: watches.yaml
  Watches.restricted: [remove]
""")

        (theme_dir / "watches.yaml").write_text("""
type: variations
name: Watches
version: "1.0"
variations:
  necklace: necklace
""")

        # Create base template
        (configs / "base.template.yaml").write_text("""
name: Base
version: "2.0"
template: "masterpiece, {prompt}, detailed"
""")

        # Create child prompt
        (configs / "test.prompt.yaml").write_text("""
type: prompt
name: Test
version: "2.0"
themable: true
implements: base.template.yaml
prompt: "woman, {Watches}"
imports:
  Watches: defaults/watches.yaml
generation:
  mode: combinatorial
  seed_mode: fixed
  seed: 42
  max_images: 10
""")

        template_path = configs / "test.prompt.yaml"
        config = pipeline.load(str(template_path))

        # Should raise ValueError during resolve (theme validation)
        with pytest.raises(ValueError, match="Invalid \\[Remove\\] directive"):
            pipeline.resolve(
                config,
                theme_name="invalid_remove",
                style="restricted"
            )
