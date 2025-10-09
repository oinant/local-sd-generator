"""
YAML file loader for Template System V2.0.

This module handles loading and caching of YAML files with proper path resolution.
All paths are resolved relative to a base path for portability across systems.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class YamlLoader:
    """
    Loads YAML files with caching and relative path resolution.

    The loader maintains a cache of loaded files to avoid redundant I/O operations.
    All paths are resolved relative to a base path to ensure portability.

    Attributes:
        cache: Dictionary mapping absolute file paths to loaded YAML data
    """

    def __init__(self, cache: Optional[dict] = None):
        """
        Initialize the YAML loader.

        Args:
            cache: Optional existing cache dictionary. If None, creates a new cache.
        """
        self.cache = cache if cache is not None else {}

    def load_file(self, path: Path | str, base_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load a YAML file with caching.

        Args:
            path: Path to the YAML file (relative or absolute).
                  Absolute paths are allowed as entry points (e.g., loading the root config).
            base_path: Base directory for resolving relative paths.
                      If None, uses current working directory.

        Returns:
            Dictionary containing the parsed YAML data

        Raises:
            FileNotFoundError: If the file does not exist
            yaml.YAMLError: If the YAML is malformed
        """
        # Allow absolute paths for entry points (direct load_file calls)
        resolved_path = self.resolve_path(path, base_path, allow_absolute=True)

        # Check cache
        cache_key = str(resolved_path)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Check file exists
        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {resolved_path}")

        # Load and parse YAML
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML in {resolved_path}: {e}")

        # Cache the result
        self.cache[cache_key] = data
        return data

    def resolve_path(self, path: Path | str, base_path: Optional[Path] = None,
                     allow_absolute: bool = False) -> Path:
        """
        Resolve a path relative to a base path.

        This method ensures all paths are resolved consistently. By default,
        absolute paths are rejected for portability within YAML files
        (implements/imports), but can be allowed for entry points.

        Args:
            path: Path to resolve (string or Path object)
            base_path: Base directory for relative resolution.
                      If None and path is relative, uses current working directory.
            allow_absolute: If True, allows absolute paths. Use for entry points only.

        Returns:
            Absolute Path object resolved relative to base_path (or as-is if absolute)

        Raises:
            ValueError: If path is absolute and allow_absolute is False
        """
        path = Path(path)

        # If absolute path
        if path.is_absolute():
            if not allow_absolute:
                raise ValueError(
                    f"Absolute paths are not supported for portability: {path}. "
                    f"Please use relative paths instead."
                )
            # Allow absolute paths for entry points (direct load_file calls)
            return path.resolve()

        # Relative path resolution
        # Use current directory if no base_path provided
        if base_path is None:
            base_path = Path.cwd()

        # Resolve relative to base_path
        resolved = (base_path / path).resolve()
        return resolved

    def clear_cache(self):
        """Clear the internal cache of loaded files."""
        self.cache.clear()

    def invalidate(self, path: Path | str):
        """
        Invalidate a specific file in the cache.

        Args:
            path: Absolute path to the file to invalidate
        """
        cache_key = str(Path(path).resolve())
        if cache_key in self.cache:
            del self.cache[cache_key]
