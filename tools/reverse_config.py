    #!/usr/bin/env python3
"""
Reverse Config Generator - Generate JSON config from existing session

Parses session_config.txt and extracts PNG metadata to recreate a JSON config file.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add CLI to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "CLI"))

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available, cannot extract PNG metadata")


def parse_session_config(config_path: Path) -> Dict[str, Any]:
    """
    Parse session_config.txt file.

    Returns:
        Dictionary with extracted configuration
    """
    config = {
        "prompt_template": None,
        "negative_prompt": None,
        "parameters": {},
        "additional_info": {},
        "session_name": None,
        "date": None
    }

    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract session name
    match = re.search(r'Nom de session:\s*(.+)', content)
    if match:
        config["session_name"] = match.group(1).strip()

    # Extract date
    match = re.search(r'Date de génération:\s*(.+)', content)
    if match:
        config["date"] = match.group(1).strip()

    # Extract prompt (multi-line)
    prompt_match = re.search(r'Prompt de base:\s*\n(.*?)\n\nPrompt négatif:', content, re.DOTALL)
    if prompt_match:
        config["prompt_template"] = prompt_match.group(1).strip()

    # Extract negative prompt
    neg_match = re.search(r'Prompt négatif:\s*\n(.*?)\n\n', content, re.DOTALL)
    if neg_match:
        config["negative_prompt"] = neg_match.group(1).strip()

    # Extract generation parameters
    params_section = re.search(r'PARAMÈTRES DE GÉNÉRATION.*?\n-+\n(.*?)\n-+', content, re.DOTALL)
    if params_section:
        params_text = params_section.group(1)

        for line in params_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Convert to appropriate type
                if key in ['steps', 'width', 'height', 'batch_size', 'n_iter']:
                    config["parameters"][key] = int(value)
                elif key == 'cfg_scale':
                    config["parameters"][key] = float(value)
                else:
                    config["parameters"][key] = value

    # Extract additional info
    info_section = re.search(r'INFORMATIONS ADDITIONNELLES.*?\n-+\n(.*?)(?:\n={3,}|$)', content, re.DOTALL)
    if info_section:
        info_text = info_section.group(1)

        for line in info_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Try to convert to int
                try:
                    value = int(value)
                except ValueError:
                    pass

                config["additional_info"][key] = value

    return config


def extract_png_metadata(png_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract SD generation parameters from PNG metadata.

    Returns:
        Dictionary with parameters or None if not available
    """
    if not PIL_AVAILABLE:
        return None

    try:
        img = Image.open(png_path)
        params_str = img.info.get("parameters", "")

        if not params_str:
            return None

        # Parse parameters string
        # Format: "prompt\nNegative prompt: neg\nSteps: 30, Sampler: ..., CFG scale: 7, Seed: 42, Size: 512x768"

        metadata = {}

        # Extract seed
        seed_match = re.search(r'Seed:\s*(\d+)', params_str)
        if seed_match:
            metadata['seed'] = int(seed_match.group(1))

        # Extract steps
        steps_match = re.search(r'Steps:\s*(\d+)', params_str)
        if steps_match:
            metadata['steps'] = int(steps_match.group(1))

        # Extract CFG scale
        cfg_match = re.search(r'CFG scale:\s*([\d.]+)', params_str)
        if cfg_match:
            metadata['cfg_scale'] = float(cfg_match.group(1))

        # Extract sampler
        sampler_match = re.search(r'Sampler:\s*([^,]+)', params_str)
        if sampler_match:
            metadata['sampler'] = sampler_match.group(1).strip()

        # Extract size
        size_match = re.search(r'Size:\s*(\d+)x(\d+)', params_str)
        if size_match:
            metadata['width'] = int(size_match.group(1))
            metadata['height'] = int(size_match.group(2))

        return metadata

    except Exception as e:
        print(f"Warning: Could not extract metadata from {png_path}: {e}")
        return None


def extract_placeholders(prompt: str) -> List[str]:
    """Extract placeholder names from prompt template."""
    return re.findall(r'\{([^}:]+)(?::[^}]*)?\}', prompt)


def detect_variation_files(session_dir: Path, placeholders: List[str]) -> Dict[str, str]:
    """
    Try to detect which variation files were used.

    Best effort based on session_config.txt additional info.
    """
    variations = {}

    # For now, return empty dict - user will need to fill this manually
    # or we can add logic to search in variations/ directory

    return variations


