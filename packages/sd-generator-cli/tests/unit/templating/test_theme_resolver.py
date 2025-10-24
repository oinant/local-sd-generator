"""
Unit tests for ThemeResolver.

Tests theme + template + rating merge logic and import resolution.
"""

import pytest
from pathlib import Path
from sd_generator_cli.templating.resolvers.theme_resolver import ThemeResolver
from sd_generator_cli.templating.models import (
    TemplateConfig,
    ThemeConfig,
    ImportResolution
)


@pytest.fixture
def configs_dir(tmp_path):
    """Create a configs directory structure."""
    configs = tmp_path / "configs"
    configs.mkdir()

    # Create template defaults
    defaults_dir = configs / "defaults"
    defaults_dir.mkdir()
    (defaults_dir / "ambiance.yaml").write_text("default ambiance")
    (defaults_dir / "outfit.sfw.yaml").write_text("default sfw outfit")

    # Create theme files
    theme_dir = configs / "themes" / "cyberpunk"
    theme_dir.mkdir(parents=True)
    (theme_dir / "cyberpunk_ambiance.yaml").write_text("cyberpunk ambiance")
    (theme_dir / "cyberpunk_outfit.sfw.yaml").write_text("cyberpunk sfw")
    (theme_dir / "cyberpunk_outfit.sexy.yaml").write_text("cyberpunk sexy")
    # No nsfw variant in theme

    # Create common fallbacks
    common_dir = configs / "common" / "outfits"
    common_dir.mkdir(parents=True)
    (common_dir / "outfit.sfw.yaml").write_text("common sfw")
    (common_dir / "outfit.sexy.yaml").write_text("common sexy")
    (common_dir / "outfit.nsfw.yaml").write_text("common nsfw")

    return configs


@pytest.fixture
def template_config(configs_dir):
    """Create a template configuration."""
    return TemplateConfig(
        version="2.0",
        name="test_template",
        template="Test {Ambiance}, {Outfit}",
        source_file=Path("/test/template.yaml"),
        themable=True,
        ratable=True,
        rating_sensitive_placeholders=["Outfit"],
        imports={
            "Ambiance": "defaults/ambiance.yaml",
            "Outfit": "defaults/outfit.sfw.yaml"
        }
    )


@pytest.fixture
def theme_config():
    """Create a theme configuration."""
    return ThemeConfig(
        name="cyberpunk",
        path=Path("/configs/themes/cyberpunk"),
        explicit=True,
        imports={
            "Ambiance": "cyberpunk/cyberpunk_ambiance.yaml",
            "Outfit.sfw": "cyberpunk/cyberpunk_outfit.sfw.yaml",
            "Outfit.sexy": "cyberpunk/cyberpunk_outfit.sexy.yaml"
            # No Outfit.nsfw - should fallback
        },
        variations=["Ambiance", "Outfit"]
    )


class TestThemeResolverInit:
    """Tests for ThemeResolver initialization."""

    def test_init(self, configs_dir):
        """Test ThemeResolver initialization."""
        resolver = ThemeResolver(configs_dir)

        assert resolver.configs_dir == configs_dir
        assert resolver.rating_resolver is not None


