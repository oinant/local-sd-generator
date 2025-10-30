"""
Unit tests for ThemeLoader.

Tests theme discovery and loading (explicit and implicit themes).
"""

import pytest
from pathlib import Path
from sd_generator_cli.templating.loaders.theme_loader import ThemeLoader
from sd_generator_cli.templating.models import ThemeConfig


@pytest.fixture
def temp_configs_dir(tmp_path):
    """Create a temporary configs directory with theme structure."""
    configs_dir = tmp_path / "configs"
    themes_dir = configs_dir / "themes"
    themes_dir.mkdir(parents=True)
    return configs_dir


@pytest.fixture
def explicit_theme(temp_configs_dir):
    """Create an explicit theme with theme.yaml."""
    theme_dir = temp_configs_dir / "themes" / "cyberpunk"
    theme_dir.mkdir()

    # Create theme.yaml
    theme_yaml = theme_dir / "theme.yaml"
    theme_yaml.write_text("""
type: theme_config
version: "1.0"
imports:
  Ambiance: cyberpunk/cyberpunk_ambiance.yaml
  Locations: cyberpunk/cyberpunk_locations.yaml
  Outfit.sfw: cyberpunk/cyberpunk_outfit.sfw.yaml
  Outfit.sexy: cyberpunk/cyberpunk_outfit.sexy.yaml
  Outfit.nsfw: cyberpunk/cyberpunk_outfit.nsfw.yaml
""")

    # Create referenced files
    (theme_dir / "cyberpunk_ambiance.yaml").write_text("data: test")
    (theme_dir / "cyberpunk_locations.yaml").write_text("data: test")
    (theme_dir / "cyberpunk_outfit.sfw.yaml").write_text("data: test")
    (theme_dir / "cyberpunk_outfit.sexy.yaml").write_text("data: test")
    (theme_dir / "cyberpunk_outfit.nsfw.yaml").write_text("data: test")

    return temp_configs_dir


@pytest.fixture
def implicit_theme(temp_configs_dir):
    """Create an implicit theme (no theme.yaml, inferred from files)."""
    theme_dir = temp_configs_dir / "themes" / "rockstar"
    theme_dir.mkdir()

    # Create theme files with naming convention
    (theme_dir / "rockstar_ambiance.yaml").write_text("data: test")
    (theme_dir / "rockstar_locations.yaml").write_text("data: test")
    (theme_dir / "rockstar_outfit.sfw.yaml").write_text("data: test")
    (theme_dir / "rockstar_outfit.sexy.yaml").write_text("data: test")
    (theme_dir / "rockstar_hair_color.yaml").write_text("data: test")

    return temp_configs_dir


@pytest.fixture
def multi_theme(temp_configs_dir):
    """Create multiple themes for discovery testing."""
    # Explicit theme: cyberpunk
    cyber_dir = temp_configs_dir / "themes" / "cyberpunk"
    cyber_dir.mkdir()
    (cyber_dir / "theme.yaml").write_text("""
type: theme_config
version: "1.0"
imports:
  Ambiance: cyberpunk/cyberpunk_ambiance.yaml
""")
    (cyber_dir / "cyberpunk_ambiance.yaml").write_text("data: test")

    # Implicit theme: pirates
    pirates_dir = temp_configs_dir / "themes" / "pirates"
    pirates_dir.mkdir()
    (pirates_dir / "pirates_ambiance.yaml").write_text("data: test")
    (pirates_dir / "pirates_outfit.sfw.yaml").write_text("data: test")

    return temp_configs_dir