def generate_json_config(session_dir: Path, output_path: Optional[Path] = None,
                         inline_variations: bool = False, dry_run: bool = False) -> Dict[str, Any]:
    """
    Generate JSON config from session directory.

    Args:
        session_dir: Path to session directory
        output_path: Where to save config (None = auto-generate)
        inline_variations: Include variation values inline instead of file paths
        dry_run: Don't write file, just return config

    Returns:
        Generated config dictionary
    """
    # Find session_config.txt
    config_txt = session_dir / "session_config.txt"
    if not config_txt.exists():
        raise FileNotFoundError(f"No session_config.txt found in {session_dir}")

    print(f"📖 Reading {config_txt.name}...")
    session_config = parse_session_config(config_txt)

    # Try to extract metadata from first PNG
    png_files = sorted(session_dir.glob("*.png"))
    png_metadata = None

    if png_files and PIL_AVAILABLE:
        print(f"🖼️  Extracting metadata from {png_files[0].name}...")
        png_metadata = extract_png_metadata(png_files[0])

    # Build JSON config
    json_config = {
        "version": "1.0",
        "name": f"Regenerate: {session_config.get('session_name', 'unknown')}",
        "description": f"Auto-generated from session {session_dir.name}",
    }

    # Prompt section
    prompt_template = session_config.get("prompt_template") or session_config["additional_info"].get("prompt_template", "")
    json_config["prompt"] = {
        "template": prompt_template,
        "negative": session_config.get("negative_prompt", "")
    }

    # Detect placeholders
    placeholders = extract_placeholders(prompt_template)
    print(f"🔍 Detected placeholders: {placeholders}")

    # Variations section
    if placeholders:
        if inline_variations:
            # TODO: Extract actual values used from filenames
            json_config["variations"] = {ph: [] for ph in placeholders}
            print("⚠️  Inline variations requested but not implemented yet")
            print("    You'll need to fill variation values manually")
        else:
            # Use file paths (user needs to update)
            json_config["variations"] = {
                ph: f"./variations/{ph.lower()}s.txt"
                for ph in placeholders
            }
            print("⚠️  Variation file paths are placeholders - update them manually")
    else:
        json_config["variations"] = {}

    # Generation section
    seed = session_config["additional_info"].get("seed_principal", 42)
    if png_metadata and 'seed' in png_metadata:
        seed = png_metadata['seed']

    json_config["generation"] = {
        "mode": "combinatorial",  # Default guess
        "seed_mode": "progressive",  # Default guess
        "seed": seed,
        "max_images": session_config["additional_info"].get("nombre_images_demandees", -1)
    }

    # Parameters section - merge session_config and PNG metadata
    params = {}

    # From session_config.txt
    if session_config["parameters"]:
        params.update({
            "width": session_config["parameters"].get("width", 512),
            "height": session_config["parameters"].get("height", 768),
            "steps": session_config["parameters"].get("steps", 30),
            "cfg_scale": session_config["parameters"].get("cfg_scale", 7.0),
            "sampler": session_config["parameters"].get("sampler_name", "Euler a"),
            "batch_size": session_config["parameters"].get("batch_size", 1),
            "batch_count": session_config["parameters"].get("n_iter", 1)
        })

    # Override with PNG metadata if available
    if png_metadata:
        if 'width' in png_metadata:
            params['width'] = png_metadata['width']
        if 'height' in png_metadata:
            params['height'] = png_metadata['height']
        if 'steps' in png_metadata:
            params['steps'] = png_metadata['steps']
        if 'cfg_scale' in png_metadata:
            params['cfg_scale'] = png_metadata['cfg_scale']
        if 'sampler' in png_metadata:
            params['sampler'] = png_metadata['sampler']

    json_config["parameters"] = params

    # Output section
    json_config["output"] = {
        "session_name": f"regenerate_{session_config.get('session_name', 'session')}",
        "filename_keys": placeholders if placeholders else []
    }

    # Determine output path
    if output_path is None:
        session_name = session_config.get('session_name', session_dir.name)
        output_path = Path("configs") / f"regenerate_{session_name}.json"

    # Write or display
    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN - Config that would be generated:")
        print("=" * 60)
        print(json.dumps(json_config, indent=2))
        print("\n" + "=" * 60)
        print(f"Would save to: {output_path}")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_config, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"\n✅ Config saved to: {output_path}")

    return json_config


