"""
Unit tests for Multi-Part Variations feature (Issue #56 - Phase 1 MVP).

Tests cover:
1. Parsing multi-part variations (parser.py)
2. Metadata tracking (import_resolver.py)
3. Placeholder resolution with sub-placeholders (template_resolver.py)
4. Syntax validation
5. Auto-resolve behavior ({Var} → {Var:main})
"""

import pytest
from pathlib import Path
from sd_generator_cli.templating.loaders.parser import ConfigParser
from sd_generator_cli.templating.resolvers.import_resolver import ImportResolver
from sd_generator_cli.templating.resolvers.template_resolver import TemplateResolver


class TestMultiPartVariationsParsing:
    """Tests for parsing multi-part variations in parser.py."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ConfigParser()

    def test_parse_simple_variations_backward_compat(self):
        """Test that simple variations still parse correctly (backward compatibility)."""
        data = {
            "short_bob": "short bob cut, brown hair",
            "long_waves": "long wavy hair, blonde"
        }

        result = self.parser.parse_variations(data)

        assert result == {
            "short_bob": "short bob cut, brown hair",
            "long_waves": "long wavy hair, blonde"
        }
        # All values should be strings
        assert all(isinstance(v, str) for v in result.values())

    def test_parse_multipart_variations(self):
        """Test parsing multi-part variations (dict values)."""
        data = {
            "short_bob": {
                "main": "short bob cut, brown hair",
                "lora": "<lora:hair_short_bob:0.7>"
            },
            "long_waves": {
                "main": "long wavy hair, blonde",
                "lora": "<lora:hair_long_waves:0.8>"
            }
        }

        result = self.parser.parse_variations(data)

        assert "short_bob" in result
        assert "long_waves" in result

        # Values should be dicts
        assert isinstance(result["short_bob"], dict)
        assert isinstance(result["long_waves"], dict)

        # Check structure
        assert result["short_bob"]["main"] == "short bob cut, brown hair"
        assert result["short_bob"]["lora"] == "<lora:hair_short_bob:0.7>"
        assert result["long_waves"]["main"] == "long wavy hair, blonde"
        assert result["long_waves"]["lora"] == "<lora:hair_long_waves:0.8>"

    def test_parse_mixed_simple_and_multipart(self):
        """Test parsing mixed simple and multi-part variations."""
        data = {
            "simple": "simple string value",
            "multipart": {
                "main": "main text",
                "lora": "lora tag"
            },
            "another_simple": "another string"
        }

        result = self.parser.parse_variations(data)

        # Simple variations
        assert result["simple"] == "simple string value"
        assert result["another_simple"] == "another string"
        assert isinstance(result["simple"], str)
        assert isinstance(result["another_simple"], str)

        # Multi-part variation
        assert isinstance(result["multipart"], dict)
        assert result["multipart"]["main"] == "main text"
        assert result["multipart"]["lora"] == "lora tag"

    def test_parse_multipart_with_structured_format(self):
        """Test multi-part with structured format (has 'variations' key)."""
        data = {
            "type": "variations",
            "version": "1.0",
            "variations": {
                "hair1": {
                    "main": "short hair",
                    "lora": "<lora:short:0.7>"
                },
                "hair2": {
                    "main": "long hair",
                    "lora": "<lora:long:0.8>"
                }
            }
        }

        result = self.parser.parse_variations(data)

        assert "hair1" in result
        assert "hair2" in result
        assert isinstance(result["hair1"], dict)
        assert result["hair1"]["main"] == "short hair"

    def test_parse_multipart_validation_non_string_part_value(self):
        """Test that non-string values in parts raise ValueError."""
        data = {
            "hair1": {
                "main": "short hair",
                "lora": 123  # Invalid: not a string
            }
        }

        with pytest.raises(ValueError, match="non-string value for part 'lora'"):
            self.parser.parse_variations(data)

    def test_parse_multipart_validation_invalid_value_type(self):
        """Test that invalid value types (not string or dict) raise ValueError."""
        data = {
            "hair1": ["list", "of", "values"]  # Invalid: list
        }

        with pytest.raises(ValueError, match="invalid value type"):
            self.parser.parse_variations(data)

    def test_parse_multipart_validation_nested_dict(self):
        """Test that nested dicts (dict within dict) raise ValueError."""
        data = {
            "hair1": {
                "main": "short hair",
                "nested": {  # Invalid: dict within dict
                    "key": "value"
                }
            }
        }

        with pytest.raises(ValueError, match="non-string value"):
            self.parser.parse_variations(data)

    def test_parse_multipart_empty_parts(self):
        """Test multi-part variation with empty parts dict."""
        data = {
            "empty": {}
        }

        result = self.parser.parse_variations(data)

        assert "empty" in result
        assert result["empty"] == {}
        assert isinstance(result["empty"], dict)


class TestMultiPartVariationsMetadata:
    """Tests for metadata tracking in import_resolver.py."""

    def setup_method(self):
        """Set up test fixtures."""
        from sd_generator_cli.templating.loaders.yaml_loader import YamlLoader
        from sd_generator_cli.templating.loaders.parser import ConfigParser

        self.loader = YamlLoader()
        self.parser = ConfigParser()
        self.resolver = ImportResolver(self.loader, self.parser)

    def test_analyze_simple_variations(self):
        """Test metadata for simple variations."""
        variations = {
            "key1": "value1",
            "key2": "value2"
        }

        metadata = self.resolver._analyze_variations(variations)

        assert metadata["is_multipart"] is False
        assert metadata["parts"] == []

    def test_analyze_multipart_variations(self):
        """Test metadata for multi-part variations."""
        variations = {
            "hair1": {
                "main": "short hair",
                "lora": "<lora:short:0.7>"
            },
            "hair2": {
                "main": "long hair",
                "lora": "<lora:long:0.8>"
            }
        }

        metadata = self.resolver._analyze_variations(variations)

        assert metadata["is_multipart"] is True
        assert "main" in metadata["parts"]
        assert "lora" in metadata["parts"]
        assert sorted(metadata["parts"]) == ["lora", "main"]  # Sorted

    def test_analyze_mixed_variations(self):
        """Test metadata for mixed simple and multi-part."""
        variations = {
            "simple": "string value",
            "multipart": {
                "main": "text",
                "lora": "tag"
            }
        }

        metadata = self.resolver._analyze_variations(variations)

        assert metadata["is_multipart"] is True  # Has at least one multi-part
        assert "main" in metadata["parts"]
        assert "lora" in metadata["parts"]

    def test_analyze_multipart_multiple_parts(self):
        """Test metadata extraction with multiple different parts."""
        variations = {
            "var1": {
                "main": "text1",
                "lora": "tag1",
                "negative": "avoid1"
            },
            "var2": {
                "main": "text2",
                "lora": "tag2",
                "custom": "custom2"
            }
        }

        metadata = self.resolver._analyze_variations(variations)

        assert metadata["is_multipart"] is True
        # All unique parts across all variations
        expected_parts = ["custom", "lora", "main", "negative"]
        assert sorted(metadata["parts"]) == expected_parts

    def test_analyze_non_dict_value(self):
        """Test metadata for non-dict values (like strings, lists)."""
        # Test string
        metadata = self.resolver._analyze_variations("just a string")
        assert metadata["is_multipart"] is False
        assert metadata["parts"] == []

        # Test list
        metadata = self.resolver._analyze_variations(["item1", "item2"])
        assert metadata["is_multipart"] is False
        assert metadata["parts"] == []

    def test_analyze_chunk_config(self):
        """Test that chunk config dicts are not treated as multi-part."""
        chunk_config = {
            "template": "some template",
            "imports": {},
            "defaults": {}
        }

        metadata = self.resolver._analyze_variations(chunk_config)

        assert metadata["is_multipart"] is False
        assert metadata["parts"] == []


class TestTemplateResolverSyntaxValidation:
    """Tests for placeholder syntax validation in template_resolver.py."""

    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = TemplateResolver()

    def test_reject_selector_with_subplaceholder(self):
        """Test that {Var[selector]:part} raises ValueError."""
        template = "{Hair[random:3]:lora}"
        context = {
            "imports": {
                "Hair": {
                    "hair1": {"main": "short", "lora": "tag1"},
                    "hair2": {"main": "long", "lora": "tag2"}
                }
            },
            "chunks": {},
            "defaults": {}
        }

        with pytest.raises(ValueError, match="Selectors cannot be combined with sub-placeholders"):
            self.resolver._resolve_placeholders(template, context)

    def test_reject_selector_with_subplaceholder_complex(self):
        """Test rejection with complex selectors."""
        templates = [
            "{Hair[limit:5]:lora}",
            "{Hair[#1,3,5]:main}",
            "{Hair[BobCut,LongHair]:lora}",
            "{Hair[$8]:main}"
        ]

        context = {
            "imports": {},
            "chunks": {},
            "defaults": {}
        }

        for template in templates:
            with pytest.raises(ValueError, match="Selectors cannot be combined"):
                self.resolver._resolve_placeholders(template, context)

    def test_allow_selector_without_subplaceholder(self):
        """Test that {Var[selector]} works correctly (no error)."""
        template = "{Hair[random:2]}"
        context = {
            "imports": {
                "Hair": {
                    "hair1": {"main": "short", "lora": "tag1"},
                    "hair2": {"main": "long", "lora": "tag2"}
                }
            },
            "chunks": {},
            "defaults": {}
        }

        # Should not raise - will use default part ("main")
        result = self.resolver._resolve_placeholders(template, context)
        # Result should be one of the main values
        assert result in ["short", "long"]

    def test_allow_subplaceholder_without_selector(self):
        """Test that {Var:part} works correctly (no error)."""
        template = "{Hair:lora}"
        context = {
            "chunks": {
                "Hair": {"main": "short hair", "lora": "<lora:short:0.7>"}
            },
            "imports": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        assert result == "<lora:short:0.7>"


class TestTemplateResolverSubPlaceholders:
    """Tests for sub-placeholder resolution in template_resolver.py."""

    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = TemplateResolver()

    def test_resolve_subplaceholder_from_chunks(self):
        """Test resolving {Var:part} when value is in chunks."""
        template = "Hair: {Hair:main}, LoRA: {Hair:lora}"
        context = {
            "chunks": {
                "Hair": {
                    "main": "short bob cut",
                    "lora": "<lora:short_bob:0.7>"
                }
            },
            "imports": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        assert result == "Hair: short bob cut, LoRA: <lora:short_bob:0.7>"

    def test_resolve_subplaceholder_from_imports(self):
        """Test resolving {Var:part} when value is in imports."""
        template = "{Hair:lora}"
        context = {
            "imports": {
                "Hair": {
                    "hair1": {"main": "short", "lora": "tag1"}
                }
            },
            "chunks": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        assert result == "tag1"

    def test_resolve_subplaceholder_missing_part(self):
        """Test resolving {Var:part} when part doesn't exist (returns empty)."""
        template = "{Hair:missing_part}"
        context = {
            "chunks": {
                "Hair": {"main": "short", "lora": "tag"}
            },
            "imports": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        assert result == ""

    def test_resolve_subplaceholder_error_simple_variation(self):
        """Test that {Var:part} raises error for simple (non-multi-part) variation."""
        template = "{Hair:lora}"
        context = {
            "chunks": {
                "Hair": "simple string value"  # Simple, not multi-part
            },
            "imports": {},
            "defaults": {}
        }

        with pytest.raises(ValueError, match="not a multi-part variation"):
            self.resolver._resolve_placeholders(template, context)

    def test_resolve_multiple_subplaceholders(self):
        """Test template with multiple sub-placeholders."""
        template = "{Hair:main}, {Outfit:main}, {Hair:lora}, {Outfit:lora}"
        context = {
            "chunks": {
                "Hair": {"main": "short", "lora": "<lora:hair:0.7>"},
                "Outfit": {"main": "dress", "lora": "<lora:dress:0.8>"}
            },
            "imports": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        assert result == "short, dress, <lora:hair:0.7>, <lora:dress:0.8>"


class TestTemplateResolverAutoResolve:
    """Tests for auto-resolve behavior ({Var} → {Var:main})."""

    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = TemplateResolver()

    def test_autoresolve_uses_main_part(self):
        """Test that {Var} auto-resolves to 'main' part if it exists."""
        template = "{Hair}"
        context = {
            "chunks": {
                "Hair": {
                    "main": "short bob cut",
                    "lora": "<lora:short:0.7>",
                    "negative": "long hair"
                }
            },
            "imports": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        assert result == "short bob cut"

    def test_autoresolve_uses_first_part_if_no_main(self):
        """Test that {Var} uses first alphabetically sorted part if no 'main'."""
        template = "{Hair}"
        context = {
            "chunks": {
                "Hair": {
                    "lora": "<lora:short:0.7>",
                    "negative": "long hair",
                    "aaa_first": "this should be first"
                }
            },
            "imports": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        # Should use "aaa_first" (first alphabetically)
        assert result == "this should be first"

    def test_autoresolve_from_imports(self):
        """Test auto-resolve when value comes from imports."""
        template = "{Hair}"
        context = {
            "imports": {
                "Hair": {
                    "hair1": {"main": "short", "lora": "tag1"}
                }
            },
            "chunks": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        assert result == "short"

    def test_autoresolve_simple_variation_unchanged(self):
        """Test that simple variations (non-multi-part) work unchanged."""
        template = "{Hair}"
        context = {
            "chunks": {
                "Hair": "simple string value"
            },
            "imports": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        assert result == "simple string value"

    def test_get_default_part_with_main(self):
        """Test _get_default_part() with 'main' present."""
        multipart = {
            "main": "main text",
            "lora": "lora tag",
            "negative": "negative prompt"
        }

        result = self.resolver._get_default_part(multipart)
        assert result == "main text"

    def test_get_default_part_without_main(self):
        """Test _get_default_part() without 'main' (uses first alphabetically)."""
        multipart = {
            "lora": "lora tag",
            "negative": "negative prompt",
            "custom": "custom value"
        }

        result = self.resolver._get_default_part(multipart)
        # Should use "custom" (first alphabetically)
        assert result == "custom value"

    def test_get_default_part_empty_dict(self):
        """Test _get_default_part() with empty dict."""
        result = self.resolver._get_default_part({})
        assert result == ""


class TestTemplateResolverEdgeCases:
    """Edge cases and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = TemplateResolver()

    def test_subplaceholder_with_missing_placeholder(self):
        """Test {MissingVar:part} when var doesn't exist."""
        template = "{MissingVar:lora}"
        context = {
            "chunks": {},
            "imports": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        # Missing var resolves to empty string
        assert result == ""

    def test_mixed_simple_and_multipart_placeholders(self):
        """Test template with both simple and multi-part placeholders."""
        template = "{Simple}, {MultiPart:main}, {MultiPart:lora}"
        context = {
            "chunks": {
                "Simple": "simple value",
                "MultiPart": {"main": "main text", "lora": "lora tag"}
            },
            "imports": {},
            "defaults": {}
        }

        result = self.resolver._resolve_placeholders(template, context)
        assert result == "simple value, main text, lora tag"

    def test_placeholder_pattern_matches_subplaceholders(self):
        """Test that PLACEHOLDER_PATTERN correctly captures sub-placeholders."""
        import re

        pattern = self.resolver.PLACEHOLDER_PATTERN

        # Test {Name}
        match = pattern.match("{Hair}")
        assert match.group(1) == "Hair"
        assert match.group(2) is None  # No selector
        assert match.group(3) is None  # No part

        # Test {Name[selector]}
        match = pattern.match("{Hair[random:3]}")
        assert match.group(1) == "Hair"
        assert match.group(2) == "random:3"  # Selector
        assert match.group(3) is None  # No part

        # Test {Name:part}
        match = pattern.match("{Hair:lora}")
        assert match.group(1) == "Hair"
        assert match.group(2) is None  # No selector
        assert match.group(3) == "lora"  # Part

        # Test {Name[selector]:part} (invalid, but pattern should still match)
        match = pattern.match("{Hair[random:3]:lora}")
        assert match.group(1) == "Hair"
        assert match.group(2) == "random:3"  # Selector
        assert match.group(3) == "lora"  # Part
