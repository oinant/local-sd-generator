#!/usr/bin/env python3
"""
Test script to reproduce the parameters bug in V2 standalone prompts.

Bug: Standalone .prompt.yaml files (without implements:) lose their parameters:
during orchestration, resulting in default SD API parameters being used.
"""

import sys
from pathlib import Path

# Add CLI/src to path
sys.path.insert(0, str(Path(__file__).parent / 'CLI' / 'src'))

from templating.v2.orchestrator import V2Pipeline


def test_standalone_parameters():
    """Test that standalone prompts preserve their parameters."""

    # Use the real Hassaku_Chloé.prompt.yaml file
    config_path = '/mnt/d/StableDiffusion/private-new/prompts/hassaku/Hassaku_Chloé.prompt.yaml'

    print("=" * 60)
    print("Testing V2 Standalone Prompt Parameters")
    print("=" * 60)
    print(f"\nConfig: {config_path}\n")

    # Initialize pipeline
    pipeline = V2Pipeline()

    # Step 1: Load config
    print("Step 1: Loading config...")
    config = pipeline.load(config_path)
    print(f"  Config type: {type(config).__name__}")
    print(f"  Has 'parameters' attribute: {hasattr(config, 'parameters')}")
    if hasattr(config, 'parameters'):
        print(f"  Config parameters: {config.parameters}")
    else:
        print("  ⚠️  Config has NO 'parameters' attribute!")

    # Step 2: Resolve inheritance and imports
    print("\nStep 2: Resolving context...")
    context = pipeline.resolve(config)
    print(f"  Context parameters: {context.parameters}")

    if not context.parameters:
        print("  ❌ BUG: Context parameters are EMPTY!")
    else:
        print("  ✓ Context parameters loaded")

    # Step 3: Generate prompts
    print("\nStep 3: Generating prompts...")
    prompts = pipeline.generate(config, context)

    if prompts:
        first_prompt = prompts[0]
        print(f"  Generated {len(prompts)} prompts")
        print(f"  First prompt parameters: {first_prompt.get('parameters', {})}")

        # Check if parameters match expected values from YAML
        params = first_prompt.get('parameters', {})
        expected = {
            'width': 832,
            'height': 1216,
            'steps': 24,
            'cfg_scale': 3,
            'sampler': 'DPM++ 2M Karras'
        }

        print("\n" + "=" * 60)
        print("Parameter Comparison:")
        print("=" * 60)

        all_ok = True
        for key, expected_val in expected.items():
            actual_val = params.get(key)
            status = "✓" if actual_val == expected_val else "❌"
            print(f"  {status} {key}: {actual_val} (expected {expected_val})")
            if actual_val != expected_val:
                all_ok = False

        print("\n" + "=" * 60)
        if all_ok:
            print("✓ ALL PARAMETERS CORRECT")
        else:
            print("❌ PARAMETERS MISMATCH - BUG CONFIRMED")
        print("=" * 60)

    else:
        print("  ❌ No prompts generated!")


if __name__ == '__main__':
    test_standalone_parameters()