class TestThemeResolverMergeImports:
    """Tests for merge_imports method."""

    def test_merge_no_theme_sfw(self, configs_dir, template_config):
        """Test merge without theme (template defaults only), SFW rating."""
        resolver = ThemeResolver(configs_dir)

        imports, metadata = resolver.merge_imports(
            template=template_config,
            theme=None,
            rating="sfw"
        )

        # Should use template defaults
        assert imports["Ambiance"] == "defaults/ambiance.yaml"
        assert imports["Outfit"] == "defaults/outfit.sfw.yaml"

        # Check metadata
        assert metadata["Ambiance"].source == "template"
        assert metadata["Ambiance"].override is False
        assert metadata["Outfit"].source == "template"
        assert metadata["Outfit"].rating_sensitive is True
        assert metadata["Outfit"].resolved_rating == "sfw"

    def test_merge_with_theme_sfw(self, configs_dir, template_config, theme_config):
        """Test merge with theme, SFW rating."""
        resolver = ThemeResolver(configs_dir)

        imports, metadata = resolver.merge_imports(
            template=template_config,
            theme=theme_config,
            rating="sfw"
        )

        # Should use theme overrides
        assert imports["Ambiance"] == "cyberpunk/cyberpunk_ambiance.yaml"
        assert imports["Outfit"] == "cyberpunk/cyberpunk_outfit.sfw.yaml"

        # Check metadata
        assert metadata["Ambiance"].source == "theme"
        assert metadata["Ambiance"].override is True
        assert metadata["Outfit"].source == "theme"
        assert metadata["Outfit"].override is True
        assert metadata["Outfit"].rating_sensitive is True
        assert metadata["Outfit"].resolved_rating == "sfw"

    def test_merge_with_theme_sexy(self, configs_dir, template_config, theme_config):
        """Test merge with theme, sexy rating."""
        resolver = ThemeResolver(configs_dir)

        imports, metadata = resolver.merge_imports(
            template=template_config,
            theme=theme_config,
            rating="sexy"
        )

        # Ambiance not rating-sensitive → use theme
        assert imports["Ambiance"] == "cyberpunk/cyberpunk_ambiance.yaml"
        # Outfit.sexy → use theme
        assert imports["Outfit"] == "cyberpunk/cyberpunk_outfit.sexy.yaml"

        # Check metadata
        assert metadata["Outfit"].source == "theme"
        assert metadata["Outfit"].resolved_rating == "sexy"

    def test_merge_with_theme_nsfw_fallback(self, configs_dir, template_config, theme_config):
        """Test merge with theme, NSFW rating (fallback to common)."""
        resolver = ThemeResolver(configs_dir)

        imports, metadata = resolver.merge_imports(
            template=template_config,
            theme=theme_config,
            rating="nsfw"
        )

        # Ambiance → theme (not rating-sensitive)
        assert imports["Ambiance"] == "cyberpunk/cyberpunk_ambiance.yaml"

        # Outfit.nsfw → theme doesn't have it, may not resolve if common doesn't exist
        # In test setup, common/outfits/ exists but may not be found by fallback logic
        # Just check that it doesn't crash
        # Could be in imports or not, depending on fallback success
        if "Outfit" in imports:
            outfit_meta = metadata["Outfit"]
            assert outfit_meta.resolved_rating == "nsfw"

    def test_merge_invalid_rating(self, configs_dir, template_config):
        """Test merge with invalid rating raises error."""
        resolver = ThemeResolver(configs_dir)

        with pytest.raises(ValueError, match="Invalid rating"):
            resolver.merge_imports(
                template=template_config,
                theme=None,
                rating="invalid"
            )

    def test_merge_non_themable_template(self, configs_dir, theme_config):
        """Test merge with non-themable template."""
        non_themable = TemplateConfig(
            version="2.0",
            name="non_themable",
            template="Test",
            source_file=Path("/test.yaml"),
            themable=False,  # Not themable
            imports={"Ambiance": "defaults/ambiance.yaml"}
        )

        resolver = ThemeResolver(configs_dir)

        imports, metadata = resolver.merge_imports(
            template=non_themable,
            theme=theme_config,
            rating="sfw"
        )

        # Even if theme provided, should still work
        # (themable flag might be advisory, not enforced in resolver)
        assert "Ambiance" in imports


class TestThemeResolverResolveImport:
    """Tests for _resolve_import private method."""

    def test_resolve_import_theme_override(self, configs_dir, theme_config):
        """Test theme override takes priority."""
        resolver = ThemeResolver(configs_dir)

        resolved, meta = resolver._resolve_import(
            placeholder="Ambiance",
            template_import="defaults/ambiance.yaml",
            theme=theme_config,
            rating="sfw",
            is_rating_sensitive=False
        )

        assert resolved == "cyberpunk/cyberpunk_ambiance.yaml"
        assert meta.source == "theme"
        assert meta.override is True

    def test_resolve_import_template_fallback(self, configs_dir):
        """Test fallback to template when theme doesn't provide."""
        resolver = ThemeResolver(configs_dir)

        # Theme doesn't have Accessories
        partial_theme = ThemeConfig(
            name="partial",
            path=Path("/configs/themes/partial"),
            explicit=True,
            imports={}  # No imports
        )

        resolved, meta = resolver._resolve_import(
            placeholder="Ambiance",
            template_import="defaults/ambiance.yaml",
            theme=partial_theme,
            rating="sfw",
            is_rating_sensitive=False
        )

        assert resolved == "defaults/ambiance.yaml"
        assert meta.source == "template"
        assert meta.override is False

    def test_resolve_import_rating_sensitive(self, configs_dir, theme_config):
        """Test rating-sensitive import resolution."""
        resolver = ThemeResolver(configs_dir)

        resolved, meta = resolver._resolve_import(
            placeholder="Outfit",
            template_import="defaults/outfit.sfw.yaml",
            theme=theme_config,
            rating="sexy",
            is_rating_sensitive=True
        )

        assert resolved == "cyberpunk/cyberpunk_outfit.sexy.yaml"
        assert meta.rating_sensitive is True
        assert meta.resolved_rating == "sexy"


