#!/usr/bin/env python3
"""
Fix variation file paths in JSON configs

Fixes:
1. Removes selectors from placeholder names (#|X, $X, :X)
2. Corrects filenames (removes extra 's', fixes case)
3. Finds correct subdirectory (my_prompts vs generalAndBasicPrompt_v19)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Tuple


# Mapping of placeholder names to actual filenames
FILENAME_MAPPING = {
    "FacialExpression": "Pony_FactialExpression.txt",
    "Angle": "General_Angle.txt",
    "Framing": "General_Framing.txt",
    "Shoes": "Attires_NSFW_Shoes.txt",
    "Waist": "Attires_Accessory_Waist.txt",
    "Style": "General_Styles.txt",
    "BreastFeature": "Pony_BreastFeature.txt",
    "BreastShape": "Pony_BreastShape.txt",
    "BreastSize": "Pony_BreastSize.txt",
    "Cum": "Pony_Cum.txt",
    "Outfits": "outfits.txt",
    "Tits": "tits.txt",
    "HairCut": "haircuts.txt",
    "SoloAction": "soloaction.txt",
    "SoloAction2": "soloaction2.txt",
    "SoloPose": "solopose.txt",
    "SoloPose2": "solopose2.txt",
    "SoloPoseHands": "soloposehands.txt",
    "SoloPoseLegs": "soloposelegs.txt",
    "HairColor": "haircolors.txt",
    "SexAct": "sexact.txt",
    "Focus": "focus.txt",
    "Places": "places.txt",
    "BottomOutfits": "Attires_NSFW_Lowerbody.txt",
    "BottomOutfits2": "categories.txt",  # Special: in bottoms/ subfolder
    "AngleToViewer": "angletoviewer.txt",
    "GeneralPosing": "General_Posing.txt",
}

# Files in my_prompts subdirectory
MY_PROMPTS_FILES = {
    "outfits.txt",
    "tits.txt",
    "haircuts.txt",
    "soloaction.txt",
    "soloaction2.txt",
    "solopose.txt",
    "solopose2.txt",
    "soloposehands.txt",
    "soloposelegs.txt",
    "haircolors.txt",
    "sexact.txt",
    "focus.txt",
    "places.txt",
    "categories.txt",
    "angletoviewer.txt",
}


def clean_placeholder_name(name: str) -> str:
    """
    Remove selectors from placeholder name.

    Examples:
        HairColor#|18 -> HairColor
        Angle:#|6|4|2$2 -> Angle
        Tits:#|4 -> Tits
    """
    # Remove everything after #, $, or :
    return re.sub(r'[#$:].*', '', name)


def find_actual_filename(placeholder: str, variations_dir: Path) -> Tuple[str, bool]:
    """
    Find actual filename for placeholder.

    Returns:
        (relative_path, found) tuple
    """
    # Get base filename from mapping
    filename = FILENAME_MAPPING.get(placeholder)

    if not filename:
        # Fallback: try lowercase version
        filename = placeholder.lower() + "s.txt"

    # Special case: BottomOutfits2 is in bottoms/ subfolder
    if placeholder == "BottomOutfits2":
        path = variations_dir / "my_prompts" / "bottoms" / filename
        if path.exists():
            return ("./variations/my_prompts/bottoms/" + filename, True)

    # Check if it's in my_prompts
    if filename in MY_PROMPTS_FILES:
        path = variations_dir / "my_prompts" / filename
        if path.exists():
            return ("./variations/my_prompts/" + filename, True)

    # Check in generalAndBasicPrompt_v19
    path = variations_dir / "generalAndBasicPrompt_v19" / filename
    if path.exists():
        return ("./variations/generalAndBasicPrompt_v19/" + filename, True)

    # Check in my_prompts as fallback
    path = variations_dir / "my_prompts" / filename
    if path.exists():
        return ("./variations/my_prompts/" + filename, True)

    # Not found - return best guess
    if filename in MY_PROMPTS_FILES:
        return ("./variations/my_prompts/" + filename, False)
    else:
        return ("./variations/generalAndBasicPrompt_v19/" + filename, False)


def fix_config_variations(config: dict, variations_dir: Path, verbose: bool = False) -> Tuple[dict, int]:
    """
    Fix variations section in config.

    Returns:
        (fixed_config, changes_count) tuple
    """
    variations = config.get("variations", {})
    if not variations:
        return config, 0

    new_variations = {}
    changes = 0

    for placeholder_name, path in variations.items():
        # Clean placeholder name
        clean_name = clean_placeholder_name(placeholder_name)

        # Find actual file
        new_path, found = find_actual_filename(clean_name, variations_dir)

        # Track changes
        if clean_name != placeholder_name or new_path != path:
            if verbose:
                if clean_name != placeholder_name:
                    print(f"    Placeholder: {placeholder_name} → {clean_name}")
                if new_path != path:
                    status = "✓" if found else "?"
                    print(f"    Path: {path} → {new_path} {status}")
            changes += 1

        new_variations[clean_name] = new_path

    config["variations"] = new_variations

    # Also fix filename_keys in output section
    output = config.get("output", {})
    if "filename_keys" in output:
        old_keys = output["filename_keys"]
        new_keys = [clean_placeholder_name(k) for k in old_keys]

        if new_keys != old_keys:
            output["filename_keys"] = new_keys
            if verbose:
                print(f"    Filename keys: {len(old_keys)} cleaned")

        config["output"] = output

    return config, changes


def fix_config_file(config_path: Path, variations_dir: Path, dry_run: bool = False, verbose: bool = False) -> bool:
    """
    Fix a single config file.

    Returns True if changes were made.
    """
    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Fix variations
    fixed_config, changes = fix_config_variations(config, variations_dir, verbose)

    if changes == 0:
        return False

    # Save if not dry-run
    if not dry_run:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(fixed_config, f, indent=2, ensure_ascii=False)
            f.write('\n')

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Fix variation file paths in JSON configs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fix all configs (dry-run)
  python fix_variation_paths.py --configs-dir D:\\StableDiffusion\\private\\configs --dry-run

  # Fix all configs for real
  python fix_variation_paths.py --configs-dir D:\\StableDiffusion\\private\\configs

  # Fix with verbose output
  python fix_variation_paths.py --configs-dir D:\\StableDiffusion\\private\\configs --verbose

  # Fix single config
  python fix_variation_paths.py --config config.json --variations-dir variations/
        """
    )

    parser.add_argument(
        '--configs-dir',
        type=Path,
        help='Directory containing config files'
    )

    parser.add_argument(
        '--config',
        type=Path,
        help='Single config file to fix'
    )

    parser.add_argument(
        '--variations-dir',
        type=Path,
        help='Variations directory (default: configs-dir/variations)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed changes'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.configs_dir and not args.config:
        parser.error("Either --configs-dir or --config is required")

    try:
        if args.configs_dir:
            # Batch mode
            configs_dir = args.configs_dir
            variations_dir = args.variations_dir or (configs_dir / "variations")

            if not configs_dir.exists():
                print(f"❌ Error: Configs directory not found: {configs_dir}")
                return 1

            if not variations_dir.exists():
                print(f"❌ Error: Variations directory not found: {variations_dir}")
                return 1

            # Find all JSON configs
            configs = sorted(configs_dir.glob("*.json"))

            if not configs:
                print(f"⚠️  No JSON files found in {configs_dir}")
                return 0

            print(f"🔍 Found {len(configs)} config file(s)")
            print(f"📁 Variations dir: {variations_dir}\n")

            if args.dry_run:
                print("🔎 DRY RUN - No files will be modified\n")

            changed_count = 0
            unchanged_count = 0

            for config_path in configs:
                print(f"📄 {config_path.name}")

                if fix_config_file(config_path, variations_dir, args.dry_run, args.verbose):
                    changed_count += 1
                    if not args.verbose:
                        print("  ✏️  Fixed")
                else:
                    unchanged_count += 1
                    if args.verbose:
                        print("  ✓ No changes needed")

                print()

            # Summary
            print("=" * 60)
            print("Summary")
            print("=" * 60)
            print(f"✏️  Changed:   {changed_count}")
            print(f"✓  Unchanged: {unchanged_count}")
            print(f"📊 Total:     {len(configs)}")
            print("=" * 60)

            if args.dry_run and changed_count > 0:
                print("\n💡 Run without --dry-run to apply changes")

        else:
            # Single file mode
            config_path = args.config

            if not config_path.exists():
                print(f"❌ Error: Config file not found: {config_path}")
                return 1

            # Determine variations dir
            if args.variations_dir:
                variations_dir = args.variations_dir
            else:
                variations_dir = config_path.parent / "variations"

            if not variations_dir.exists():
                print(f"❌ Error: Variations directory not found: {variations_dir}")
                return 1

            print(f"📄 {config_path.name}\n")

            if fix_config_file(config_path, variations_dir, args.dry_run, args.verbose):
                if not args.dry_run:
                    print("\n✅ Config updated")
                else:
                    print("\n🔎 Changes would be applied (run without --dry-run)")
            else:
                print("✓ No changes needed")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
