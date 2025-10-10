"""
Tests for ConfigValidator - 5 Phase Validation System.

This module tests all validation phases:
1. Structure: Required fields, YAML well-formed
2. Paths: Files exist (implements, imports)
3. Inheritance: Type compatibility
4. Imports: No duplicate keys in merge
5. Templates: Reserved placeholders validation
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from templating.loaders.yaml_loader import YamlLoader
from templating.loaders.parser import ConfigParser
from templating.validators.validator import ConfigValidator
from templating.validators.validation_error import ValidationResult
from templating.models.config_models import (
    TemplateConfig, ChunkConfig, PromptConfig, GenerationConfig
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def loader():
    """Create a YamlLoader instance."""
    return YamlLoader()


@pytest.fixture
def parser():
    """Create a ConfigParser instance."""
    return ConfigParser()


@pytest.fixture
def validator(loader):
    """Create a ConfigValidator instance."""
    return ConfigValidator(loader)


# ============================================================================
# PHASE 1: STRUCTURE VALIDATION TESTS
# ============================================================================

class TestPhase1Structure:
    """Test Phase 1: Structure validation."""

    def test_template_missing_version(self, temp_dir, validator):
        """Test that missing version field is caught."""
        config = TemplateConfig(
            version='',  # Missing
            name='TestTemplate',
            template='test',
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].type == 'structure'
        assert 'version' in result.errors[0].message.lower()

    def test_template_missing_name(self, temp_dir, validator):
        """Test that missing name field is caught."""
        config = TemplateConfig(
            version='2.0',
            name='',  # Missing
            template='test',
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].type == 'structure'
        assert 'name' in result.errors[0].message.lower()

    def test_template_missing_template(self, temp_dir, validator):
        """Test that missing template field is caught."""
        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='',  # Missing
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].type == 'structure'
        assert 'template' in result.errors[0].message.lower()

    def test_chunk_missing_type(self, temp_dir, validator):
        """Test that missing type field in chunk is caught."""
        config = ChunkConfig(
            version='2.0',
            type='',  # Missing
            template='test',
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].type == 'structure'
        assert 'type' in result.errors[0].message.lower()

    def test_chunk_missing_template(self, temp_dir, validator):
        """Test that missing template field in chunk is caught."""
        config = ChunkConfig(
            version='2.0',
            type='character',
            template='',  # Missing
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].type == 'structure'
        assert 'template' in result.errors[0].message.lower()

    def test_prompt_implements_optional(self, temp_dir, validator):
        """Test that implements field is optional in prompts (standalone prompts)."""
        gen_config = GenerationConfig(
            mode='random',
            seed=42,
            seed_mode='fixed',
            max_images=10
        )
        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements=None,  # Optional for standalone prompts
            generation=gen_config,
            template='test',
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        # Should be valid (implements is optional)
        structure_errors = [e for e in result.errors if e.type == 'structure']
        assert len(structure_errors) == 0

    def test_prompt_missing_generation(self, temp_dir, validator):
        """Test that missing generation field in prompt is caught."""
        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='../base.yaml',
            generation=None,  # Missing
            template='test',
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        # Should have structure error (and possibly path error for missing implements file)
        structure_errors = [e for e in result.errors if e.type == 'structure']
        assert len(structure_errors) >= 1
        assert 'generation' in structure_errors[0].message.lower()

    def test_multiple_structure_errors(self, temp_dir, validator):
        """Test that multiple structure errors are all collected."""
        config = TemplateConfig(
            version='',  # Missing
            name='',  # Missing
            template='',  # Missing
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        assert len(result.errors) == 3  # All 3 errors collected
        assert all(e.type == 'structure' for e in result.errors)

    def test_valid_template_structure(self, temp_dir, validator):
        """Test that valid template passes structure validation."""
        config = TemplateConfig(
            version='2.0',
            name='ValidTemplate',
            template='test template',
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        # May have other phase errors, but no structure errors
        structure_errors = [e for e in result.errors if e.type == 'structure']
        assert len(structure_errors) == 0


# ============================================================================
# PHASE 2: PATH VALIDATION TESTS
# ============================================================================

class TestPhase2Paths:
    """Test Phase 2: Path validation."""

    def test_implements_file_not_found(self, temp_dir, validator):
        """Test that non-existent implements file is caught."""
        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            implements='../nonexistent.yaml',
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        path_errors = [e for e in result.errors if e.type == 'path']
        assert len(path_errors) >= 1
        assert any('not found' in e.message.lower() for e in path_errors)

    def test_implements_absolute_path_rejected(self, temp_dir, validator):
        """Test that absolute paths in implements are rejected."""
        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            implements='/absolute/path/parent.yaml',
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        path_errors = [e for e in result.errors if e.type == 'path']
        assert len(path_errors) >= 1
        assert any('absolute' in e.message.lower() for e in path_errors)

    def test_import_file_not_found(self, temp_dir, validator):
        """Test that non-existent import file is caught."""
        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            imports={
                'Outfit': '../variations/outfit.yaml'  # Non-existent
            },
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        path_errors = [e for e in result.errors if e.type == 'path']
        assert len(path_errors) >= 1
        assert any('outfit' in e.message.lower() for e in path_errors)

    def test_multiple_import_files_not_found(self, temp_dir, validator):
        """Test that multiple missing import files are all caught."""
        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            imports={
                'Outfit': '../variations/outfit.yaml',
                'Pose': '../variations/pose.yaml',
                'Angle': '../variations/angle.yaml'
            },
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        path_errors = [e for e in result.errors if e.type == 'path']
        assert len(path_errors) >= 3  # All 3 missing files reported

    def test_import_list_with_missing_files(self, temp_dir, validator):
        """Test validation of multi-source imports with missing files."""
        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            imports={
                'Outfit': [
                    '../variations/outfit1.yaml',  # Missing
                    '../variations/outfit2.yaml',  # Missing
                    '"inline string"'  # Inline (should not be validated)
                ]
            },
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        path_errors = [e for e in result.errors if e.type == 'path']
        # Should have 2 errors (not 3, inline string skipped)
        assert len(path_errors) >= 2

    def test_nested_import_paths(self, temp_dir, validator):
        """Test validation of nested imports (dict structure)."""
        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            imports={
                'chunks': {
                    'positive': '../chunks/positive.yaml',
                    'negative': '../chunks/negative.yaml'
                }
            },
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        assert not result.is_valid
        path_errors = [e for e in result.errors if e.type == 'path']
        assert len(path_errors) >= 2  # Both nested files missing

    def test_valid_paths_with_existing_files(self, temp_dir, validator):
        """Test that validation passes when all files exist."""
        # Create parent file
        parent_file = temp_dir / 'parent.yaml'
        parent_file.write_text('version: "2.0"\nname: Parent\ntemplate: test')

        # Create import file
        import_file = temp_dir / 'outfit.yaml'
        import_file.write_text('Casual: "jeans"\nFormal: "suit"')

        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            implements='parent.yaml',
            imports={'Outfit': 'outfit.yaml'},
            source_file=temp_dir / 'test.yaml'
        )
        result = validator.validate(config)
        # No path errors (may have other errors from other phases)
        path_errors = [e for e in result.errors if e.type == 'path']
        assert len(path_errors) == 0


# ============================================================================
# PHASE 3: INHERITANCE VALIDATION TESTS
# ============================================================================

class TestPhase3Inheritance:
    """Test Phase 3: Inheritance validation."""

    def test_chunk_type_mismatch(self, temp_dir, validator):
        """Test that chunk type mismatch is caught."""
        # Create parent chunk with type 'character'
        parent_file = temp_dir / 'parent.chunk.yaml'
        parent_data = {
            'version': '2.0',
            'type': 'character',
            'template': 'parent template'
        }
        parent_file.write_text(yaml.dump(parent_data))

        # Create child chunk with type 'scene' (mismatch!)
        config = ChunkConfig(
            version='2.0',
            type='scene',  # Different from parent
            template='child template',
            implements='parent.chunk.yaml',
            source_file=temp_dir / 'child.chunk.yaml'
        )

        result = validator.validate(config)
        assert not result.is_valid
        inheritance_errors = [e for e in result.errors if e.type == 'inheritance']
        assert len(inheritance_errors) >= 1
        assert any('mismatch' in e.message.lower() for e in inheritance_errors)

    def test_chunk_parent_without_type_warning(self, temp_dir, validator):
        """Test that parent chunk without type generates warning."""
        # Create parent chunk WITHOUT type field
        parent_file = temp_dir / 'parent.chunk.yaml'
        parent_data = {
            'version': '2.0',
            # No 'type' field
            'template': 'parent template'
        }
        parent_file.write_text(yaml.dump(parent_data))

        # Create child chunk with type
        config = ChunkConfig(
            version='2.0',
            type='character',
            template='child template',
            implements='parent.chunk.yaml',
            source_file=temp_dir / 'child.chunk.yaml'
        )

        result = validator.validate(config)
        # Should have a warning (inheritance error with "Warning:" in message)
        inheritance_errors = [e for e in result.errors if e.type == 'inheritance']
        assert len(inheritance_errors) >= 1
        assert any('warning' in e.message.lower() for e in inheritance_errors)

    def test_chunk_same_type_valid(self, temp_dir, validator):
        """Test that chunk inheriting same type is valid."""
        # Create parent chunk with type 'character'
        parent_file = temp_dir / 'parent.chunk.yaml'
        parent_data = {
            'version': '2.0',
            'type': 'character',
            'template': 'parent template'
        }
        parent_file.write_text(yaml.dump(parent_data))

        # Create child chunk with same type
        config = ChunkConfig(
            version='2.0',
            type='character',  # Same as parent
            template='child template',
            implements='parent.chunk.yaml',
            source_file=temp_dir / 'child.chunk.yaml'
        )

        result = validator.validate(config)
        # No inheritance errors (parent/child have same type)
        inheritance_errors = [e for e in result.errors if e.type == 'inheritance']
        # May have warning about parent type, but no mismatch error
        mismatch_errors = [e for e in inheritance_errors if 'mismatch' in e.message.lower()]
        assert len(mismatch_errors) == 0

    def test_template_inheritance_no_type_check(self, temp_dir, validator):
        """Test that template inheritance is not type-checked."""
        # Templates don't have type field, so no validation
        parent_file = temp_dir / 'parent.template.yaml'
        parent_data = {
            'version': '2.0',
            'name': 'Parent',
            'template': 'parent template'
        }
        parent_file.write_text(yaml.dump(parent_data))

        config = TemplateConfig(
            version='2.0',
            name='Child',
            template='child template',
            implements='parent.template.yaml',
            source_file=temp_dir / 'child.template.yaml'
        )

        result = validator.validate(config)
        # No inheritance errors for templates
        inheritance_errors = [e for e in result.errors if e.type == 'inheritance']
        assert len(inheritance_errors) == 0


# ============================================================================
# PHASE 4: IMPORTS VALIDATION TESTS
# ============================================================================

class TestPhase4Imports:
    """Test Phase 4: Imports validation (duplicate keys)."""

    def test_duplicate_keys_in_multi_source(self, temp_dir, validator):
        """Test that duplicate keys across import files are caught."""
        # Create first file with key 'Casual'
        file1 = temp_dir / 'outfit1.yaml'
        file1.write_text(yaml.dump({'Casual': 'jeans', 'Formal': 'suit'}))

        # Create second file with duplicate key 'Casual'
        file2 = temp_dir / 'outfit2.yaml'
        file2.write_text(yaml.dump({'Casual': 'casual dress', 'Sports': 'sportswear'}))

        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            imports={
                'Outfit': [
                    'outfit1.yaml',
                    'outfit2.yaml'
                ]
            },
            source_file=temp_dir / 'test.yaml'
        )

        result = validator.validate(config)
        assert not result.is_valid
        import_errors = [e for e in result.errors if e.type == 'import']
        assert len(import_errors) >= 1
        assert any('duplicate' in e.message.lower() for e in import_errors)
        assert any('casual' in e.message.lower() for e in import_errors)

    def test_no_duplicate_keys_valid(self, temp_dir, validator):
        """Test that non-conflicting multi-source imports are valid."""
        # Create files with unique keys
        file1 = temp_dir / 'outfit1.yaml'
        file1.write_text(yaml.dump({'Casual': 'jeans', 'Formal': 'suit'}))

        file2 = temp_dir / 'outfit2.yaml'
        file2.write_text(yaml.dump({'Sports': 'sportswear', 'Beach': 'swimsuit'}))

        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            imports={
                'Outfit': [
                    'outfit1.yaml',
                    'outfit2.yaml'
                ]
            },
            source_file=temp_dir / 'test.yaml'
        )

        result = validator.validate(config)
        # No import errors (keys are unique)
        import_errors = [e for e in result.errors if e.type == 'import']
        duplicate_errors = [e for e in import_errors if 'duplicate' in e.message.lower()]
        assert len(duplicate_errors) == 0

    def test_inline_strings_no_conflict(self, temp_dir, validator):
        """Test that inline strings don't cause conflicts (auto-generated keys)."""
        # Create file with key 'Casual'
        file1 = temp_dir / 'outfit1.yaml'
        file1.write_text(yaml.dump({'Casual': 'jeans'}))

        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            imports={
                'Outfit': [
                    'outfit1.yaml',
                    '"casual dress"',  # Inline string (gets auto key)
                    '"another casual"'  # Another inline
                ]
            },
            source_file=temp_dir / 'test.yaml'
        )

        result = validator.validate(config)
        # No import errors (inline strings get auto-generated keys)
        import_errors = [e for e in result.errors if e.type == 'import']
        duplicate_errors = [e for e in import_errors if 'duplicate' in e.message.lower()]
        assert len(duplicate_errors) == 0