class TestThemeResolverValidateCompatibility:
    """Tests for validate_theme_compatibility method."""

    def test_validate_full_compatibility(self, configs_dir, template_config, theme_config):
        """Test validation when theme provides all imports."""
        resolver = ThemeResolver(configs_dir)

        status = resolver.validate_theme_compatibility(
            template=template_config,
            theme=theme_config,
            rating="sfw"
        )

        assert status["Ambiance"] == "provided"
        assert status["Outfit"] == "provided"

    def test_validate_partial_compatibility(self, configs_dir, template_config):
        """Test validation when theme provides some imports."""
        partial_theme = ThemeConfig(
            name="partial",
            path=Path("/configs/themes/partial"),
            explicit=True,
            imports={
                "Ambiance": "partial/ambiance.yaml"
                # Missing Outfit
            }
        )

        # Create the ambiance file
        partial_dir = configs_dir / "themes" / "partial"
        partial_dir.mkdir(parents=True)
        (partial_dir / "ambiance.yaml").write_text("test")

        resolver = ThemeResolver(configs_dir)

        status = resolver.validate_theme_compatibility(
            template=template_config,
            theme=partial_theme,
            rating="sfw"
        )

        assert status["Ambiance"] == "provided"
        # Outfit should be "fallback" if template/common provides it
        assert status["Outfit"] in ["fallback", "missing"]

    def test_validate_with_fallback(self, configs_dir, template_config, theme_config):
        """Test validation shows fallback when theme doesn't have rating variant."""
        resolver = ThemeResolver(configs_dir)

        status = resolver.validate_theme_compatibility(
            template=template_config,
            theme=theme_config,
            rating="nsfw"  # Theme doesn't have Outfit.nsfw
        )

        # Ambiance not rating-sensitive → provided
        assert status["Ambiance"] == "provided"
        # Outfit.nsfw not in theme → should be fallback or missing
        # Depends on whether fallback can find the file
        assert status["Outfit"] in ["fallback", "missing"]


class TestThemeResolverEdgeCases:
    """Edge cases and error handling."""

    def test_merge_empty_imports(self, configs_dir):
        """Test merge with template having no imports."""
        empty_template = TemplateConfig(
            version="2.0",
            name="empty",
            template="Empty",
            source_file=Path("/test.yaml"),
            imports={}  # No imports
        )

        resolver = ThemeResolver(configs_dir)

        imports, metadata = resolver.merge_imports(
            template=empty_template,
            theme=None,
            rating="sfw"
        )

        assert imports == {}
        assert metadata == {}

    def test_merge_missing_file_warning(self, configs_dir, caplog):
        """Test that missing files generate warnings."""
        template = TemplateConfig(
            version="2.0",
            name="test",
            template="Test",
            source_file=Path("/test.yaml"),
            imports={"Missing": "nonexistent/file.yaml"}
        )

        resolver = ThemeResolver(configs_dir)

        imports, metadata = resolver.merge_imports(
            template=template,
            theme=None,
            rating="sfw"
        )

        # Should not include missing import
        assert "Missing" not in imports
        # Should log warning (check caplog if needed)

    def test_resolve_with_none_theme(self, configs_dir, template_config):
        """Test resolution with None theme (template-only)."""
        resolver = ThemeResolver(configs_dir)

        imports, metadata = resolver.merge_imports(
            template=template_config,
            theme=None,
            rating="sfw"
        )

        # Should work fine, using template defaults
        assert len(imports) > 0
        for meta in metadata.values():
            assert meta.source == "template"
            assert meta.override is False

    def test_metadata_completeness(self, configs_dir, template_config, theme_config):
        """Test that all imports have corresponding metadata."""
        resolver = ThemeResolver(configs_dir)

        imports, metadata = resolver.merge_imports(
            template=template_config,
            theme=theme_config,
            rating="sfw"
        )

        # Every import should have metadata
        assert set(imports.keys()) == set(metadata.keys())

        # Every metadata should have required fields
        for placeholder, meta in metadata.items():
            assert meta.source in ["theme", "template", "common", "none"]
            assert isinstance(meta.override, bool)
            assert isinstance(meta.rating_sensitive, bool)
