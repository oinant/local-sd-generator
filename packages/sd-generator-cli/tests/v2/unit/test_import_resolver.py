"""
Tests for ImportResolver - Template System V2.0 Phase 4.

Tests cover:
- Single file imports
- Inline string imports with MD5 keys
- Multi-source merging
- Conflict detection
- Nested imports
"""

import pytest
from pathlib import Path
from sd_generator_cli.templating.resolvers.import_resolver import ImportResolver
from sd_generator_cli.templating.loaders.yaml_loader import YamlLoader
from sd_generator_cli.templating.loaders.parser import ConfigParser
from sd_generator_cli.templating.models.config_models import PromptConfig, GenerationConfig
from sd_generator_cli.templating.utils.hash_utils import md5_short


@pytest.fixture
def temp_files(tmp_path):
    """Create temporary variation files for testing."""
    # Create variation files
    outfit_urban = tmp_path / "outfit_urban.yaml"
    outfit_urban.write_text("""
Urban1: "jeans and t-shirt"
Urban2: "casual sneakers"
Urban3: "baseball cap"
""")

    outfit_chic = tmp_path / "outfit_chic.yaml"
    outfit_chic.write_text("""
Chic1: "elegant dress"
Chic2: "designer heels"
Chic3: "pearl necklace"
""")

    # File with duplicate key (for conflict tests)
    outfit_conflict = tmp_path / "outfit_conflict.yaml"
    outfit_conflict.write_text("""
Urban1: "different urban style"
Casual: "business casual"
""")

    # Simple variations
    angles = tmp_path / "angles.yaml"
    angles.write_text("""
Straight: "straight angle, eye level"
Above: "from above, top down"
Below: "from below, worm's eye view"
""")

    # Nested chunks
    chunks_positive = tmp_path / "positive.yaml"
    chunks_positive.write_text("""
Quality: "masterpiece, best quality"
Detail: "detailed, highly detailed"
""")

    chunks_negative = tmp_path / "negative.yaml"
    chunks_negative.write_text("""
BadAnatomy: "bad anatomy, deformed"
LowQuality: "low quality, blurry"
""")

    return {
        'base_path': tmp_path,
        'outfit_urban': outfit_urban,
        'outfit_chic': outfit_chic,
        'outfit_conflict': outfit_conflict,
        'angles': angles,
        'chunks_positive': chunks_positive,
        'chunks_negative': chunks_negative,
    }


@pytest.fixture
def resolver(temp_files):
    """Create ImportResolver instance with loader and parser."""
    loader = YamlLoader()
    parser = ConfigParser()
    return ImportResolver(loader, parser)


class TestSingleFileImport:
    """Test single file import resolution."""

    def test_load_simple_variation_file(self, resolver, temp_files):
        """Test loading a simple variation file."""
        base_path = temp_files['base_path']
        variations = resolver._load_variation_file('angles.yaml', base_path)

        assert len(variations) == 3
        assert variations['Straight'] == "straight angle, eye level"
        assert variations['Above'] == "from above, top down"
        assert variations['Below'] == "from below, worm's eye view"

    def test_resolve_single_file_import(self, resolver, temp_files):
        """Test resolving a config with single file import."""
        base_path = temp_files['base_path']

        # Create mock config
        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'Angle': 'angles.yaml'
            }
        )

        resolved = resolver.resolve_imports(config, base_path)

        assert 'Angle' in resolved
        assert len(resolved['Angle']) == 3
        assert resolved['Angle']['Straight'] == "straight angle, eye level"

    def test_file_not_found_error(self, resolver, temp_files):
        """Test error when variation file not found."""
        base_path = temp_files['base_path']

        with pytest.raises(FileNotFoundError):
            resolver._load_variation_file('nonexistent.yaml', base_path)