# ============================================================================
# PHASE 5: TEMPLATES VALIDATION TESTS
# ============================================================================

class TestPhase5Templates:
    """Test Phase 5: Template validation (reserved placeholders)."""

    def test_chunk_with_reserved_placeholder_prompt(self, temp_dir, validator):
        """Test that {prompt} in chunk template is caught."""
        config = ChunkConfig(
            version='2.0',
            type='character',
            template='1girl, {prompt}, beautiful',  # {prompt} not allowed!
            source_file=temp_dir / 'test.chunk.yaml'
        )

        result = validator.validate(config)
        assert not result.is_valid
        template_errors = [e for e in result.errors if e.type == 'template']
        assert len(template_errors) >= 1
        assert any('prompt' in e.message.lower() for e in template_errors)
        assert any('reserved' in e.message.lower() for e in template_errors)

    def test_chunk_with_reserved_placeholder_negprompt(self, temp_dir, validator):
        """Test that {negprompt} in chunk template is caught."""
        config = ChunkConfig(
            version='2.0',
            type='character',
            template='1girl, beautiful, {negprompt}',  # Not allowed!
            source_file=temp_dir / 'test.chunk.yaml'
        )

        result = validator.validate(config)
        assert not result.is_valid
        template_errors = [e for e in result.errors if e.type == 'template']
        assert len(template_errors) >= 1
        assert any('negprompt' in e.message.lower() for e in template_errors)

    def test_chunk_with_reserved_placeholder_loras(self, temp_dir, validator):
        """Test that {loras} in chunk template is caught."""
        config = ChunkConfig(
            version='2.0',
            type='character',
            template='{loras}, 1girl, beautiful',  # Not allowed!
            source_file=temp_dir / 'test.chunk.yaml'
        )

        result = validator.validate(config)
        assert not result.is_valid
        template_errors = [e for e in result.errors if e.type == 'template']
        assert len(template_errors) >= 1
        assert any('loras' in e.message.lower() for e in template_errors)

    def test_chunk_with_multiple_reserved_placeholders(self, temp_dir, validator):
        """Test that multiple reserved placeholders are all caught."""
        config = ChunkConfig(
            version='2.0',
            type='character',
            template='{loras}, {prompt}, {negprompt}',  # All 3 not allowed!
            source_file=temp_dir / 'test.chunk.yaml'
        )

        result = validator.validate(config)
        assert not result.is_valid
        template_errors = [e for e in result.errors if e.type == 'template']
        # Should have 3 errors (one for each reserved placeholder)
        assert len(template_errors) >= 3

    def test_chunk_with_normal_placeholders_valid(self, temp_dir, validator):
        """Test that normal placeholders in chunks are valid."""
        config = ChunkConfig(
            version='2.0',
            type='character',
            template='1girl, {Angle}, {Pose}, {Outfit}',  # Normal placeholders OK
            source_file=temp_dir / 'test.chunk.yaml'
        )

        result = validator.validate(config)
        # No template errors for normal placeholders
        template_errors = [e for e in result.errors if e.type == 'template']
        assert len(template_errors) == 0

    def test_template_with_reserved_placeholders_valid(self, temp_dir, validator):
        """Test that reserved placeholders in template are valid."""
        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='masterpiece, {prompt}, detailed',  # {prompt} OK in template
            source_file=temp_dir / 'test.template.yaml'
        )

        result = validator.validate(config)
        # No template errors for reserved placeholders in templates
        template_errors = [e for e in result.errors if e.type == 'template']
        assert len(template_errors) == 0

    def test_prompt_with_reserved_placeholders_valid(self, temp_dir, validator):
        """Test that reserved placeholders in prompt are valid."""
        parent_file = temp_dir / 'parent.yaml'
        parent_file.write_text('version: "2.0"\nname: Parent\ntemplate: test')

        gen_config = GenerationConfig(
            mode='random',
            seed=42,
            seed_mode='fixed',
            max_images=10
        )
        config = PromptConfig(
            version='2.0',
            name='TestPrompt',
            implements='parent.yaml',
            generation=gen_config,
            template='{loras}, {prompt}, detailed',  # Reserved OK in prompts
            source_file=temp_dir / 'test.prompt.yaml'
        )

        result = validator.validate(config)
        # No template errors
        template_errors = [e for e in result.errors if e.type == 'template']
        assert len(template_errors) == 0


