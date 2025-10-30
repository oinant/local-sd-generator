#!/usr/bin/env python3
"""
Manual testing script for Pydantic schema validation.

Usage:
    python3 test_schemas_manual.py template <yaml_file>
    python3 test_schemas_manual.py prompt <yaml_file>
    python3 test_schemas_manual.py chunk <yaml_file>
    python3 test_schemas_manual.py variations <yaml_file>
    python3 test_schemas_manual.py theme <yaml_file>
"""

import sys
import yaml
from pathlib import Path
from pydantic import ValidationError

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

from sd_generator_cli.templating.schemas import (
    TemplateFileSchema,
    PromptFileSchema,
    ChunkFileSchema,
    VariationsFileSchema,
    ThemeFileSchema,
)


def test_template(file_path: Path):
    """Test TemplateFileSchema validation."""
    print(f"\n{'='*60}")
    print(f"Testing TEMPLATE schema on: {file_path}")
    print(f"{'='*60}\n")

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    print("📄 Raw YAML data:")
    print(yaml.dump(data, default_flow_style=False))

    try:
        validated = TemplateFileSchema(**data)
        print("\n✅ VALIDATION SUCCESS!")
        print(f"\nValidated object:")
        print(f"  - type: {validated.type}")
        print(f"  - name: {validated.name}")
        print(f"  - version: {validated.version}")
        print(f"  - template: {validated.template[:50]}..." if len(validated.template) > 50 else f"  - template: {validated.template}")
        print(f"  - has implements: {validated.implements is not None}")
        print(f"  - imports count: {len(validated.imports)}")
    except ValidationError as e:
        print("\n❌ VALIDATION FAILED!")
        print(f"\nErrors ({len(e.errors())} total):")
        for i, error in enumerate(e.errors(), 1):
            print(f"\n  Error {i}:")
            print(f"    Location: {' -> '.join(str(x) for x in error['loc'])}")
            print(f"    Message: {error['msg']}")
            print(f"    Type: {error['type']}")
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {type(e).__name__}")
        print(f"   {str(e)}")


def test_prompt(file_path: Path):
    """Test PromptFileSchema validation."""
    print(f"\n{'='*60}")
    print(f"Testing PROMPT schema on: {file_path}")
    print(f"{'='*60}\n")

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    print("📄 Raw YAML data:")
    print(yaml.dump(data, default_flow_style=False))

    try:
        validated = PromptFileSchema(**data)
        print("\n✅ VALIDATION SUCCESS!")
        print(f"\nValidated object:")
        print(f"  - type: {validated.type}")
        print(f"  - name: {validated.name}")
        print(f"  - version: {validated.version}")
        print(f"  - prompt: {validated.prompt[:50]}..." if len(validated.prompt) > 50 else f"  - prompt: {validated.prompt}")
        print(f"  - has implements: {validated.implements is not None}")
        print(f"  - generation.mode: {validated.generation.mode}")
        print(f"  - generation.seed_mode: {validated.generation.seed_mode}")
        print(f"  - generation.max_images: {validated.generation.max_images}")
        print(f"  - themable: {validated.themable}")
    except ValidationError as e:
        print("\n❌ VALIDATION FAILED!")
        print(f"\nErrors ({len(e.errors())} total):")
        for i, error in enumerate(e.errors(), 1):
            print(f"\n  Error {i}:")
            print(f"    Location: {' -> '.join(str(x) for x in error['loc'])}")
            print(f"    Message: {error['msg']}")
            print(f"    Type: {error['type']}")
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {type(e).__name__}")
        print(f"   {str(e)}")


def test_chunk(file_path: Path):
    """Test ChunkFileSchema validation."""
    print(f"\n{'='*60}")
    print(f"Testing CHUNK schema on: {file_path}")
    print(f"{'='*60}\n")

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    print("📄 Raw YAML data:")
    print(yaml.dump(data, default_flow_style=False))

    try:
        validated = ChunkFileSchema(**data)
        print("\n✅ VALIDATION SUCCESS!")
        print(f"\nValidated object:")
        print(f"  - type: {validated.type}")
        print(f"  - name: {validated.name}")
        print(f"  - version: {validated.version}")
        print(f"  - template: {validated.template[:50]}..." if len(validated.template) > 50 else f"  - template: {validated.template}")
        print(f"  - has implements: {validated.implements is not None}")
    except ValidationError as e:
        print("\n❌ VALIDATION FAILED!")
        print(f"\nErrors ({len(e.errors())} total):")
        for i, error in enumerate(e.errors(), 1):
            print(f"\n  Error {i}:")
            print(f"    Location: {' -> '.join(str(x) for x in error['loc'])}")
            print(f"    Message: {error['msg']}")
            print(f"    Type: {error['type']}")
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {type(e).__name__}")
        print(f"   {str(e)}")