class TestThemeLoader:
    """Tests for ThemeLoader class."""

    def test_init(self, temp_configs_dir):
        """Test ThemeLoader initialization."""
        loader = ThemeLoader(temp_configs_dir)

        assert loader.configs_dir == temp_configs_dir
        assert loader.themes_dir == temp_configs_dir / "themes"

    def test_discover_themes_empty(self, temp_configs_dir):
        """Test discovery with no themes."""
        loader = ThemeLoader(temp_configs_dir)
        themes = loader.discover_themes()

        assert themes == []

    def test_discover_themes_explicit(self, explicit_theme):
        """Test discovery of explicit theme."""
        loader = ThemeLoader(explicit_theme)
        themes = loader.discover_themes()

        assert len(themes) == 1
        theme = themes[0]

        assert theme.name == "cyberpunk"
        assert theme.explicit is True
        assert "Ambiance" in theme.imports
        assert "Locations" in theme.imports
        assert "Outfit.sfw" in theme.imports
        assert "Outfit.sexy" in theme.imports
        assert "Outfit.nsfw" in theme.imports

    def test_discover_themes_implicit(self, implicit_theme):
        """Test discovery of implicit theme."""
        loader = ThemeLoader(implicit_theme)
        themes = loader.discover_themes()

        assert len(themes) == 1
        theme = themes[0]

        assert theme.name == "rockstar"
        assert theme.explicit is False
        assert "Ambiance" in theme.imports
        assert "Locations" in theme.imports
        assert "Outfit.sfw" in theme.imports
        assert "Outfit.sexy" in theme.imports
        assert "HairColor" in theme.imports

    def test_discover_themes_multiple(self, multi_theme):
        """Test discovery of multiple themes."""
        loader = ThemeLoader(multi_theme)
        themes = loader.discover_themes()

        assert len(themes) == 2
        theme_names = {t.name for t in themes}
        assert theme_names == {"cyberpunk", "pirates"}

    def test_load_theme_explicit(self, explicit_theme):
        """Test loading explicit theme by name."""
        loader = ThemeLoader(explicit_theme)
        theme = loader.load_theme("cyberpunk")

        assert theme is not None
        assert theme.name == "cyberpunk"
        assert theme.explicit is True
        assert len(theme.imports) == 5

    def test_load_theme_implicit(self, implicit_theme):
        """Test loading implicit theme by name."""
        loader = ThemeLoader(implicit_theme)
        theme = loader.load_theme("rockstar")

        assert theme is not None
        assert theme.name == "rockstar"
        assert theme.explicit is False
        assert "Ambiance" in theme.imports

    def test_load_theme_not_found(self, temp_configs_dir):
        """Test loading non-existent theme."""
        loader = ThemeLoader(temp_configs_dir)
        theme = loader.load_theme("nonexistent")

        assert theme is None

    def test_load_explicit_theme_imports(self, explicit_theme):
        """Test explicit theme import paths."""
        loader = ThemeLoader(explicit_theme)
        theme = loader.load_theme("cyberpunk")

        assert theme.imports["Ambiance"] == "cyberpunk/cyberpunk_ambiance.yaml"
        assert theme.imports["Locations"] == "cyberpunk/cyberpunk_locations.yaml"
        assert theme.imports["Outfit.sfw"] == "cyberpunk/cyberpunk_outfit.sfw.yaml"

    def test_load_implicit_theme_imports(self, implicit_theme):
        """Test implicit theme import inference."""
        loader = ThemeLoader(implicit_theme)
        theme = loader.load_theme("rockstar")

        # Implicit themes should infer paths from filenames
        assert theme.imports["Ambiance"] == "rockstar/rockstar_ambiance.yaml"
        assert theme.imports["Locations"] == "rockstar/rockstar_locations.yaml"
        assert theme.imports["Outfit.sfw"] == "rockstar/rockstar_outfit.sfw.yaml"
        assert theme.imports["Outfit.sexy"] == "rockstar/rockstar_outfit.sexy.yaml"
        assert theme.imports["HairColor"] == "rockstar/rockstar_hair_color.yaml"

    def test_variations_extraction_explicit(self, explicit_theme):
        """Test variations extraction from explicit theme."""
        loader = ThemeLoader(explicit_theme)
        theme = loader.load_theme("cyberpunk")

        # Should extract unique base placeholders
        assert set(theme.variations) == {"Ambiance", "Locations", "Outfit"}

    def test_variations_extraction_implicit(self, implicit_theme):
        """Test variations extraction from implicit theme."""
        loader = ThemeLoader(implicit_theme)
        theme = loader.load_theme("rockstar")

        assert set(theme.variations) == {"Ambiance", "Locations", "Outfit", "HairColor"}

    def test_get_theme_variants(self, explicit_theme):
        """Test getting rating variants for a placeholder."""
        loader = ThemeLoader(explicit_theme)
        variants = loader.get_theme_variants("cyberpunk", "Outfit")

        assert set(variants) == {"nsfw", "sfw", "sexy"}

    def test_get_theme_variants_no_variants(self, explicit_theme):
        """Test getting variants for placeholder without ratings."""
        loader = ThemeLoader(explicit_theme)
        variants = loader.get_theme_variants("cyberpunk", "Ambiance")

        assert variants == []

    def test_get_theme_variants_theme_not_found(self, temp_configs_dir):
        """Test getting variants for non-existent theme."""
        loader = ThemeLoader(temp_configs_dir)
        variants = loader.get_theme_variants("nonexistent", "Outfit")

        assert variants == []

    def test_filename_to_placeholder_basic(self, temp_configs_dir):
        """Test filename to placeholder conversion (basic)."""
        loader = ThemeLoader(temp_configs_dir)

        assert loader._filename_to_placeholder("ambiance") == "Ambiance"
        assert loader._filename_to_placeholder("locations") == "Locations"

    def test_filename_to_placeholder_with_rating(self, temp_configs_dir):
        """Test filename to placeholder conversion (with rating suffix)."""
        loader = ThemeLoader(temp_configs_dir)

        assert loader._filename_to_placeholder("outfit.sfw") == "Outfit.sfw"
        assert loader._filename_to_placeholder("outfit.sexy") == "Outfit.sexy"
        assert loader._filename_to_placeholder("outfit.nsfw") == "Outfit.nsfw"

    def test_filename_to_placeholder_multi_word(self, temp_configs_dir):
        """Test filename to placeholder conversion (multi-word)."""
        loader = ThemeLoader(temp_configs_dir)

        assert loader._filename_to_placeholder("hair_color") == "HairColor"
        assert loader._filename_to_placeholder("hair_color.sfw") == "HairColor.sfw"
        assert loader._filename_to_placeholder("skin_type") == "SkinType"

    def test_extract_variations_from_imports(self, temp_configs_dir):
        """Test extracting base variations from import keys."""
        loader = ThemeLoader(temp_configs_dir)

        imports = {
            "Outfit.sfw": "path1",
            "Outfit.sexy": "path2",
            "Outfit.nsfw": "path3",
            "Ambiance": "path4",
            "HairColor": "path5",
            "HairColor.sexy": "path6"
        }

        variations = loader._extract_variations_from_imports(imports)

        assert set(variations) == {"Ambiance", "HairColor", "Outfit"}
        assert variations == sorted(variations)  # Should be sorted


