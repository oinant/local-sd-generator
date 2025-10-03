#!/usr/bin/env python3
"""
Phase 2 Demo: End-to-end demonstration of chunk + multi-field templating.

This demo shows the complete flow:
1. Load Emma character (chunk)
2. Load ethnic features (multi-field variations)
3. Load poses (regular variations)
4. Resolve with "with" syntax
5. Generate 4 variations (2 ethnicities × 2 poses)
"""

from pathlib import Path
from CLI.templating import load_prompt_config, resolve_prompt


def main():
    # Path to fixtures
    fixtures_path = Path(__file__).parent / "tests" / "templating" / "fixtures"
    config_path = fixtures_path / "prompts" / "emma_variations.prompt.yaml"

    print("=" * 80)
    print("Phase 2 Demo: Chunk Templates + Multi-Field Expansion")
    print("=" * 80)
    print()

    # Load configuration
    print(f"Loading configuration from: {config_path}")
    config = load_prompt_config(config_path)
    print(f"  Name: {config.name}")
    print(f"  Generation mode: {config.generation_mode}")
    print(f"  Seed mode: {config.seed_mode}")
    print(f"  Base seed: {config.seed}")
    print()

    # Resolve
    print("Resolving prompt variations...")
    variations = resolve_prompt(config, base_path=fixtures_path)
    print(f"  Generated {len(variations)} variations")
    print()

    # Display results
    print("=" * 80)
    print("Generated Variations")
    print("=" * 80)
    print()

    for i, var in enumerate(variations):
        print(f"{'─' * 80}")
        print(f"Variation {i} (seed {var.seed})")
        print(f"{'─' * 80}")
        print(var.final_prompt)
        print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print(f"✓ Successfully generated {len(variations)} variations")
    print(f"✓ Each variation combines:")
    print(f"  - Emma's base character data (name, age, body type)")
    print(f"  - Ethnicity multi-field expansion (skin, hair, eyes)")
    print(f"  - Pose variation")
    print(f"  - Technical quality prompts")
    print()
    print("Phase 2 integration: WORKING ✓")
    print()


if __name__ == "__main__":
    main()