def test_variations(file_path: Path):
    """Test VariationsFileSchema validation."""
    print(f"\n{'='*60}")
    print(f"Testing VARIATIONS schema on: {file_path}")
    print(f"{'='*60}\n")

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    print("📄 Raw YAML data:")
    print(yaml.dump(data, default_flow_style=False))

    try:
        validated = VariationsFileSchema(**data)
        print("\n✅ VALIDATION SUCCESS!")
        print(f"\nValidated object:")
        print(f"  - type: {validated.type}")
        print(f"  - name: {validated.name}")
        print(f"  - version: {validated.version}")
        print(f"  - variations count: {len(validated.variations)}")

        # Show first 5 variations
        items = list(validated.variations.items())[:5]
        print(f"\n  First {min(5, len(validated.variations))} variations:")
        for key, value in items:
            if isinstance(value, dict):
                parts = ', '.join(value.keys())
                print(f"    {key}: [multipart: {parts}]")
            else:
                preview = value[:40] + "..." if len(value) > 40 else value
                print(f"    {key}: {preview}")

        if len(validated.variations) > 5:
            print(f"  ... and {len(validated.variations) - 5} more")

    except ValidationError as e:
        print("\n❌ VALIDATION FAILED!")
        print(f"\nErrors ({len(e.errors())} total):")
        for i, error in enumerate(e.errors(), 1):
            print(f"\n  Error {i}:")
            print(f"    Location: {' -> '.join(str(x) for x in error['loc'])}")
            print(f"    Message: {error['msg']}")
            print(f"    Type: {error['type']}")
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {type(e).__name__}")
        print(f"   {str(e)}")


def test_theme(file_path: Path):
    """Test ThemeFileSchema validation."""
    print(f"\n{'='*60}")
    print(f"Testing THEME schema on: {file_path}")
    print(f"{'='*60}\n")

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    print("📄 Raw YAML data:")
    print(yaml.dump(data, default_flow_style=False))

    try:
        validated = ThemeFileSchema(**data)
        print("\n✅ VALIDATION SUCCESS!")
        print(f"\nValidated object:")
        print(f"  - type: {validated.type}")
        print(f"  - name: {validated.name}")
        print(f"  - version: {validated.version}")
        print(f"  - imports count: {len(validated.imports)}")
        print(f"  - variations: {validated.variations}")

        # Show imports with styles
        print(f"\n  Imports breakdown:")
        for key, value in validated.imports.items():
            if isinstance(value, list):
                print(f"    {key}: [Remove]")
            else:
                print(f"    {key}: {value}")

    except ValidationError as e:
        print("\n❌ VALIDATION FAILED!")
        print(f"\nErrors ({len(e.errors())} total):")
        for i, error in enumerate(e.errors(), 1):
            print(f"\n  Error {i}:")
            print(f"    Location: {' -> '.join(str(x) for x in error['loc'])}")
            print(f"    Message: {error['msg']}")
            print(f"    Type: {error['type']}")
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {type(e).__name__}")
        print(f"   {str(e)}")


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 test_schemas_manual.py template <yaml_file>")
        print("  python3 test_schemas_manual.py prompt <yaml_file>")
        print("  python3 test_schemas_manual.py chunk <yaml_file>")
        print("  python3 test_schemas_manual.py variations <yaml_file>")
        print("  python3 test_schemas_manual.py theme <yaml_file>")
        sys.exit(1)

    schema_type = sys.argv[1].lower()
    file_path = Path(sys.argv[2])

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    test_map = {
        'template': test_template,
        'prompt': test_prompt,
        'chunk': test_chunk,
        'variations': test_variations,
        'theme': test_theme,
    }

    if schema_type not in test_map:
        print(f"❌ Unknown schema type: {schema_type}")
        print(f"   Valid types: {', '.join(test_map.keys())}")
        sys.exit(1)

    test_map[schema_type](file_path)


if __name__ == '__main__':
    main()
