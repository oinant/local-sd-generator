#!/usr/bin/env python3
"""
SD Image Generator - JSON Config CLI

Main command-line interface for JSON-driven image generation.
Supports interactive config selection and direct config path execution.

Usage:
    python3 generator_cli.py                    # Interactive mode
    python3 generator_cli.py --config path.json # Direct config
    python3 generator_cli.py --list             # List configs
    python3 generator_cli.py --help             # Show help
"""

import argparse
import sys
from pathlib import Path

# Add CLI directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.global_config import load_global_config, ensure_global_config
from config.config_selector import select_config_interactive, list_available_configs
from execution.json_generator import run_generation_from_config


def check_tty() -> bool:
    """
    Check if running in a TTY (interactive terminal).

    Returns:
        True if TTY available, False otherwise
    """
    return sys.stdin.isatty()


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="SD Image Generator - JSON Config Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Interactive config selection
  %(prog)s --config anime.json          # Run specific config
  %(prog)s --list                       # List available configs
  %(prog)s --config configs/test.json   # Run config with path

For more information, see documentation at:
  docs/cli/usage/json-config-system.md
        """
    )

    parser.add_argument(
        '--config',
        type=Path,
        help='Direct path to JSON config file'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List available configurations and exit'
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
            print(f"\nCreate the directory or update your .sdgen_config.json")
            return 1

        # List mode
        if args.list:
            list_available_configs(configs_dir)
            return 0

        # Determine config path
        if args.config:
            # Direct config path provided
            config_path = args.config

            # If relative path, try resolving relative to configs_dir first
            if not config_path.is_absolute():
                # Try relative to configs_dir
                configs_dir_path = configs_dir / config_path
                if configs_dir_path.exists():
                    config_path = configs_dir_path
                else:
                    # Try relative to current directory
                    config_path = Path.cwd() / config_path

            if not config_path.exists():
                print(f"✗ Config file not found: {config_path}")
                return 1

        else:
            # Interactive selection
            if not check_tty():
                print("✗ Interactive mode requires a TTY (terminal)")
                print("\nUse --config to specify config directly for non-interactive use.")
                return 1

            try:
                config_path = select_config_interactive(configs_dir)
            except ValueError as e:
                print(f"\n✗ {e}")
                return 1
            except Exception as e:
                print(f"\n✗ Error selecting config: {e}")
                return 1

        # Run generation
        try:
            result = run_generation_from_config(
                config_path=config_path,
                api_url=api_url
            )

            # Display final summary
            print("\n" + "=" * 60)
            print("✓ Generation Session Complete")
            print("=" * 60)
            print(f"Config: {result['config_name']}")
            print(f"Session: {result['session_name']}")
            print(f"Success: {result['success_count']}/{result['total_count']} images")
            print("=" * 60)

            return 0 if result['success_count'] > 0 else 1

        except KeyboardInterrupt:
            print("\n\n✗ Generation interrupted by user")
            return 130  # Standard exit code for SIGINT

        except Exception as e:
            print(f"\n✗ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return 1

    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
        return 130

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
