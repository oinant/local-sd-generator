#!/usr/bin/env python3
"""
Simple script to generate images from YAML prompt templates.

This bridges the new templating system (Phase 2) with the legacy JSON generation system.

Usage:
    python3 generate_from_template.py examples/prompts/quick_test.prompt.yaml --count 16
    python3 generate_from_template.py examples/prompts/sophia_expressions.prompt.yaml
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from templating import load_prompt_config, resolve_prompt
from config.global_config import load_global_config


def generate_legacy_json(prompt_config_path: str, max_count: int = None, output_file: str = None):
    """
    Generate legacy JSON format from YAML prompt template.

    Args:
        prompt_config_path: Path to .prompt.yaml file
        max_count: Maximum number of variations to generate (overrides config)
        output_file: Output JSON file path (optional)

    Returns:
        Path to generated JSON file
    """
    # Load config
    config_path = Path(prompt_config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Prompt config not found: {prompt_config_path}")

    config = load_prompt_config(config_path)

    # Override max_images if specified
    if max_count is not None:
        config.max_images = max_count

    # Resolve variations
    # Base path should be the examples/ directory, not prompts/
    base_path = config_path.parent.parent if config_path.parent.name == "prompts" else config_path.parent
    print(f"Loading template: {config.name}")
    print(f"Base path: {base_path}")

    variations = resolve_prompt(config, base_path=base_path)

    print(f"Generated {len(variations)} variations")

    # Convert to legacy JSON format
    legacy_format = {
        "session_name": config.name.lower().replace(" ", "_").replace("-", "_"),
        "prompt_template": None,  # Not used in legacy, variations have full prompts
        "negative_prompt": config.negative_prompt or "",
        "variations": [],
        "generation_config": {
            "seed_mode": config.seed_mode,
            "base_seed": config.seed,
            "generation_mode": config.generation_mode
        },
        "metadata": {
            "source": str(config_path),
            "generated_at": datetime.now().isoformat(),
            "total_variations": len(variations),
            "templating_system": "phase2"
        }
    }

    # Add variations
    for var in variations:
        legacy_format["variations"].append({
            "index": var.index,
            "prompt": var.final_prompt,
            "negative_prompt": var.negative_prompt,
            "seed": var.seed,
            "metadata": var.placeholders
        })

    # Determine output file
    if output_file is None:
        # Load global config to get output_dir
        global_config = load_global_config()
        output_dir = Path(global_config.output_dir) / 'dryrun'

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"generated_{legacy_format['session_name']}_{timestamp}.json"

    output_path = Path(output_file)

    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(legacy_format, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Generated: {output_path}")
    print(f"   {len(variations)} variations ready for generation")

    return output_path


def preview_variations(prompt_config_path: str, count: int = 3):
    """
    Preview first N variations without generating JSON.

    Args:
        prompt_config_path: Path to .prompt.yaml file
        count: Number of variations to preview
    """
    config_path = Path(prompt_config_path)
    config = load_prompt_config(config_path)

    # Base path should be the examples/ directory, not prompts/
    base_path = config_path.parent.parent if config_path.parent.name == "prompts" else config_path.parent
    variations = resolve_prompt(config, base_path=base_path)

    print(f"\n{'='*80}")
    print(f"Preview: {config.name}")
    print(f"{'='*80}\n")
    print(f"Total variations: {len(variations)}")
    print(f"Generation mode: {config.generation_mode}")
    print(f"Seed mode: {config.seed_mode}")
    print(f"Base seed: {config.seed}\n")

    for i, var in enumerate(variations[:count]):
        print(f"{'─'*80}")
        print(f"Variation {i} (seed {var.seed})")
        print(f"{'─'*80}")
        print(var.final_prompt)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate images from YAML prompt templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview first 3 variations
  python3 generate_from_template.py examples/prompts/quick_test.prompt.yaml --preview

  # Generate JSON with all variations from config
  python3 generate_from_template.py examples/prompts/sophia_expressions.prompt.yaml

  # Generate JSON with limited count
  python3 generate_from_template.py examples/prompts/portrait_full.prompt.yaml --count 50

  # Specify output file
  python3 generate_from_template.py examples/prompts/quick_test.prompt.yaml -o my_batch.json
        """
    )

    parser.add_argument(
        'prompt_config',
        help='Path to .prompt.yaml file'
    )

    parser.add_argument(
        '-c', '--count',
        type=int,
        help='Maximum number of variations to generate (overrides config)'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output JSON file path (default: auto-generated)'
    )

    parser.add_argument(
        '-p', '--preview',
        action='store_true',
        help='Preview variations without generating JSON'
    )

    parser.add_argument(
        '--preview-count',
        type=int,
        default=3,
        help='Number of variations to preview (default: 3)'
    )

    args = parser.parse_args()

    try:
        if args.preview:
            preview_variations(args.prompt_config, args.preview_count)
        else:
            output_path = generate_legacy_json(
                args.prompt_config,
                max_count=args.count,
                output_file=args.output
            )

            print(f"\nNext steps:")
            print(f"  1. Review the generated JSON: {output_path}")
            print(f"  2. Use with legacy image generator")
            print(f"  3. Or integrate with SD API directly")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
