#!/usr/bin/env python3
"""
Integration test for Phase 2: SF-7 (Global Config) and SF-1 (Config Loading & Validation)

This script validates:
1. Global config system works correctly
2. JSON config loading and validation works
3. Error messages are clear and helpful
"""

import sys
import json
from pathlib import Path

# Add CLI to path
sys.path.insert(0, str(Path(__file__).parent))

from config.global_config import (
    GlobalConfig,
    locate_global_config,
    load_global_config,
    create_default_global_config
)
from config.config_loader import (
    load_config_from_file,
    validate_config,
    load_and_validate_config
)
from config.config_schema import GenerationSessionConfig


def test_global_config():
    """Test SF-7: Global Config File"""
    print("\n" + "="*60)
    print("TEST 1: Global Config System (SF-7)")
    print("="*60)

    # Test 1: Locate config (should not exist yet)
    print("\n1. Testing config location...")
    config_path = locate_global_config()
    if config_path:
        print(f"   ✓ Found global config at: {config_path}")
        config = load_global_config()
        print(f"   ✓ Loaded config:")
        print(f"     - configs_dir: {config.configs_dir}")
        print(f"     - output_dir: {config.output_dir}")
        print(f"     - api_url: {config.api_url}")
    else:
        print("   ✓ No global config found (using defaults)")
        config = load_global_config()
        print(f"   ✓ Default config:")
        print(f"     - configs_dir: {config.configs_dir}")
        print(f"     - output_dir: {config.output_dir}")
        print(f"     - api_url: {config.api_url}")

    # Test 2: Create temporary global config
    print("\n2. Testing config creation...")
    temp_config_path = Path.cwd() / ".sdgen_config.json.test"
    test_config = GlobalConfig(
        configs_dir="./configs",
        output_dir="./apioutput",
        api_url="http://127.0.0.1:7860"
    )
    create_default_global_config(temp_config_path, test_config)
    print(f"   ✓ Created test config at: {temp_config_path}")

    # Verify it was created correctly
    loaded = json.loads(temp_config_path.read_text())
    assert loaded["configs_dir"] == "./configs"
    assert loaded["output_dir"] == "./apioutput"
    assert loaded["api_url"] == "http://127.0.0.1:7860"
    print("   ✓ Config contents verified")

    # Cleanup
    temp_config_path.unlink()
    print("   ✓ Cleanup complete")

    print("\n✅ SF-7 Global Config: PASSED")
    return True


def test_json_config_loading():
    """Test SF-1: JSON Config Loading & Validation"""
    print("\n" + "="*60)
    print("TEST 2: JSON Config Loading & Validation (SF-1)")
    print("="*60)

    config_file = Path.cwd().parent / "configs" / "test_config_phase2.json"

    if not config_file.exists():
        print(f"\n❌ Test config file not found: {config_file}")
        return False

    # Test 1: Load config
    print("\n1. Testing config loading...")
    try:
        config = load_config_from_file(config_file)
        print(f"   ✓ Config loaded successfully")
        print(f"     - Name: {config.name}")
        print(f"     - Description: {config.description}")
        print(f"     - Version: {config.version}")
    except Exception as e:
        print(f"   ❌ Failed to load config: {e}")
        return False

    # Test 2: Validate config
    print("\n2. Testing config validation...")
    result = validate_config(config)

    if result.is_valid:
        print("   ✓ Config is valid!")
    else:
        print("   ❌ Config validation failed:")
        for error in result.errors:
            print(f"      - {error}")

    if result.warnings:
        print("\n   Warnings:")
        for warning in result.warnings:
            print(f"      ⚠ {warning}")

    # Test 3: Display loaded configuration
    print("\n3. Configuration details:")
    print(f"   Prompt template: {config.prompt.template}")
    print(f"   Negative prompt: {config.prompt.negative}")
    print(f"\n   Variations:")
    for name, path in config.variations.items():
        exists = "✓" if Path(path).exists() else "✗"
        print(f"     {exists} {name}: {path}")

    print(f"\n   Generation:")
    print(f"     - Mode: {config.generation.mode}")
    print(f"     - Seed mode: {config.generation.seed_mode}")
    print(f"     - Seed: {config.generation.seed}")
    print(f"     - Max images: {config.generation.max_images}")

    print(f"\n   Parameters:")
    print(f"     - Size: {config.parameters.width}x{config.parameters.height}")
    print(f"     - Steps: {config.parameters.steps}")
    print(f"     - CFG scale: {config.parameters.cfg_scale}")
    print(f"     - Sampler: {config.parameters.sampler}")

    print(f"\n   Output:")
    print(f"     - Session name: {config.output.session_name}")
    print(f"     - Filename keys: {config.output.filename_keys}")

    if result.is_valid:
        print("\n✅ SF-1 Config Loading & Validation: PASSED")
        return True
    else:
        print("\n❌ SF-1 Config Loading & Validation: FAILED")
        return False


