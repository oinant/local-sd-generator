"""
JSON-Driven Generation Executor (SF-3)

Executes generation from JSON config with interactive parameter resolution.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_schema import GenerationSessionConfig, ParametersConfig
from config.config_loader import load_config_from_file, validate_config
from config.global_config import load_global_config
from image_variation_generator import ImageVariationGenerator
from sdapi_client import GenerationConfig


# Available samplers (common defaults - can be queried from API)
DEFAULT_SAMPLERS = [
    "Euler a",
    "Euler",
    "LMS",
    "Heun",
    "DPM2",
    "DPM2 a",
    "DPM++ 2S a",
    "DPM++ 2M",
    "DPM++ SDE",
    "DPM++ 2M Karras",
    "DPM++ 2S a Karras",
    "DPM++ SDE Karras",
    "DPM fast",
    "DPM adaptive",
    "LMS Karras",
    "DDIM",
    "PLMS",
]


def prompt_generation_mode() -> str:
    """
    Prompt user to select generation mode.

    Returns:
        Selected mode: "combinatorial" or "random"
    """
    print("\nGeneration mode not specified in config.")
    print("Available modes:")
    print("  1. combinatorial - Generate all possible combinations")
    print("  2. random - Generate random unique combinations")
    print()

    while True:
        try:
            choice = input("Select mode (1-2): ").strip()

            if choice == "1":
                return "combinatorial"
            elif choice == "2":
                return "random"
            else:
                print("Invalid choice. Please enter 1 or 2.")

        except (KeyboardInterrupt, EOFError):
            print("\nSelection cancelled.")
            raise ValueError("User cancelled generation mode selection")


def prompt_seed_mode() -> str:
    """
    Prompt user to select seed mode.

    Returns:
        Selected seed mode: "fixed", "progressive", or "random"
    """
    print("\nSeed mode not specified in config.")
    print("Available modes:")
    print("  1. fixed - Same seed for all images")
    print("  2. progressive - Seeds increment (seed, seed+1, seed+2...)")
    print("  3. random - Random seed for each image")
    print()

    while True:
        try:
            choice = input("Select mode (1-3): ").strip()

            if choice == "1":
                return "fixed"
            elif choice == "2":
                return "progressive"
            elif choice == "3":
                return "random"
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

        except (KeyboardInterrupt, EOFError):
            print("\nSelection cancelled.")
            raise ValueError("User cancelled seed mode selection")


def prompt_max_images(total_combinations: int) -> int:
    """
    Prompt user for maximum number of images to generate.

    Args:
        total_combinations: Total possible combinations

    Returns:
        Number of images to generate
    """
    print(f"\nTotal possible combinations: {total_combinations}")
    print("How many images would you like to generate?")
    print(f"  • Enter a number (1-{total_combinations})")
    print(f"  • Press Enter to generate all {total_combinations}")
    print()

    while True:
        try:
            choice = input(f"Number of images (default: {total_combinations}): ").strip()

            if not choice:
                return total_combinations

            num = int(choice)

            if num < 1:
                print("Number must be at least 1.")
                continue

            if num > total_combinations:
                print(f"Warning: Requested {num} but only {total_combinations} combinations exist.")
                print(f"Using {total_combinations} instead.")
                return total_combinations

            return num

        except ValueError:
            print("Invalid input. Please enter a number.")
        except (KeyboardInterrupt, EOFError):
            print("\nSelection cancelled.")
            raise ValueError("User cancelled image count selection")


def prompt_sampler(available_samplers: Optional[List[str]] = None) -> str:
    """
    Prompt user to select sampler.

    Args:
        available_samplers: List of available samplers (uses defaults if None)

    Returns:
        Selected sampler name
    """
    samplers = available_samplers or DEFAULT_SAMPLERS

    print("\nSampler not specified in config.")
    print("Available samplers:")
    print()

    for i, sampler in enumerate(samplers, start=1):
        print(f"  {i}. {sampler}")

    print()

    while True:
        try:
            choice = input(f"Select sampler (1-{len(samplers)}): ").strip()

            try:
                num = int(choice)
                if 1 <= num <= len(samplers):
                    return samplers[num - 1]
                else:
                    print(f"Invalid choice. Please enter 1-{len(samplers)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        except (KeyboardInterrupt, EOFError):
            print("\nSelection cancelled.")
            raise ValueError("User cancelled sampler selection")


def prompt_numeric_param(param_name: str, default: Any, min_value: int = 1) -> int:
    """
    Prompt user for numeric parameter value.

    Args:
        param_name: Name of parameter (for display)
        default: Default value
        min_value: Minimum allowed value

    Returns:
        User-selected value
    """
    print(f"\n{param_name} not specified in config.")

    while True:
        try:
            choice = input(f"{param_name} (default: {default}): ").strip()

            if not choice:
                return default

            num = int(choice)

            if num < min_value:
                print(f"Value must be at least {min_value}.")
                continue

            return num

        except ValueError:
            print("Invalid input. Please enter a number.")
        except (KeyboardInterrupt, EOFError):
            print("\nSelection cancelled.")
            raise ValueError(f"User cancelled {param_name} selection")


def prompt_float_param(param_name: str, default: float, min_value: float = 0.1) -> float:
    """
    Prompt user for float parameter value.

    Args:
        param_name: Name of parameter (for display)
        default: Default value
        min_value: Minimum allowed value

    Returns:
        User-selected value
    """
    print(f"\n{param_name} not specified in config.")

    while True:
        try:
            choice = input(f"{param_name} (default: {default}): ").strip()

            if not choice:
                return default

            num = float(choice)

            if num < min_value:
                print(f"Value must be at least {min_value}.")
                continue

            return num

        except ValueError:
            print("Invalid input. Please enter a number.")
        except (KeyboardInterrupt, EOFError):
            print("\nSelection cancelled.")
            raise ValueError(f"User cancelled {param_name} selection")


def resolve_interactive_params(config: GenerationSessionConfig,
                                 available_samplers: Optional[List[str]] = None) -> GenerationSessionConfig:
    """
    Resolve interactive parameters ("ask" and -1 values).

    Creates a copy of config with resolved values.

    Args:
        config: Configuration with potentially interactive params
        available_samplers: List of available samplers (optional)

    Returns:
        New config with all interactive params resolved

    Raises:
        ValueError: If user cancels selection
    """
    # Create deep copy to avoid mutating original
    resolved = deepcopy(config)

    print("\n=== Resolving Interactive Parameters ===\n")

    # Generation mode
    if resolved.generation.mode == "ask":
        resolved.generation.mode = prompt_generation_mode()

    # Seed mode
    if resolved.generation.seed_mode == "ask":
        resolved.generation.seed_mode = prompt_seed_mode()

    # Seed (if -1, ask for value)
    if resolved.generation.seed == -1:
        resolved.generation.seed = prompt_numeric_param("Seed", default=42, min_value=0)

    # Max images will be resolved after we know total combinations
    # (handled separately in run_generation_from_config)

    # Parameters
    if resolved.parameters.width == -1:
        resolved.parameters.width = prompt_numeric_param("Width", default=512, min_value=64)

    if resolved.parameters.height == -1:
        resolved.parameters.height = prompt_numeric_param("Height", default=768, min_value=64)

    if resolved.parameters.steps == -1:
        resolved.parameters.steps = prompt_numeric_param("Steps", default=30, min_value=1)

    if resolved.parameters.cfg_scale == -1.0:
        resolved.parameters.cfg_scale = prompt_float_param("CFG Scale", default=7.0, min_value=0.1)

    if resolved.parameters.sampler == "ask":
        resolved.parameters.sampler = prompt_sampler(available_samplers)

    if resolved.parameters.batch_size == -1:
        resolved.parameters.batch_size = prompt_numeric_param("Batch size", default=1, min_value=1)

    if resolved.parameters.batch_count == -1:
        resolved.parameters.batch_count = prompt_numeric_param("Batch count", default=1, min_value=1)

    print("\n✓ All parameters resolved\n")

    return resolved


def create_generator_from_config(config: GenerationSessionConfig,
                                   api_url: str = "http://127.0.0.1:7860",
                                   base_output_dir: str = "apioutput",
                                   config_dir: Optional[Path] = None) -> ImageVariationGenerator:
    """
    Create ImageVariationGenerator from resolved config.

    Args:
        config: Fully resolved configuration
        api_url: Stable Diffusion API URL
        base_output_dir: Base output directory for images
        config_dir: Directory containing the config file (for resolving relative paths)

    Returns:
        Configured ImageVariationGenerator instance
    """
    # Resolve variation file paths relative to config directory
    variation_files = config.variations
    if config_dir:
        resolved_variations = {}
        for placeholder, path in variation_files.items():
            # Support both single path (string) and multiple paths (list)
            if isinstance(path, list):
                resolved_paths = []
                for p in path:
                    path_obj = Path(p)
                    if not path_obj.is_absolute():
                        resolved_paths.append(str((config_dir / p).resolve()))
                    else:
                        resolved_paths.append(p)
                resolved_variations[placeholder] = resolved_paths
            else:
                path_obj = Path(path)
                # If relative path, resolve relative to config directory
                if not path_obj.is_absolute():
                    resolved_path = (config_dir / path).resolve()
                    resolved_variations[placeholder] = str(resolved_path)
                else:
                    resolved_variations[placeholder] = path
        variation_files = resolved_variations

    # Create generator
    generator = ImageVariationGenerator(
        prompt_template=config.prompt.template,
        negative_prompt=config.prompt.negative,
        variation_files=variation_files,
        api_url=api_url,
        base_output_dir=base_output_dir,
        seed=config.generation.seed,
        max_images=config.generation.max_images,
        generation_mode=config.generation.mode,
        seed_mode=config.generation.seed_mode,
        session_name=config.output.session_name or "json_config_session",
        filename_keys=config.output.filename_keys
    )

    # Set generation parameters
    gen_config = GenerationConfig(
        steps=config.parameters.steps,
        cfg_scale=config.parameters.cfg_scale,
        width=config.parameters.width,
        height=config.parameters.height,
        sampler_name=config.parameters.sampler,
        batch_size=config.parameters.batch_size,
        n_iter=config.parameters.batch_count
    )

    generator.set_generation_config(gen_config)

    return generator


def run_generation_from_config(config_path: Path,
                                 api_url: str = None,
                                 base_output_dir: str = None,
                                 available_samplers: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Complete execution flow: load, validate, resolve, generate.

    Args:
        config_path: Path to JSON config file
        api_url: Stable Diffusion API URL (uses .sdgen_config.json if None)
        base_output_dir: Base output directory (uses .sdgen_config.json if None)
        available_samplers: List of available samplers (optional)

    Returns:
        Dictionary with generation results:
        {
            "success_count": int,
            "total_count": int,
            "session_name": str,
            "config_name": str
        }

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config invalid or user cancels
    """
    print(f"\n=== SD Image Generator - JSON Config Mode ===\n")

    # 0. Load global config for api_url and output_dir defaults
    global_config = load_global_config()
    if api_url is None:
        api_url = global_config.api_url
    if base_output_dir is None:
        base_output_dir = global_config.output_dir

    # 1. Load config
    print(f"Loading config: {config_path.name}...")
    try:
        config = load_config_from_file(config_path)
        print("✓ Config loaded successfully\n")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        raise

    # 2. Validate config
    print("Validating config...")
    validation = validate_config(config, available_samplers, config_dir=config_path.parent)

    if not validation.is_valid:
        print("✗ Config validation failed:\n")
        print(validation)
        raise ValueError("Configuration validation failed")

    if validation.warnings:
        print("⚠ Warnings:\n")
        for warning in validation.get_warning_messages():
            print(f"  {warning}")
        print()

    print("✓ Config validated\n")

    # 3. Resolve interactive parameters
    try:
        resolved_config = resolve_interactive_params(config, available_samplers)
    except ValueError as e:
        print(f"\n✗ Parameter resolution failed: {e}")
        raise

    # 4. Calculate total combinations for max_images prompt
    from variation_loader import load_variations_for_placeholders

    variations = load_variations_for_placeholders(
        resolved_config.prompt.template,
        resolved_config.variations,
        verbose=False,
        negative_prompt=resolved_config.prompt.negative
    )

    total_combinations = 1
    for placeholder_variations in variations.values():
        total_combinations *= len(placeholder_variations)

    # Resolve max_images if needed
    if resolved_config.generation.max_images == -1:
        resolved_config.generation.max_images = prompt_max_images(total_combinations)

    # 5. Create generator
    print("Creating generator...")
    generator = create_generator_from_config(
        resolved_config,
        api_url,
        base_output_dir,
        config_dir=config_path.parent  # Pass config directory for relative path resolution
    )
    print("✓ Generator created\n")

    # 6. Run generation
    print("Starting generation...\n")
    print("=" * 60)

    try:
        success_count, total_count = generator.run()
    except Exception as e:
        print(f"\n✗ Generation failed: {e}")
        raise

    print("=" * 60)

    # 7. Display results
    print("\n✓ Generation complete!")
    print(f"  Session: {generator.session_name}")
    print(f"  Images: {success_count}/{total_count} successful")

    if generator.start_time and generator.end_time:
        duration = generator.end_time - generator.start_time
        print(f"  Time: {duration}")

    return {
        "success_count": success_count,
        "total_count": total_count,
        "session_name": generator.session_name,
        "config_name": config.name or config_path.name
    }
