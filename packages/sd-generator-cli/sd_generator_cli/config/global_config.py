"""
Global Configuration System for SD Generator

Manages sdgen_config.json in the current working directory.
Supports configs_dir, output_dir, api_url, and webui_token settings.

Config location: ./sdgen_config.json (current directory only)
"""

import json
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class GlobalConfig:
    """Global configuration settings"""
    configs_dir: str = "./prompts"
    output_dir: str = "./results"
    api_url: str = "http://127.0.0.1:7860"
    webui_token: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'GlobalConfig':
        """Create from dictionary"""
        return cls(
            configs_dir=data.get("configs_dir", cls.configs_dir),
            output_dir=data.get("output_dir", cls.output_dir),
            api_url=data.get("api_url", cls.api_url),
            webui_token=data.get("webui_token")
        )


def locate_global_config() -> Optional[Path]:
    """
    Locate global config file in current directory only.

    Returns:
        Path to config file if found, None otherwise
    """
    config_path = Path.cwd() / "sdgen_config.json"
    return config_path if config_path.exists() else None


def load_global_config() -> GlobalConfig:
    """
    Load global configuration from current directory.

    Returns:
        GlobalConfig instance

    Raises:
        FileNotFoundError: If config file not found in current directory
        ValueError: If config file is invalid JSON
    """
    config_path = locate_global_config()

    if config_path is None:
        raise FileNotFoundError(
            "No config found. Run 'sdgen init' first."
        )

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


def generate_webui_token() -> str:
    """
    Generate a new UUID v4 token for WebUI authentication.

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def prompt_user_for_paths(interactive: bool = True) -> tuple[str, str, str, Optional[str]]:
    """
    Prompt user for configuration paths and WebUI token.

    Args:
        interactive: If True, prompt user for input. If False, use defaults.

    Returns:
        Tuple of (configs_dir, output_dir, api_url, webui_token)
    """
    if not interactive:
        return (
            GlobalConfig.configs_dir,
            GlobalConfig.output_dir,
            GlobalConfig.api_url,
            None
        )

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

    # WebUI Token (optional)
    print("\n--- WebUI Authentication (optional) ---")
    print("Generate a secure token for WebUI access?")
    print("(Useful if you plan to expose WebUI via tunneling)")
    generate_token = input("Generate token? [Y/n]: ").strip().lower()

    webui_token = None
    if generate_token != 'n':
        webui_token = generate_webui_token()
        print(f"\n✓ Generated token: {webui_token}")
        print("  Save this token to authenticate with the WebUI.")

    return configs_dir, output_dir, api_url, webui_token


def ensure_global_config(interactive: bool = True, force_create: bool = False) -> GlobalConfig:
    """
    Ensure global config exists in current directory, creating it if necessary.

    Args:
        interactive: If True, prompt user for values when creating
        force_create: If True, create even if it exists (overwrite)

    Returns:
        GlobalConfig instance
    """
    config_path = Path.cwd() / "sdgen_config.json"

    # If config exists and we're not forcing recreation, ask to overwrite
    if config_path.exists() and not force_create:
        if interactive:
            response = input(f"Config already exists at {config_path}. Overwrite? [y/N]: ").strip().lower()
            if response != 'y':
                print("Keeping existing config.")
                return load_global_config()
        else:
            return load_global_config()

    # Get configuration values
    if interactive:
        if not config_path.exists():
            print(f"\nCreating config at: {config_path}")
        configs_dir, output_dir, api_url, webui_token = prompt_user_for_paths(interactive=True)
        config = GlobalConfig(
            configs_dir=configs_dir,
            output_dir=output_dir,
            api_url=api_url,
            webui_token=webui_token
        )
    else:
        config = GlobalConfig()

    # Create the config file
    create_default_global_config(config_path, config)

    if interactive:
        print(f"\n✓ Config created at: {config_path}")

    return config
