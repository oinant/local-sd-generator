#!/usr/bin/env python3
"""
SD Image Generator - YAML Template CLI (Phase 2)

Command-line interface for Phase 2 YAML template-driven image generation.
Supports interactive template selection and direct execution.

Usage:
    python3 template_cli.py                        # Interactive mode
    python3 template_cli.py --template path.yaml   # Direct template
    python3 template_cli.py --list                 # List templates
    python3 template_cli.py --help                 # Show help
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add CLI directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.global_config import load_global_config, ensure_global_config
from templating import load_prompt_config, resolve_prompt


def check_tty() -> bool:
    """Check if running in a TTY (interactive terminal)."""
    return sys.stdin.isatty()


def find_yaml_templates(configs_dir: Path) -> list[Path]:
    """
    Find all .prompt.yaml template files in configs directory.

    Args:
        configs_dir: Directory to search

    Returns:
        List of paths to .prompt.yaml files
    """
    templates = []

    # Search recursively for .prompt.yaml files
    for yaml_file in configs_dir.rglob("*.prompt.yaml"):
        templates.append(yaml_file)

    # Sort by name for consistent display
    templates.sort(key=lambda p: p.name)

    return templates


def list_yaml_templates(configs_dir: Path):
    """Display list of available YAML templates."""
    templates = find_yaml_templates(configs_dir)

    if not templates:
        print(f"No .prompt.yaml templates found in {configs_dir}")
        return

    print(f"\n{'='*80}")
    print(f"Available YAML Templates ({len(templates)} found)")
    print(f"{'='*80}\n")

    for idx, template_path in enumerate(templates, 1):
        # Try to load name from YAML
        try:
            config = load_prompt_config(template_path)
            name = config.name
            rel_path = template_path.relative_to(configs_dir)
        except Exception as e:
            name = f"[Error: {e}]"
            rel_path = template_path

        print(f"{idx:3d}. {name}")
        print(f"     {rel_path}\n")


def select_template_interactive(configs_dir: Path) -> Path:
    """
    Interactive template selection.

    Args:
        configs_dir: Directory containing templates

    Returns:
        Path to selected template

    Raises:
        ValueError: If no templates found or invalid selection
    """
    templates = find_yaml_templates(configs_dir)

    if not templates:
        raise ValueError(f"No .prompt.yaml templates found in {configs_dir}")

    print(f"\n{'='*80}")
    print(f"Select YAML Template ({len(templates)} available)")
    print(f"{'='*80}\n")

    for idx, template_path in enumerate(templates, 1):
        try:
            config = load_prompt_config(template_path)
            name = config.name
            rel_path = template_path.relative_to(configs_dir)
        except Exception:
            name = template_path.stem
            rel_path = template_path

        print(f"{idx:3d}. {name}")
        print(f"     {rel_path}\n")

    while True:
        try:
            choice = input(f"\nSelect template (1-{len(templates)}): ").strip()

            if not choice:
                raise ValueError("No selection made")

            idx = int(choice) - 1

            if 0 <= idx < len(templates):
                return templates[idx]
            else:
                print(f"Invalid selection. Please enter 1-{len(templates)}")

        except ValueError as e:
            if "invalid literal" in str(e):
                print("Invalid input. Please enter a number.")
            else:
                raise
        except KeyboardInterrupt:
            print("\n\nSelection cancelled")
            raise ValueError("User cancelled selection")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="SD Image Generator - YAML Template Mode (Phase 2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive template selection
  %(prog)s --template portrait.prompt.yaml   # Run specific template
  %(prog)s --list                            # List available templates
  %(prog)s --template test.yaml --count 10   # Generate 10 variations
  %(prog)s --template test.yaml --dry-run    # Generate JSON only (no API calls)

Phase 2 templates use .prompt.yaml format with advanced features:
  - Multi-field variations
  - Chunk templates
  - Flexible selectors

For more information, see:
  docs/cli/usage/yaml-template-system.md
        """
    )

    parser.add_argument(
        '--template',
        type=Path,
        help='Direct path to .prompt.yaml template file'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List available YAML templates and exit'
    )

    parser.add_argument(
        '--count',
        type=int,
        help='Maximum number of variations to generate (overrides template config)'
    )

    parser.add_argument(
        '--init-config',
        action='store_true',
        help='Initialize global configuration file'
    )

    parser.add_argument(
        '--api-url',
        type=str,
        help='Override Stable Diffusion API URL (default from global config)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry-run mode: save API requests as JSON files instead of generating images'
    )

    return parser.parse_args()