# ============================================================================
# INTEGRATION TESTS: MULTIPLE PHASES
# ============================================================================

class TestValidatorIntegration:
    """Test validator with multiple errors across phases."""

    def test_multiple_errors_collected(self, temp_dir, validator):
        """Test that errors from all phases are collected."""
        config = TemplateConfig(
            version='',  # Structure error
            name='',  # Structure error
            template='{prompt}',  # OK
            implements='../missing.yaml',  # Path error
            imports={
                'Outfit': '../missing_outfit.yaml'  # Path error
            },
            source_file=temp_dir / 'test.yaml'
        )

        result = validator.validate(config)
        assert not result.is_valid
        # Should have multiple errors from different phases
        assert len(result.errors) >= 4

        # Check we have errors from multiple types
        error_types = {e.type for e in result.errors}
        assert 'structure' in error_types
        assert 'path' in error_types

    def test_validation_result_json_export(self, temp_dir, validator):
        """Test that validation result can be exported to JSON."""
        config = TemplateConfig(
            version='',
            name='TestTemplate',
            template='test',
            source_file=temp_dir / 'test.yaml'
        )

        result = validator.validate(config)
        json_data = result.to_json()

        # Check JSON structure
        assert 'errors' in json_data
        assert 'count' in json_data
        assert isinstance(json_data['errors'], list)
        assert json_data['count'] == len(json_data['errors'])

        # Check error structure
        if json_data['errors']:
            error = json_data['errors'][0]
            assert 'type' in error
            assert 'message' in error
            assert 'file' in error

    def test_valid_config_passes_all_phases(self, temp_dir, validator):
        """Test that a completely valid config passes all phases."""
        config = TemplateConfig(
            version='2.0',
            name='ValidTemplate',
            template='masterpiece, {prompt}, detailed',
            source_file=temp_dir / 'test.yaml'
        )

        result = validator.validate(config)
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.error_count == 0


