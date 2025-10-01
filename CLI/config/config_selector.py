"""
Configuration Selector for JSON Config System (SF-2)

Provides interactive config selection from a directory.
"""

import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ConfigInfo:
    """Information about a configuration file"""
    path: Path
    name: str
    description: str
    filename: str

    @property
    def display_name(self) -> str:
        """Get display name (use name if available, else filename)"""
        return self.name if self.name else self.filename


def discover_configs(configs_dir: Path) -> List[ConfigInfo]:
    """
    Discover all JSON config files in directory.

    Args:
        configs_dir: Directory to search for configs

    Returns:
        List of ConfigInfo objects sorted by filename

    Raises:
        FileNotFoundError: If configs_dir doesn't exist
        NotADirectoryError: If configs_dir is not a directory
    """
    if not configs_dir.exists():
        raise FileNotFoundError(f"Configs directory not found: {configs_dir}")

    if not configs_dir.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {configs_dir}")

    configs = []

    # Find all .json files
    for json_file in configs_dir.glob("*.json"):
        if not json_file.is_file():
            continue

        # Try to extract metadata (name, description)
        name = ""
        description = ""

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                name = data.get("name", "")
                description = data.get("description", "")
        except (json.JSONDecodeError, Exception):
            # If we can't parse, just use filename
            pass

        configs.append(ConfigInfo(
            path=json_file,
            name=name,
            description=description,
            filename=json_file.name
        ))

    # Sort by filename for consistent ordering
    configs.sort(key=lambda c: c.filename)

    return configs


def display_config_list(configs: List[ConfigInfo]) -> None:
    """
    Display list of configs for user selection.

    Args:
        configs: List of ConfigInfo to display
    """
    if not configs:
        print("No configuration files found.")
        return

    print("\nAvailable configurations:\n")

    for i, config in enumerate(configs, start=1):
        # Display number and filename
        print(f"  {i}. {config.filename}")

        # Display name if different from filename
        if config.name and config.name != config.filename:
            print(f"     {config.name}")

        # Display description if available
        if config.description:
            # Indent description
            print(f"     {config.description}")

        print()  # Blank line between entries


def validate_config_selection(selection: str, max_num: int) -> int:
    """
    Validate user's config selection input.

    Args:
        selection: User input string
        max_num: Maximum valid number

    Returns:
        Selected index (0-based)

    Raises:
        ValueError: If selection is invalid
    """
    # Check if input is numeric
    try:
        num = int(selection)
    except ValueError:
        raise ValueError(f"Invalid selection: '{selection}'. Please enter a number.")

    # Check range
    if num < 1 or num > max_num:
        raise ValueError(f"Selection must be between 1 and {max_num}.")

    return num - 1  # Convert to 0-based index


def prompt_user_selection(configs: List[ConfigInfo]) -> Path:
    """
    Prompt user to select a configuration interactively.

    Args:
        configs: List of ConfigInfo to select from

    Returns:
        Path to selected config file

    Raises:
        ValueError: If no configs available or user cancels
        EOFError: If stdin is closed
    """
    if not configs:
        raise ValueError("No configurations available to select.")

    # Display list
    display_config_list(configs)

    # Prompt for selection
    max_num = len(configs)
    prompt = f"Select configuration (1-{max_num}): "

    while True:
        try:
            selection = input(prompt).strip()

            if not selection:
                raise ValueError("Selection cancelled by user.")

            # Validate
            index = validate_config_selection(selection, max_num)

            # Return selected path
            return configs[index].path

        except ValueError as e:
            print(f"Error: {e}")
            continue
        except (KeyboardInterrupt, EOFError):
            print("\nSelection cancelled.")
            raise ValueError("Selection cancelled by user.")


def select_config_interactive(configs_dir: Path) -> Path:
    """
    Complete interactive config selection flow.

    Args:
        configs_dir: Directory containing config files

    Returns:
        Path to selected config file

    Raises:
        ValueError: If no configs found or selection fails
    """
    # Discover configs
    configs = discover_configs(configs_dir)

    if not configs:
        raise ValueError(f"No configuration files found in: {configs_dir}")

    # Prompt user
    return prompt_user_selection(configs)


def list_available_configs(configs_dir: Path) -> None:
    """
    List all available configs (for --list option).

    Args:
        configs_dir: Directory containing config files
    """
    try:
        configs = discover_configs(configs_dir)

        if not configs:
            print(f"No configuration files found in: {configs_dir}")
            return

        print(f"\nConfiguration files in {configs_dir}:\n")

        for config in configs:
            print(f"  • {config.filename}")
            if config.name:
                print(f"    Name: {config.name}")
            if config.description:
                print(f"    Description: {config.description}")
            print(f"    Path: {config.path}")
            print()

    except Exception as e:
        print(f"Error listing configs: {e}")