class TestThemeLoaderEdgeCases:
    """Edge cases and error handling."""

    def test_no_themes_directory(self, temp_configs_dir):
        """Test when themes/ directory doesn't exist."""
        # Don't create themes/ directory
        loader = ThemeLoader(temp_configs_dir)
        themes = loader.discover_themes()

        assert themes == []

    def test_empty_theme_directory(self, temp_configs_dir):
        """Test theme directory with no valid files."""
        theme_dir = temp_configs_dir / "themes" / "empty"
        theme_dir.mkdir(parents=True)
        # Create a non-yaml file
        (theme_dir / "readme.txt").write_text("Empty theme")

        loader = ThemeLoader(temp_configs_dir)
        theme = loader.load_theme("empty")

        # Should return None for implicit theme with no yaml files
        assert theme is None

    def test_malformed_theme_yaml(self, temp_configs_dir):
        """Test handling of malformed theme.yaml."""
        theme_dir = temp_configs_dir / "themes" / "broken"
        theme_dir.mkdir(parents=True)
        (theme_dir / "theme.yaml").write_text("invalid: yaml: syntax: [")

        loader = ThemeLoader(temp_configs_dir)

        # Should raise YAML parsing error
        with pytest.raises(Exception):
            loader.load_theme("broken")

    def test_theme_yaml_missing_imports(self, temp_configs_dir):
        """Test theme.yaml without imports field."""
        theme_dir = temp_configs_dir / "themes" / "minimal"
        theme_dir.mkdir(parents=True)
        (theme_dir / "theme.yaml").write_text("""
type: theme_config
version: "1.0"
""")

        loader = ThemeLoader(temp_configs_dir)
        theme = loader.load_theme("minimal")

        assert theme is not None
        assert theme.imports == {}
        assert theme.variations == []