class TestInlineStringImport:
    """Test inline string imports with MD5 keys."""

    def test_is_inline_string_detection(self, resolver):
        """Test detection of inline strings vs file paths."""
        assert resolver._is_inline_string('"luxury room"') is True
        assert resolver._is_inline_string("'jungle scene'") is True
        assert resolver._is_inline_string('no quotes but no yaml') is True
        assert resolver._is_inline_string('../variations/outfit.yaml') is False
        assert resolver._is_inline_string('outfit.yaml') is False

    def test_inline_string_with_md5_key(self, resolver, temp_files):
        """Test inline string gets MD5 key."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'Place': [
                    'luxury living room',
                    'tropical jungle'
                ]
            }
        )

        resolved = resolver.resolve_imports(config, base_path)

        assert 'Place' in resolved
        assert len(resolved['Place']) == 2

        # Check MD5 keys generated
        key1 = md5_short('luxury living room')
        key2 = md5_short('tropical jungle')

        assert key1 in resolved['Place']
        assert key2 in resolved['Place']
        assert resolved['Place'][key1] == 'luxury living room'
        assert resolved['Place'][key2] == 'tropical jungle'

    def test_inline_string_with_quotes_stripped(self, resolver, temp_files):
        """Test inline strings with quotes get stripped."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'Place': ['"luxury room"', "'jungle scene'"]
            }
        )

        resolved = resolver.resolve_imports(config, base_path)

        # Values should be stripped of quotes
        key1 = md5_short('"luxury room"')
        key2 = md5_short("'jungle scene'")

        assert resolved['Place'][key1] == 'luxury room'
        assert resolved['Place'][key2] == 'jungle scene'