def process_all_sessions(apioutput_dir: Path, dry_run: bool = False,
                         inline_variations: bool = False) -> tuple[int, int, int]:
    """
    Process all sessions in apioutput directory.

    Args:
        apioutput_dir: Path to apioutput directory
        dry_run: Preview without writing
        inline_variations: Use inline variations

    Returns:
        Tuple of (success_count, skipped_count, error_count)
    """
    # Find all session directories (with session_config.txt)
    sessions = []
    for item in apioutput_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            if (item / "session_config.txt").exists():
                sessions.append(item)

    if not sessions:
        print(f"⚠️  No sessions with session_config.txt found in {apioutput_dir}")
        return 0, 0, 0

    sessions.sort()  # Process in order

    print(f"\n🔍 Found {len(sessions)} session(s) to process\n")

    success_count = 0
    skipped_count = 0
    error_count = 0

    for i, session_dir in enumerate(sessions, 1):
        print(f"[{i}/{len(sessions)}] Processing {session_dir.name}...")

        # Check if config already exists
        session_name = None
        try:
            config_txt = session_dir / "session_config.txt"
            temp_config = parse_session_config(config_txt)
            session_name = session_dir.name
        except:
            session_name = session_dir.name

        output_path = Path("configs") / f"regenerate_{session_name}.json"

        if output_path.exists() and not dry_run:
            print(f"  ⏭️  Skipped (config already exists: {output_path})")
            skipped_count += 1
            continue

        try:
            generate_json_config(
                session_dir=session_dir,
                output_path=output_path,
                inline_variations=inline_variations,
                dry_run=dry_run
            )
            success_count += 1
            print()  # Blank line between sessions

        except Exception as e:
            print(f"  ❌ Error: {e}")
            error_count += 1
            print()

    return success_count, skipped_count, error_count


def main():
    parser = argparse.ArgumentParser(
        description="Generate JSON config from existing session(s)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate config from single session
  %(prog)s --session apioutput/20250101_120000_mysession

  # Process all sessions in apioutput directory
  %(prog)s --all

  # Preview all without writing
  %(prog)s --all --dry-run

  # Process all with custom apioutput directory
  %(prog)s --all --apioutput-dir CLI/apioutput

  # Preview single session without writing
  %(prog)s --session apioutput/20250101_120000_mysession --dry-run

  # Custom output path
  %(prog)s --session apioutput/20250101_120000_mysession --output configs/my_config.json

  # Use inline variations (no file paths)
  %(prog)s --session apioutput/20250101_120000_mysession --inline
        """
    )

    parser.add_argument(
        '--session',
        type=Path,
        help='Path to single session directory'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all sessions in apioutput directory'
    )

    parser.add_argument(
        '--apioutput-dir',
        type=Path,
        default=Path('apioutput'),
        help='Path to apioutput directory (default: apioutput/)'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output config file path (default: configs/regenerate_<session>.json)'
    )

    parser.add_argument(
        '--inline',
        action='store_true',
        help='Use inline variations instead of file paths'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview config without writing file'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.session and not args.all:
        parser.error("Either --session or --all is required")

    if args.session and args.all:
        parser.error("Cannot use both --session and --all")

    try:
        if args.all:
            # Process all sessions
            if not args.apioutput_dir.exists():
                print(f"❌ Error: apioutput directory not found: {args.apioutput_dir}")
                return 1

            success, skipped, errors = process_all_sessions(
                apioutput_dir=args.apioutput_dir,
                dry_run=args.dry_run,
                inline_variations=args.inline
            )

            # Summary
            print("\n" + "=" * 60)
            print("Batch Processing Summary")
            print("=" * 60)
            print(f"✅ Success: {success}")
            print(f"⏭️  Skipped: {skipped}")
            print(f"❌ Errors:  {errors}")
            print("=" * 60)

            if not args.dry_run and success > 0:
                print("\n⚠️  Remember to:")
                print("  1. Update variation file paths in generated configs")
                print("  2. Verify generation modes and seed modes")
                print("  3. Test configs: python3 CLI/generator_cli.py --list")

            return 0 if errors == 0 else 1

        else:
            # Process single session
            if not args.session.exists():
                print(f"❌ Error: Session directory not found: {args.session}")
                return 1

            if not args.session.is_dir():
                print(f"❌ Error: Not a directory: {args.session}")
                return 1

            config = generate_json_config(
                session_dir=args.session,
                output_path=args.output,
                inline_variations=args.inline,
                dry_run=args.dry_run
            )

            if not args.dry_run:
                print("\n⚠️  Remember to:")
                print("  1. Update variation file paths if needed")
                print("  2. Verify generation mode and seed mode")
                print("  3. Test the config: python3 CLI/generator_cli.py --config <path>")

            return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