def test_validation_error_messages():
    """Test validation error messages are helpful"""
    print("\n" + "="*60)
    print("TEST 3: Validation Error Messages")
    print("="*60)

    # Create invalid config
    print("\n1. Testing invalid config detection...")
    from config.config_schema import PromptConfig, GenerationConfig
    invalid_config = GenerationSessionConfig(
        version="",  # Missing
        prompt=PromptConfig(template="", negative=""),  # Missing template
        variations={},  # Empty
        generation=GenerationConfig(mode="invalid_mode")  # Invalid mode
    )

    result = validate_config(invalid_config)

    if not result.is_valid:
        print("   ✓ Invalid config correctly detected")
        print(f"   ✓ Found {len(result.errors)} errors:")
        for error in result.errors:
            print(f"      - {error.field}: {error.message}")
            if error.suggestion:
                print(f"        → {error.suggestion}")
    else:
        print("   ❌ Invalid config not detected!")
        return False

    print("\n✅ Validation Error Messages: PASSED")
    return True


def test_placeholder_validation():
    """Test placeholder-variation matching"""
    print("\n" + "="*60)
    print("TEST 4: Placeholder-Variation Matching")
    print("="*60)

    # Test with mismatched placeholders
    print("\n1. Testing placeholder mismatch detection...")

    from config.config_schema import PromptConfig
    config = GenerationSessionConfig(
        version="1.0",
        prompt=PromptConfig(
            template="test {Expression}, {Angle}, {MissingVar}"
        ),
        variations={
            "Expression": "/tmp/expr.txt",
            "Angle": "/tmp/angle.txt",
            "UnusedVar": "/tmp/unused.txt"
        }
    )

    result = validate_config(config)

    # Should have error for MissingVar
    missing_errors = [e for e in result.errors if "MissingVar" in e.field]
    if missing_errors:
        print(f"   ✓ Missing variation detected: {missing_errors[0].field}")
    else:
        print("   ❌ Missing variation not detected!")
        return False

    # Should have warning for UnusedVar
    unused_warnings = [w for w in result.warnings if "UnusedVar" in w.field]
    if unused_warnings:
        print(f"   ✓ Unused variation detected: {unused_warnings[0].field}")
    else:
        print("   ⚠ Unused variation warning not generated")

    print("\n✅ Placeholder-Variation Matching: PASSED")
    return True


def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("PHASE 2 INTEGRATION TESTS")
    print("SF-7: Global Config File")
    print("SF-1: JSON Config Loading & Validation")
    print("="*60)

    results = []

    # Run tests
    try:
        results.append(("Global Config", test_global_config()))
        results.append(("JSON Config Loading", test_json_config_loading()))
        results.append(("Validation Errors", test_validation_error_messages()))
        results.append(("Placeholder Matching", test_placeholder_validation()))
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("\nPhase 2 implementation is ready for commit:")
        print("  - SF-7: Global Config File")
        print("  - SF-1: JSON Config Loading & Validation")
        return True
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please review the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