class TestRemoveDirectiveValidation:
    """Tests for [Remove] directive validation in ThemeLoader."""

    def test_validate_remove_directive_valid(self, temp_configs_dir):
        """Test that valid [Remove] directive passes validation."""
        loader = ThemeLoader(temp_configs_dir)

        imports = {
            "Outfit": "outfit.yaml",
            "Hair.xxx": ["Remove"]  # Valid [Remove] directive
        }

        # Should not raise
        loader._validate_remove_directives(imports, Path("test.yaml"))

    def test_validate_remove_directive_multiple_removes(self, temp_configs_dir):
        """Test that multiple [Remove] directives are valid."""
        loader = ThemeLoader(temp_configs_dir)

        imports = {
            "Outfit.xxx": ["Remove"],
            "Hair.xxx": ["Remove"],
            "Jewelry.xxx": ["Remove"]
        }

        # Should not raise
        loader._validate_remove_directives(imports, Path("test.yaml"))

    def test_validate_remove_directive_wrong_case(self, temp_configs_dir):
        """Test that [Remove] with wrong case raises ValueError."""
        loader = ThemeLoader(temp_configs_dir)

        imports = {
            "Outfit.xxx": ["remove"]  # Wrong case
        }

        with pytest.raises(ValueError, match="Invalid \\[Remove\\] directive"):
            loader._validate_remove_directives(imports, Path("test.yaml"))

    def test_validate_remove_directive_empty_list(self, temp_configs_dir):
        """Test that empty list raises ValueError."""
        loader = ThemeLoader(temp_configs_dir)

        imports = {
            "Outfit.xxx": []  # Empty list
        }

        with pytest.raises(ValueError, match="Invalid \\[Remove\\] directive"):
            loader._validate_remove_directives(imports, Path("test.yaml"))

    def test_validate_remove_directive_multiple_elements(self, temp_configs_dir):
        """Test that list with multiple elements raises ValueError."""
        loader = ThemeLoader(temp_configs_dir)

        imports = {
            "Outfit.xxx": ["Remove", "extra"]  # Too many elements
        }

        with pytest.raises(ValueError, match="Invalid \\[Remove\\] directive"):
            loader._validate_remove_directives(imports, Path("test.yaml"))

    def test_validate_remove_directive_mixed_valid_invalid(self, temp_configs_dir):
        """Test that mix of valid and invalid imports raises on invalid."""
        loader = ThemeLoader(temp_configs_dir)

        imports = {
            "Outfit": "outfit.yaml",  # Valid file path
            "Hair.xxx": ["Remove"],  # Valid [Remove]
            "Jewelry.xxx": ["REMOVE"]  # Invalid case
        }

        with pytest.raises(ValueError, match="Invalid \\[Remove\\] directive"):
            loader._validate_remove_directives(imports, Path("test.yaml"))

    def test_validate_remove_directive_nested_imports_valid(self, temp_configs_dir):
        """Test that [Remove] in nested imports is validated."""
        loader = ThemeLoader(temp_configs_dir)

        imports = {
            "chunks": {
                "positive": "positive.chunk.yaml",
                "negative.xxx": ["Remove"]  # Nested [Remove]
            }
        }

        # Should not raise
        loader._validate_remove_directives(imports, Path("test.yaml"))

    def test_validate_remove_directive_nested_imports_invalid(self, temp_configs_dir):
        """Test that invalid [Remove] in nested imports raises ValueError."""
        loader = ThemeLoader(temp_configs_dir)

        imports = {
            "chunks": {
                "positive": "positive.chunk.yaml",
                "negative.xxx": ["remove"]  # Invalid nested [Remove]
            }
        }

        with pytest.raises(ValueError, match="Invalid \\[Remove\\] directive"):
            loader._validate_remove_directives(imports, Path("test.yaml"))

    def test_validate_remove_directive_error_message_contains_placeholder(self, temp_configs_dir):
        """Test that error message contains placeholder name."""
        loader = ThemeLoader(temp_configs_dir)

        imports = {
            "SpecificPlaceholder.xxx": ["WRONG"]
        }

        with pytest.raises(ValueError, match="'SpecificPlaceholder\\.xxx'"):
            loader._validate_remove_directives(imports, Path("test.yaml"))

    def test_load_explicit_theme_validates_remove(self, temp_configs_dir):
        """Test that load_explicit_theme() validates [Remove] directives."""
        theme_dir = temp_configs_dir / "themes" / "test"
        theme_dir.mkdir(parents=True)

        # Create theme.yaml with invalid [Remove]
        theme_yaml = theme_dir / "theme.yaml"
        theme_yaml.write_text("""
type: theme_config
version: "1.0"
imports:
  Outfit: outfit.yaml
  Hair.xxx: [remove]
""")

        loader = ThemeLoader(temp_configs_dir)

        # Should raise during load
        with pytest.raises(ValueError, match="Invalid \\[Remove\\] directive"):
            loader.load_theme("test")
