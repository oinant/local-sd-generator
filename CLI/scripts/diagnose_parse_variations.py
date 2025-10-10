#!/usr/bin/env python3
"""
Diagnostic script to trace parse_variations() behavior.

Tests both isolated parsing and import_resolver flow to identify divergence.
"""

import sys
from pathlib import Path
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from templating.v2.loaders.yaml_loader import YamlLoader
from templating.v2.loaders.parser import ConfigParser
from templating.v2.resolvers.import_resolver import ImportResolver


def test_isolated_parsing():
    """Test parse_variations() in isolation."""
    print("=" * 80)
    print("TEST 1: Isolated parse_variations()")
    print("=" * 80)

    # Load raw YAML data
    test_file = Path(__file__).parent.parent / 'tests/templating/fixtures/variations/haircolors_structured.yaml'

    with open(test_file, 'r', encoding='utf-8') as f:
        raw_data = yaml.safe_load(f)

    print(f"\n📥 Raw YAML data keys: {list(raw_data.keys())}")
    print(f"   type: {raw_data.get('type')}")
    print(f"   name: {raw_data.get('name')}")
    print(f"   version: {raw_data.get('version')}")
    print(f"   variations keys: {list(raw_data.get('variations', {}).keys())}")

    # Parse with ConfigParser
    parser = ConfigParser()
    result = parser.parse_variations(raw_data)

    print(f"\n✅ parse_variations() result keys: {list(result.keys())}")
    print(f"   'type' in result: {'type' in result}")
    print(f"   'name' in result: {'name' in result}")
    print(f"   'version' in result: {'version' in result}")
    print(f"   'variations' in result: {'variations' in result}")
    print(f"\n✅ Result is ONLY variations: {result == raw_data.get('variations')}")

    return result


def test_import_resolver_flow():
    """Test parse_variations() through ImportResolver."""
    print("\n" + "=" * 80)
    print("TEST 2: parse_variations() via ImportResolver")
    print("=" * 80)

    # Initialize components
    loader = YamlLoader()
    parser = ConfigParser()
    resolver = ImportResolver(loader, parser)

    # Test file
    test_file = Path(__file__).parent.parent / 'tests/templating/fixtures/variations/haircolors_structured.yaml'
    base_path = test_file.parent

    print(f"\n📂 Loading: {test_file.name}")
    print(f"   Base path: {base_path}")

    # Simulate _load_variation_file()
    resolved_path = loader.resolve_path(test_file.name, base_path)
    print(f"\n🔍 Resolved path: {resolved_path}")

    # Load file (this is where the issue might be)
    data = loader.load_file(resolved_path, base_path)
    print(f"\n📥 YamlLoader.load_file() result keys: {list(data.keys())}")
    print(f"   type: {data.get('type')}")
    print(f"   name: {data.get('name')}")
    print(f"   version: {data.get('version')}")
    print(f"   'variations' in data: {'variations' in data}")

    # Parse variations (should extract only variations)
    result = parser.parse_variations(data)
    print(f"\n✅ parse_variations() result keys: {list(result.keys())}")
    print(f"   'type' in result: {'type' in result}")
    print(f"   'name' in result: {'name' in result}")
    print(f"   'version' in result: {'version' in result}")

    return data, result


def test_multi_source_merge():
    """Test multi-source merging (where duplicate key error occurs)."""
    print("\n" + "=" * 80)
    print("TEST 3: Multi-source merge with structured format")
    print("=" * 80)

    # Initialize components
    loader = YamlLoader()
    parser = ConfigParser()
    resolver = ImportResolver(loader, parser)

    # Test with two structured files
    test_dir = Path(__file__).parent.parent / 'tests/templating/fixtures/variations'
    sources = [
        'haircolors_structured.yaml',
        'hairstyles.yaml'  # Assuming this exists as flat format
    ]

    print(f"\n📋 Sources to merge:")
    for src in sources:
        src_path = test_dir / src
        if src_path.exists():
            with open(src_path, 'r') as f:
                data = yaml.safe_load(f)
            print(f"   - {src}: {list(data.keys())}")

    try:
        # This should trigger the duplicate key detection
        merged = resolver._merge_multi_sources(
            sources,
            test_dir,
            'TestImport'
        )
        print(f"\n✅ Merge successful!")
        print(f"   Result keys: {list(merged.keys())}")
    except ValueError as e:
        print(f"\n❌ Merge failed: {e}")
        print(f"\n🔍 Analysis:")
        print(f"   This is the duplicate key error from import_resolver.py:163-166")
        print(f"   It means parse_variations() is NOT extracting variations correctly")
        print(f"   The full dict (with type, name, version) is being returned instead")


def main():
    """Run all diagnostic tests."""
    print("\n🔬 DIAGNOSTIC: parse_variations() Flow Analysis")
    print("=" * 80)

    # Test 1: Isolated parsing
    isolated_result = test_isolated_parsing()

    # Test 2: Through ImportResolver
    loader_data, resolver_result = test_import_resolver_flow()

    # Test 3: Multi-source merge (where error occurs)
    test_multi_source_merge()

    # Summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)

    print("\n🔍 Key Findings:")
    print(f"   1. Isolated parse_variations() works: {isolated_result == {'BobCut': 'bob cut hair, chin-length', 'LongHair': 'long flowing hair, waist-length', 'PixieCut': 'short pixie cut, edgy', 'Braided': 'braided hair, intricate'}}")
    print(f"   2. YamlLoader.load_file() returns: {list(loader_data.keys())}")
    print(f"   3. ImportResolver flow result: {list(resolver_result.keys())}")

    print("\n💡 Conclusion:")
    if 'type' in resolver_result or 'name' in resolver_result:
        print("   ❌ parse_variations() is NOT filtering metadata keys in ImportResolver flow")
        print("   ❌ This causes duplicate key errors when merging multi-source imports")
        print("   ⚠️  The fix in parser.py:151-157 is correct but not being used")
    else:
        print("   ✅ parse_variations() correctly extracts only variations")
        print("   ✅ No metadata keys in result")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