# ============================================================================
# ERROR DETAILS TESTS
# ============================================================================

class TestErrorDetails:
    """Test that errors include proper details for debugging."""

    def test_path_error_includes_file_info(self, temp_dir, validator):
        """Test that path errors include file information."""
        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            implements='../missing.yaml',
            source_file=temp_dir / 'test.yaml'
        )

        result = validator.validate(config)
        path_errors = [e for e in result.errors if e.type == 'path']
        assert len(path_errors) >= 1
        error = path_errors[0]
        assert error.file is not None
        assert error.name == 'implements'

    def test_inheritance_error_includes_details(self, temp_dir, validator):
        """Test that inheritance errors include type details."""
        parent_file = temp_dir / 'parent.chunk.yaml'
        parent_data = {
            'version': '2.0',
            'type': 'character',
            'template': 'parent'
        }
        parent_file.write_text(yaml.dump(parent_data))

        config = ChunkConfig(
            version='2.0',
            type='scene',
            template='child',
            implements='parent.chunk.yaml',
            source_file=temp_dir / 'child.chunk.yaml'
        )

        result = validator.validate(config)
        inheritance_errors = [e for e in result.errors if e.type == 'inheritance']
        assert len(inheritance_errors) >= 1
        error = inheritance_errors[0]
        assert error.details is not None
        assert 'child_type' in error.details
        assert 'parent_type' in error.details

    def test_import_error_includes_conflict_details(self, temp_dir, validator):
        """Test that import conflict errors include key details."""
        file1 = temp_dir / 'outfit1.yaml'
        file1.write_text(yaml.dump({'Casual': 'jeans'}))

        file2 = temp_dir / 'outfit2.yaml'
        file2.write_text(yaml.dump({'Casual': 'dress'}))

        config = TemplateConfig(
            version='2.0',
            name='TestTemplate',
            template='test',
            imports={
                'Outfit': ['outfit1.yaml', 'outfit2.yaml']
            },
            source_file=temp_dir / 'test.yaml'
        )

        result = validator.validate(config)
        import_errors = [e for e in result.errors if e.type == 'import']
        assert len(import_errors) >= 1
        error = import_errors[0]
        assert error.details is not None
        assert 'key' in error.details
        assert error.details['key'] == 'Casual'
