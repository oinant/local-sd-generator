"""
Unit tests for InheritanceResolver (Phase 3).

Tests cover:
- Simple inheritance (1 level)
- Multi-level inheritance (grandparent → parent → child)
- Merge rules for each config section
- Cache behavior
- Template override warnings
- Type validation for chunks
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
import logging

from templating.v2.resolvers.inheritance_resolver import InheritanceResolver
from templating.v2.loaders.yaml_loader import YamlLoader
from templating.v2.loaders.parser import ConfigParser
from templating.v2.models.config_models import (
    TemplateConfig,
    ChunkConfig,
    PromptConfig,
    GenerationConfig
)


class TestInheritanceResolverBasic:
    """Test basic inheritance resolution."""

    def test_no_inheritance_returns_unchanged(self, tmp_path):
        """Test that configs without implements: are returned unchanged."""
        # Setup
        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        template_file = tmp_path / "simple.template.yaml"
        config = TemplateConfig(
            version="2.0",
            name="Simple",
            template="test template",
            source_file=template_file,
            implements=None  # No inheritance
        )

        # Execute
        result = resolver.resolve_implements(config)

        # Assert - should be the same object
        assert result is config
        assert result.template == "test template"

    def test_simple_inheritance_template(self, tmp_path):
        """Test simple 1-level inheritance for TemplateConfig."""
        # Create parent template
        parent_file = tmp_path / "parent.template.yaml"
        parent_data = {
            "version": "2.0",
            "name": "Parent",
            "template": "parent template",
            "parameters": {"width": 832, "height": 1216},
            "imports": {"Character": "../chunks/char.chunk.yaml"}
        }
        parent_file.write_text(yaml.dump(parent_data))

        # Create child template
        child_file = tmp_path / "child.template.yaml"
        child_data = {
            "version": "2.0",
            "name": "Child",
            "implements": "parent.template.yaml",
            "template": "child template",
            "parameters": {"steps": 30}  # Override
        }

        # Setup
        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        # Parse child
        child_config = parser.parse_template(child_data, child_file)

        # Execute
        result = resolver.resolve_implements(child_config)

        # Assert
        assert result.name == "Child"
        assert result.template == "child template"
        # Parameters should be merged (parent + child)
        assert result.parameters["width"] == 832  # From parent
        assert result.parameters["height"] == 1216  # From parent
        assert result.parameters["steps"] == 30  # From child
        # Imports should be inherited
        assert "Character" in result.imports

    def test_simple_inheritance_chunk(self, tmp_path):
        """Test simple 1-level inheritance for ChunkConfig."""
        # Create parent chunk
        parent_file = tmp_path / "parent.chunk.yaml"
        parent_data = {
            "version": "2.0",
            "type": "character",
            "template": "parent chunk template",
            "defaults": {"Angle": "Straight", "Main": "30"},
            "chunks": {"Pose": "Standing"}
        }
        parent_file.write_text(yaml.dump(parent_data))

        # Create child chunk
        child_file = tmp_path / "child.chunk.yaml"
        child_data = {
            "version": "2.0",
            "type": "character",
            "implements": "parent.chunk.yaml",
            "template": "child chunk template",
            "chunks": {"Main": "22"}  # Override
        }

        # Setup
        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_chunk(child_data, child_file)

        # Execute
        result = resolver.resolve_implements(child_config)

        # Assert
        assert result.type == "character"
        assert result.template == "child chunk template"
        # Defaults merged
        assert result.defaults["Angle"] == "Straight"  # From parent
        assert result.defaults["Main"] == "30"  # From parent
        # Chunks merged (child overrides)
        assert result.chunks["Pose"] == "Standing"  # From parent
        assert result.chunks["Main"] == "22"  # From child (override)


class TestMultiLevelInheritance:
    """Test multi-level inheritance (grandparent → parent → child)."""

    def test_three_level_inheritance(self, tmp_path):
        """Test 3-level inheritance chain."""
        # Grandparent
        grandparent_file = tmp_path / "grandparent.template.yaml"
        grandparent_data = {
            "version": "2.0",
            "name": "Grandparent",
            "template": "grandparent template",
            "parameters": {"width": 512, "height": 512, "steps": 20}
        }
        grandparent_file.write_text(yaml.dump(grandparent_data))

        # Parent
        parent_file = tmp_path / "parent.template.yaml"
        parent_data = {
            "version": "2.0",
            "name": "Parent",
            "implements": "grandparent.template.yaml",
            "template": "parent template",
            "parameters": {"width": 832, "steps": 30}  # Override width, steps
        }
        parent_file.write_text(yaml.dump(parent_data))

        # Child
        child_file = tmp_path / "child.template.yaml"
        child_data = {
            "version": "2.0",
            "name": "Child",
            "implements": "parent.template.yaml",
            "template": "child template",
            "parameters": {"steps": 40}  # Override steps again
        }

        # Setup
        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_template(child_data, child_file)

        # Execute
        result = resolver.resolve_implements(child_config)

        # Assert - final merged parameters
        assert result.parameters["width"] == 832  # From parent (overrode grandparent)
        assert result.parameters["height"] == 512  # From grandparent (unchanged)
        assert result.parameters["steps"] == 40  # From child (overrode parent)


class TestMergeRules:
    """Test specific merge rules for each config section."""

    def test_parameters_merge(self, tmp_path):
        """Test that parameters are merged (child overrides parent keys)."""
        # Parent
        parent_file = tmp_path / "parent.template.yaml"
        parent_data = {
            "version": "2.0",
            "name": "Parent",
            "template": "template",
            "parameters": {
                "width": 832,
                "height": 1216,
                "steps": 30,
                "cfg_scale": 7
            }
        }
        parent_file.write_text(yaml.dump(parent_data))

        # Child
        child_file = tmp_path / "child.template.yaml"
        child_data = {
            "version": "2.0",
            "name": "Child",
            "implements": "parent.template.yaml",
            "template": "template",
            "parameters": {
                "steps": 40,  # Override
                "sampler": "DPM++ 2M"  # New key
            }
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_template(child_data, child_file)
        result = resolver.resolve_implements(child_config)

        # Assert - all keys present, child overrides
        assert result.parameters["width"] == 832  # Inherited
        assert result.parameters["height"] == 1216  # Inherited
        assert result.parameters["cfg_scale"] == 7  # Inherited
        assert result.parameters["steps"] == 40  # Overridden
        assert result.parameters["sampler"] == "DPM++ 2M"  # New

    def test_imports_merge(self, tmp_path):
        """Test that imports are merged (child overrides parent keys)."""
        parent_file = tmp_path / "parent.template.yaml"
        parent_data = {
            "version": "2.0",
            "name": "Parent",
            "template": "template",
            "imports": {
                "Character": "../chunks/char1.chunk.yaml",
                "Style": "../variations/style.yaml"
            }
        }
        parent_file.write_text(yaml.dump(parent_data))

        child_file = tmp_path / "child.template.yaml"
        child_data = {
            "version": "2.0",
            "name": "Child",
            "implements": "parent.template.yaml",
            "template": "template",
            "imports": {
                "Character": "../chunks/char2.chunk.yaml",  # Override
                "Outfit": "../variations/outfit.yaml"  # New
            }
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_template(child_data, child_file)
        result = resolver.resolve_implements(child_config)

        # Assert
        assert result.imports["Character"] == "../chunks/char2.chunk.yaml"  # Overridden
        assert result.imports["Style"] == "../variations/style.yaml"  # Inherited
        assert result.imports["Outfit"] == "../variations/outfit.yaml"  # New

    def test_chunks_and_defaults_merge(self, tmp_path):
        """Test that chunks and defaults are merged (ChunkConfig)."""
        parent_file = tmp_path / "parent.chunk.yaml"
        parent_data = {
            "version": "2.0",
            "type": "character",
            "template": "template",
            "defaults": {"Angle": "Straight", "Pose": "Standing"},
            "chunks": {"Main": "30"}
        }
        parent_file.write_text(yaml.dump(parent_data))

        child_file = tmp_path / "child.chunk.yaml"
        child_data = {
            "version": "2.0",
            "type": "character",
            "implements": "parent.chunk.yaml",
            "template": "template",
            "defaults": {"Pose": "Sitting"},  # Override
            "chunks": {"Main": "22", "HairCut": "BobCut"}  # Override + New
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_chunk(child_data, child_file)
        result = resolver.resolve_implements(child_config)

        # Assert defaults
        assert result.defaults["Angle"] == "Straight"  # Inherited
        assert result.defaults["Pose"] == "Sitting"  # Overridden
        # Assert chunks
        assert result.chunks["Main"] == "22"  # Overridden
        assert result.chunks["HairCut"] == "BobCut"  # New

    def test_template_replace_with_warning(self, tmp_path, caplog):
        """Test that child template replaces parent and logs warning."""
        parent_file = tmp_path / "parent.chunk.yaml"
        parent_data = {
            "version": "2.0",
            "type": "character",
            "template": "parent template content"
        }
        parent_file.write_text(yaml.dump(parent_data))

        child_file = tmp_path / "child.chunk.yaml"
        child_data = {
            "version": "2.0",
            "type": "character",
            "implements": "parent.chunk.yaml",
            "template": "child template content"
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_chunk(child_data, child_file)

        # Execute with logging capture
        with caplog.at_level(logging.WARNING):
            result = resolver.resolve_implements(child_config)

        # Assert template replaced
        assert result.template == "child template content"
        # Assert warning logged
        assert "Overriding parent template" in caplog.text

    def test_negative_prompt_inheritance(self, tmp_path):
        """Test negative_prompt inheritance (REPLACE if child provides)."""
        parent_file = tmp_path / "parent.template.yaml"
        parent_data = {
            "version": "2.0",
            "name": "Parent",
            "template": "template",
            "negative_prompt": "parent negative"
        }
        parent_file.write_text(yaml.dump(parent_data))

        # Test 1: Child doesn't provide negative_prompt → inherit
        child1_file = tmp_path / "child1.template.yaml"
        child1_data = {
            "version": "2.0",
            "name": "Child1",
            "implements": "parent.template.yaml",
            "template": "template"
            # No negative_prompt
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child1_config = parser.parse_template(child1_data, child1_file)
        result1 = resolver.resolve_implements(child1_config)
        assert result1.negative_prompt == "parent negative"  # Inherited

        # Test 2: Child provides negative_prompt → override
        child2_file = tmp_path / "child2.template.yaml"
        child2_data = {
            "version": "2.0",
            "name": "Child2",
            "implements": "parent.template.yaml",
            "template": "template",
            "negative_prompt": "child negative"
        }

        resolver.clear_cache()  # Clear cache for fresh test
        child2_config = parser.parse_template(child2_data, child2_file)
        result2 = resolver.resolve_implements(child2_config)
        assert result2.negative_prompt == "child negative"  # Overridden


class TestCacheBehavior:
    """Test resolution cache functionality."""

    def test_cache_avoids_redundant_loads(self, tmp_path):
        """Test that cache prevents redundant file loads."""
        parent_file = tmp_path / "parent.template.yaml"
        parent_data = {
            "version": "2.0",
            "name": "Parent",
            "template": "parent template"
        }
        parent_file.write_text(yaml.dump(parent_data))

        child_file = tmp_path / "child.template.yaml"
        child_data = {
            "version": "2.0",
            "name": "Child",
            "implements": "parent.template.yaml",
            "template": "child template"
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_template(child_data, child_file)

        # First resolution
        result1 = resolver.resolve_implements(child_config)
        cache_size_1 = len(resolver.resolution_cache)

        # Second resolution (should use cache)
        result2 = resolver.resolve_implements(child_config)
        cache_size_2 = len(resolver.resolution_cache)

        # Assert
        assert result1.name == "Child"
        assert result2.name == "Child"
        assert cache_size_1 == cache_size_2  # No new cache entries
        # Cache should contain entry for child file
        cache_key = str(child_file.resolve())
        assert cache_key in resolver.resolution_cache

    def test_clear_cache(self, tmp_path):
        """Test cache clearing functionality."""
        parent_file = tmp_path / "parent.template.yaml"
        parent_data = {
            "version": "2.0",
            "name": "Parent",
            "template": "parent template"
        }
        parent_file.write_text(yaml.dump(parent_data))

        child_file = tmp_path / "child.template.yaml"
        child_data = {
            "version": "2.0",
            "name": "Child",
            "implements": "parent.template.yaml",
            "template": "child template"
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_template(child_data, child_file)

        # Resolve to populate cache
        resolver.resolve_implements(child_config)
        assert len(resolver.resolution_cache) > 0

        # Clear cache
        resolver.clear_cache()
        assert len(resolver.resolution_cache) == 0

    def test_invalidate_specific_file(self, tmp_path):
        """Test invalidating a specific file in cache."""
        parent_file = tmp_path / "parent.template.yaml"
        parent_data = {
            "version": "2.0",
            "name": "Parent",
            "template": "parent template"
        }
        parent_file.write_text(yaml.dump(parent_data))

        child_file = tmp_path / "child.template.yaml"
        child_data = {
            "version": "2.0",
            "name": "Child",
            "implements": "parent.template.yaml",
            "template": "child template"
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_template(child_data, child_file)

        # Resolve to populate cache
        resolver.resolve_implements(child_config)
        cache_key = str(child_file.resolve())
        assert cache_key in resolver.resolution_cache

        # Invalidate specific file
        resolver.invalidate(child_file)
        assert cache_key not in resolver.resolution_cache


class TestChunkTypeValidation:
    """Test type validation for chunk inheritance."""

    def test_same_type_allowed(self, tmp_path):
        """Test that chunks with same type can inherit."""
        parent_file = tmp_path / "parent.chunk.yaml"
        parent_data = {
            "version": "2.0",
            "type": "character",
            "template": "parent"
        }
        parent_file.write_text(yaml.dump(parent_data))

        child_file = tmp_path / "child.chunk.yaml"
        child_data = {
            "version": "2.0",
            "type": "character",
            "implements": "parent.chunk.yaml",
            "template": "child"
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_chunk(child_data, child_file)

        # Should not raise
        result = resolver.resolve_implements(child_config)
        assert result.type == "character"

    def test_type_mismatch_raises_error(self, tmp_path):
        """Test that chunks with different types cannot inherit."""
        parent_file = tmp_path / "parent.chunk.yaml"
        parent_data = {
            "version": "2.0",
            "type": "character",
            "template": "parent"
        }
        parent_file.write_text(yaml.dump(parent_data))

        child_file = tmp_path / "child.chunk.yaml"
        child_data = {
            "version": "2.0",
            "type": "scene",  # Different type
            "implements": "parent.chunk.yaml",
            "template": "child"
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_chunk(child_data, child_file)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Type mismatch"):
            resolver.resolve_implements(child_config)

    def test_parent_no_type_logs_warning(self, tmp_path, caplog):
        """Test that parent with no type logs warning and assumes child type."""
        parent_file = tmp_path / "parent.chunk.yaml"
        parent_data = {
            "version": "2.0",
            "type": "",  # Empty type
            "template": "parent"
        }
        parent_file.write_text(yaml.dump(parent_data))

        child_file = tmp_path / "child.chunk.yaml"
        child_data = {
            "version": "2.0",
            "type": "character",
            "implements": "parent.chunk.yaml",
            "template": "child"
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_chunk(child_data, child_file)

        # Execute with logging
        with caplog.at_level(logging.WARNING):
            result = resolver.resolve_implements(child_config)

        # Assert warning logged
        assert "has no type, assuming" in caplog.text
        # Should still succeed
        assert result.type == "character"


class TestErrorHandling:
    """Test error handling in inheritance resolution."""

    def test_missing_parent_file_raises_error(self, tmp_path):
        """Test that missing parent file raises FileNotFoundError."""
        child_file = tmp_path / "child.template.yaml"
        child_data = {
            "version": "2.0",
            "name": "Child",
            "implements": "nonexistent.template.yaml",
            "template": "child"
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_template(child_data, child_file)

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            resolver.resolve_implements(child_config)

    def test_absolute_path_in_implements_raises_error(self, tmp_path):
        """Test that absolute paths in implements: raise ValueError."""
        child_file = tmp_path / "child.template.yaml"
        child_data = {
            "version": "2.0",
            "name": "Child",
            "implements": "/absolute/path/parent.template.yaml",  # Absolute path
            "template": "child"
        }

        loader = YamlLoader()
        parser = ConfigParser()
        resolver = InheritanceResolver(loader, parser)

        child_config = parser.parse_template(child_data, child_file)

        # Should raise ValueError (absolute paths not allowed)
        with pytest.raises(ValueError, match="Invalid implements path"):
            resolver.resolve_implements(child_config)