def main():
    """Main CLI entry point"""
    args = parse_arguments()

    try:
        # Initialize global config if requested
        if args.init_config:
            print("Initializing global configuration...")
            config = ensure_global_config(interactive=True, force_create=True)
            print("\n✓ Global configuration initialized")
            return 0

        # Load global configuration
        try:
            global_config = load_global_config()
        except Exception as e:
            print(f"✗ Error loading global config: {e}")
            print("\nRun with --init-config to create global configuration.")
            return 1

        configs_dir = Path(global_config.configs_dir)
        api_url = args.api_url or global_config.api_url

        # Verify configs directory exists
        if not configs_dir.exists():
            print(f"✗ Configs directory not found: {configs_dir}")
            print("\nCreate the directory or update your .sdgen_config.json")
            return 1

        # List mode
        if args.list:
            list_yaml_templates(configs_dir)
            return 0

        # Determine template path
        if args.template:
            # Direct template path provided
            template_path = args.template

            # If relative path, try resolving relative to configs_dir first
            if not template_path.is_absolute():
                # Try relative to configs_dir
                configs_dir_path = configs_dir / template_path
                if configs_dir_path.exists():
                    template_path = configs_dir_path
                else:
                    # Try relative to current directory
                    template_path = Path.cwd() / template_path

            if not template_path.exists():
                print(f"✗ Template file not found: {template_path}")
                return 1

        else:
            # Interactive selection
            if not check_tty():
                print("✗ Interactive mode requires a TTY (terminal)")
                print("\nUse --template to specify template directly for non-interactive use.")
                return 1

            try:
                template_path = select_template_interactive(configs_dir)
            except ValueError as e:
                print(f"\n✗ {e}")
                return 1
            except Exception as e:
                print(f"\n✗ Error selecting template: {e}")
                return 1

        print(f"\n{'='*80}")
        print(f"Processing Template: {template_path.name}")
        print(f"{'='*80}\n")

        # Load template config
        config = load_prompt_config(template_path)

        # Override max_images if specified
        if args.count is not None:
            config.max_images = args.count

        # Resolve variations
        base_path = template_path.parent
        print(f"Resolving template: {config.name}")
        print(f"Base path: {base_path}")

        variations = resolve_prompt(config, base_path=base_path)
        print(f"Generated {len(variations)} variations\n")

        # Generate using the new API module
        from api import BatchGenerator, SDAPIClient, SessionManager, ImageWriter, ProgressReporter
        from api.sdapi_client import GenerationConfig, PromptConfig

        session_name = config.name.lower().replace(" ", "_").replace("-", "_")
        output_base_dir = Path(global_config.output_dir)

        # Initialize components
        api_client = SDAPIClient(api_url=api_url)
        session_manager = SessionManager(
            base_output_dir=str(output_base_dir),
            session_name=session_name,
            dry_run=args.dry_run
        )
        image_writer = ImageWriter(session_manager.output_dir)
        progress = ProgressReporter(
            total_images=len(variations),
            output_dir=session_manager.output_dir,
            verbose=True
        )

        # Create batch generator
        generator = BatchGenerator(
            api_client=api_client,
            session_manager=session_manager,
            image_writer=image_writer,
            progress_reporter=progress,
            dry_run=args.dry_run
        )

        session_dir = Path(session_manager.output_dir)

        print(f"{'='*80}")
        print("Starting Image Generation")
        print(f"{'='*80}\n")
        print(f"Output directory: {session_dir}\n")

        # Create output directory
        session_manager.create_session_dir()

        # Save JSON manifest with variations
        manifest_path = session_dir / f"{session_name}_manifest.json"
        manifest = {
            "session_name": session_name,
            "template_source": str(template_path),
            "generated_at": datetime.now().isoformat(),
            "total_variations": len(variations),
            "templating_system": "phase2",
            "variations": []
        }

        for var in variations:
            manifest["variations"].append({
                "index": var.index,
                "prompt": var.final_prompt,
                "negative_prompt": var.negative_prompt,
                "seed": var.seed,
                "placeholders": var.placeholders
            })

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        print(f"✓ Manifest saved: {manifest_path}\n")

        # Test connection if not in dry-run mode
        if not args.dry_run:
            print(f"Connecting to SD API: {api_url}")
            if not api_client.test_connection():
                print("✗ Failed to connect to SD API")
                print("   Make sure Stable Diffusion WebUI is running")
                return 1
            print("✓ Connected to SD API\n")

        # Configure generation parameters from YAML config
        gen_config = GenerationConfig(
            width=config.width,
            height=config.height,
            steps=config.steps,
            cfg_scale=config.cfg_scale,
            sampler_name=config.sampler,
            batch_size=config.batch_size,
            n_iter=config.batch_count,
            # Hires Fix parameters
            enable_hr=config.enable_hr,
            hr_scale=config.hr_scale,
            hr_upscaler=config.hr_upscaler,
            denoising_strength=config.denoising_strength,
            hr_second_pass_steps=config.hr_second_pass_steps
        )
        api_client.generation_config = gen_config

        # Convert Phase 2 variations to PromptConfig list
        prompt_configs = []
        for idx, var in enumerate(variations):
            prompt_cfg = PromptConfig(
                prompt=var.final_prompt,
                negative_prompt=var.negative_prompt,
                seed=var.seed,
                filename=f"{session_name}_{idx:04d}.png"
            )
            prompt_configs.append(prompt_cfg)

        # Generate images using BatchGenerator
        try:
            success_count, total_count = generator.generate_batch(
                prompt_configs=prompt_configs,
                delay_between_images=2.0
            )

            fail_count = total_count - success_count

            # Display final summary
            print(f"\n{'='*80}")
            print("✓ Generation Complete")
            print(f"{'='*80}\n")
            print(f"Total images: {total_count}")
            print(f"Success: {success_count}")
            print(f"Failed: {fail_count}")

            if args.dry_run:
                print("\nDry-run mode: API requests saved to:")
                print(f"  {session_dir}")
            else:
                print("\nImages saved to:")
                print(f"  {session_dir}")

            return 0

        except Exception as e:
            print(f"\n✗ Error during generation: {e}")
            import traceback
            traceback.print_exc()
            return 1

    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        return 130

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
