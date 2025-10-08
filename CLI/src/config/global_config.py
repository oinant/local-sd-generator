"""
Global Configuration System for SD Generator

Manages .sdgen_config.json for project-level and user-level configuration.
Supports configs_dir, output_dir, and api_url settings.

Search order: Project root → User home → Defaults
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class GlobalConfig:
    """Global configuration settings"""
    configs_dir: str = "./configs"
    output_dir: str = "./apioutput"
    api_url: str = "http://127.0.0.1:7860"

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'GlobalConfig':
        """Create from dictionary"""
        return cls(
            configs_dir=data.get("configs_dir", cls.configs_dir),
            output_dir=data.get("output_dir", cls.output_dir),
            api_url=data.get("api_url", cls.api_url)
        )


def locate_global_config() -> Optional[Path]:
    """
    Locate global config file.

    Search order:
    1. Project root: .sdgen_config.json
    2. User home: ~/.sdgen_config.json

    Returns:
        Path to config file if found, None otherwise
    """
    # Search in project root (current working directory)
    project_config = Path.cwd() / ".sdgen_config.json"
    if project_config.exists():
        return project_config

    # Search in user home directory
    home_config = Path.home() / ".sdgen_config.json"
    if home_config.exists():
        return home_config

    return None


def load_global_config() -> GlobalConfig:
    """
    Load global configuration.

    Attempts to locate and load config file.
    Returns defaults if not found.

    Returns:
        GlobalConfig instance

    Raises:
        ValueError: If config file exists but is invalid JSON
    """
    config_path = locate_global_config()

    if config_path is None:
        # Return defaults
        return GlobalConfig()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return GlobalConfig.from_dict(data)

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_path}: {e}")
    except Exception as e:
        raise ValueError(f"Error reading config file {config_path}: {e}")


def create_default_global_config(path: Path, config: Optional[GlobalConfig] = None) -> None:
    """
    Create a default global config file.

    Args:
        path: Path where to create the config file
        config: GlobalConfig instance to save (uses defaults if None)

    Raises:
        ValueError: If unable to create config file
    """
    if config is None:
        config = GlobalConfig()

    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write config with pretty printing
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline

    except Exception as e:
        raise ValueError(f"Error creating config file {path}: {e}")


def prompt_user_for_paths(interactive: bool = True) -> tuple[str, str, str]:
    """
    Prompt user for configuration paths.

    Args:
        interactive: If True, prompt user for input. If False, use defaults.

    Returns:
        Tuple of (configs_dir, output_dir, api_url)
    """
    if not interactive:
        return GlobalConfig.configs_dir, GlobalConfig.output_dir, GlobalConfig.api_url

    print("\n=== SD Generator Global Configuration ===")
    print("\nPress Enter to use default values.")

    # Configs directory
    configs_dir = input(f"Configs directory [{GlobalConfig.configs_dir}]: ").strip()
    if not configs_dir:
        configs_dir = GlobalConfig.configs_dir

    # Output directory
    output_dir = input(f"Output directory [{GlobalConfig.output_dir}]: ").strip()
    if not output_dir:
        output_dir = GlobalConfig.output_dir

    # API URL
    api_url = input(f"API URL [{GlobalConfig.api_url}]: ").strip()
    if not api_url:
        api_url = GlobalConfig.api_url

    return configs_dir, output_dir, api_url


def ensure_global_config(interactive: bool = True, force_create: bool = False) -> GlobalConfig:
    """
    Ensure global config exists, creating it if necessary.

    Args:
        interactive: If True, prompt user for values when creating
        force_create: If True, create even if it exists (for reset)

    Returns:
        GlobalConfig instance
    """
    config_path = locate_global_config()

    # If config exists and we're not forcing recreation, load it
    if config_path is not None and not force_create:
        return load_global_config()

    # Decide where to create the config
    if config_path is None:
        # Default to project root
        config_path = Path.cwd() / ".sdgen_config.json"

    # Get configuration values
    if interactive:
        print(f"\nGlobal config not found. Creating at: {config_path}")
        configs_dir, output_dir, api_url = prompt_user_for_paths(interactive=True)
        config = GlobalConfig(
            configs_dir=configs_dir,
            output_dir=output_dir,
            api_url=api_url
        )
    else:
        config = GlobalConfig()

    # Create the config file
    create_default_global_config(config_path, config)

    if interactive:
        print(f"\n✓ Config created at: {config_path}")

    return config