class TestMultiSourceMerge:
    """Test multi-source merging (files + inline)."""

    def test_merge_two_files(self, resolver, temp_files):
        """Test merging two variation files."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'Outfit': [
                    'outfit_urban.yaml',
                    'outfit_chic.yaml'
                ]
            }
        )

        resolved = resolver.resolve_imports(config, base_path)

        assert 'Outfit' in resolved
        # 3 urban + 3 chic = 6 total
        assert len(resolved['Outfit']) == 6

        # Urban items
        assert resolved['Outfit']['Urban1'] == "jeans and t-shirt"
        assert resolved['Outfit']['Urban2'] == "casual sneakers"
        assert resolved['Outfit']['Urban3'] == "baseball cap"

        # Chic items
        assert resolved['Outfit']['Chic1'] == "elegant dress"
        assert resolved['Outfit']['Chic2'] == "designer heels"
        assert resolved['Outfit']['Chic3'] == "pearl necklace"

    def test_merge_files_and_inline(self, resolver, temp_files):
        """Test merging files with inline strings."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'Outfit': [
                    'outfit_urban.yaml',
                    'red dress, elegant',
                    'blue jeans, casual'
                ]
            }
        )

        resolved = resolver.resolve_imports(config, base_path)

        assert 'Outfit' in resolved
        # 3 from file + 2 inline = 5 total
        assert len(resolved['Outfit']) == 5

        # File items
        assert resolved['Outfit']['Urban1'] == "jeans and t-shirt"

        # Inline items (with MD5 keys)
        key1 = md5_short('red dress, elegant')
        key2 = md5_short('blue jeans, casual')
        assert resolved['Outfit'][key1] == 'red dress, elegant'
        assert resolved['Outfit'][key2] == 'blue jeans, casual'

    def test_order_preserved_in_merge(self, resolver, temp_files):
        """Test that merge preserves order of sources."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'Outfit': [
                    'outfit_urban.yaml',
                    'outfit_chic.yaml'
                ]
            }
        )

        resolved = resolver.resolve_imports(config, base_path)

        # Keys should appear in order: Urban1, Urban2, Urban3, Chic1, Chic2, Chic3
        keys = list(resolved['Outfit'].keys())
        assert keys[0] == 'Urban1'
        assert keys[1] == 'Urban2'
        assert keys[2] == 'Urban3'
        assert keys[3] == 'Chic1'
        assert keys[4] == 'Chic2'
        assert keys[5] == 'Chic3'


class TestConflictDetection:
    """Test duplicate key detection in multi-source merges."""

    def test_duplicate_key_raises_error(self, resolver, temp_files):
        """Test error when duplicate keys found between files."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'Outfit': [
                    'outfit_urban.yaml',     # Has Urban1
                    'outfit_conflict.yaml'   # Also has Urban1
                ]
            }
        )

        with pytest.raises(ValueError) as exc_info:
            resolver.resolve_imports(config, base_path)

        error_msg = str(exc_info.value)
        assert "Duplicate key 'Urban1'" in error_msg
        assert "Outfit" in error_msg
        assert "outfit_urban.yaml" in error_msg
        assert "outfit_conflict.yaml" in error_msg

    def test_inline_no_conflict_with_file_keys(self, resolver, temp_files):
        """Test inline strings don't conflict with file keys (different keys)."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'Outfit': [
                    'outfit_urban.yaml',  # Has Urban1, Urban2, Urban3
                    'Urban1: different'   # Inline string (gets MD5 key, not "Urban1")
                ]
            }
        )

        # Should not raise - inline gets MD5 key
        resolved = resolver.resolve_imports(config, base_path)

        # File key
        assert resolved['Outfit']['Urban1'] == "jeans and t-shirt"

        # Inline key (MD5)
        inline_key = md5_short('Urban1: different')
        assert resolved['Outfit'][inline_key] == 'Urban1: different'


class TestNestedImports:
    """Test nested import structures (e.g., chunks: {positive: ..., negative: ...})."""

    def test_nested_dict_imports(self, resolver, temp_files):
        """Test importing nested structures."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'chunks': {
                    'positive': 'positive.yaml',
                    'negative': 'negative.yaml'
                }
            }
        )

        resolved = resolver.resolve_imports(config, base_path)

        assert 'chunks' in resolved
        assert 'positive' in resolved['chunks']
        assert 'negative' in resolved['chunks']

        # Check positive variations
        assert resolved['chunks']['positive']['Quality'] == "masterpiece, best quality"
        assert resolved['chunks']['positive']['Detail'] == "detailed, highly detailed"

        # Check negative variations
        assert resolved['chunks']['negative']['BadAnatomy'] == "bad anatomy, deformed"
        assert resolved['chunks']['negative']['LowQuality'] == "low quality, blurry"

    def test_nested_with_multi_source(self, resolver, temp_files):
        """Test nested imports with multi-source in nested context."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'chunks': {
                    'positive': [
                        'positive.yaml',
                        'ultra detailed'
                    ]
                }
            }
        )

        resolved = resolver.resolve_imports(config, base_path)

        assert 'chunks' in resolved
        assert 'positive' in resolved['chunks']

        # File items
        assert resolved['chunks']['positive']['Quality'] == "masterpiece, best quality"

        # Inline item
        inline_key = md5_short('ultra detailed')
        assert resolved['chunks']['positive'][inline_key] == 'ultra detailed'


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_imports(self, resolver, temp_files):
        """Test config with no imports."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={}
        )

        resolved = resolver.resolve_imports(config, base_path)
        assert resolved == {}

    def test_empty_multi_source_list(self, resolver, temp_files):
        """Test empty list in multi-source."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'Outfit': []
            }
        )

        resolved = resolver.resolve_imports(config, base_path)
        assert resolved['Outfit'] == {}

    def test_single_inline_string_in_list(self, resolver, temp_files):
        """Test list with only one inline string."""
        base_path = temp_files['base_path']

        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.template.yaml',
            generation=GenerationConfig(
                mode='random',
                seed=42,
                seed_mode='fixed',
                max_images=10
            ),
            template='test',
            source_file=base_path / 'prompt.yaml',
            imports={
                'Place': ['luxury room']
            }
        )

        resolved = resolver.resolve_imports(config, base_path)

        key = md5_short('luxury room')
        assert resolved['Place'][key] == 'luxury room'
        assert len(resolved['Place']) == 1
