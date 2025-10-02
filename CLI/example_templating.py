#!/usr/bin/env python3
"""
Example usage of the new templating system.

This demonstrates the Phase 1 implementation:
- Loading YAML variation files
- Using advanced selectors ([happy,sad], [random:5], [range:1-10])
- Resolving prompt configurations
- Combinatorial and random generation modes
"""

from pathlib import Path
from CLI.templating import load_prompt_config, resolve_prompt


def main():
    """Run example templating workflow."""
    print("=" * 60)
    print("Next-Gen Templating System - Phase 1 Demo")
    print("=" * 60)
    print()

    # Path to test fixtures
    fixtures_dir = Path(__file__).parent.parent / "tests" / "templating" / "fixtures"
    prompt_file = fixtures_dir / "simple_test.prompt.yaml"

    # Load configuration
    print(f"📄 Loading prompt config: {prompt_file.name}")
    config = load_prompt_config(prompt_file)
    print(f"   Name: {config.name}")
    print(f"   Mode: {config.generation_mode}")
    print(f"   Seed mode: {config.seed_mode}")
    print(f"   Imports: {len(config.imports)} variation files")
    print()

    # Resolve variations
    print("🔄 Resolving variations...")
    variations = resolve_prompt(config, base_path=fixtures_dir.parent)
    print(f"   Generated {len(variations)} variations")
    print()

    # Display first 3 variations
    print("📋 First 3 variations:")
    print("-" * 60)
    for i, var in enumerate(variations[:3]):
        print(f"\n[{i+1}] Variation #{var.index}")
        print(f"    Seed: {var.seed}")
        print(f"    Placeholders:")
        for key, value in var.placeholders.items():
            print(f"      - {key}: {value}")
        print(f"    Final prompt:")
        print(f"      {var.final_prompt}")
        print(f"    Negative:")
        print(f"      {var.negative_prompt}")

    print("\n" + "=" * 60)
    print("✅ Phase 1 implementation complete!")
    print()
    print("Supported features:")
    print("  ✓ YAML variation files")
    print("  ✓ Advanced selectors: [keys], [indices], [range:N-M], [random:N]")
    print("  ✓ Combinatorial and random generation modes")
    print("  ✓ Progressive, fixed, and random seed modes")
    print("  ✓ Prompt config files (.prompt.yaml)")
    print("=" * 60)


if __name__ == "__main__":
    main()
