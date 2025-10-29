"""
Theme discovery and loading for Themable Templates feature.

This module handles:
- Discovery of themes in configs_dir/themes/
- Loading explicit themes (with theme.yaml)
- Inferring implicit themes (from {theme}_*.yaml files)
- Rating suffix extraction and validation
"""

from pathlib import Path
from typing import List, Dict, Optional
import yaml

from sd_generator_cli.templating.models import ThemeConfig


class ThemeLoader:
    """Loader for theme discovery and configuration."""

    def __init__(self, configs_dir: Path):
        """
        Initialize theme loader.

        Args:
            configs_dir: Base directory containing themes/ subdirectory
        """
        self.configs_dir = Path(configs_dir)
        self.themes_dir = self.configs_dir / "themes"

    def discover_available_themes(
        self,
        template_source_file: Path,
        themes_config: 'ThemeConfigBlock'
    ) -> Dict[str, str]:
        """
        Discover all available themes for a template using ThemeConfigBlock.

        Combines explicit themes and autodiscovered themes based on configuration.

        Args:
            template_source_file: Path to the template file (for relative path resolution)
            themes_config: ThemeConfigBlock from template

        Returns:
            Dict mapping theme names to their theme.yaml file paths

        Example:
            >>> from sd_generator_cli.templating.models import ThemeConfigBlock
            >>> themes_cfg = ThemeConfigBlock(
            ...     enable_autodiscovery=True,
            ...     search_paths=['./'],
            ...     explicit={'custom': '../custom/theme.yaml'}
            ... )
            >>> loader.discover_available_themes(Path('template.yaml'), themes_cfg)
            {'custom': '../custom/theme.yaml', 'pirates': './pirates/theme.yaml', 'cyberpunk': './cyberpunk/theme.yaml'}
        """
        available: Dict[str, str] = {}
        template_dir = template_source_file.parent

        # 1. Add explicit themes first (highest priority)
        if themes_config.explicit:
            for name, path in themes_config.explicit.items():
                # Resolve relative paths
                if not Path(path).is_absolute():
                    resolved = (template_dir / path).resolve()
                    available[name] = str(resolved)
                else:
                    available[name] = path

        # 2. Add autodiscovered themes if enabled
        if themes_config.enable_autodiscovery:
            search_paths = themes_config.search_paths if themes_config.search_paths else ['.']

            for search_path_str in search_paths:
                # Resolve relative to template file
                if not Path(search_path_str).is_absolute():
                    search_path = (template_dir / search_path_str).resolve()
                else:
                    search_path = Path(search_path_str)

                if not search_path.exists() or not search_path.is_dir():
                    continue

                # Scan for theme.yaml files
                discovered = self._scan_directory_for_themes(search_path)

                # Add discovered themes (explicit themes have priority)
                for name, path in discovered.items():
                    if name not in available:
                        available[name] = path

        return available

    def _scan_directory_for_themes(self, directory: Path) -> Dict[str, str]:
        """
        Scan a directory for theme.yaml files.

        Looks for immediate subdirectories containing theme.yaml.

        Args:
            directory: Directory to scan

        Returns:
            Dict mapping theme names to theme.yaml file paths

        Example:
            Directory structure:
                ./
                ├── pirates/
                │   └── theme.yaml
                ├── cyberpunk/
                │   └── theme.yaml
                └── rockstar/
                    └── theme.yaml

            Returns:
                {'pirates': './pirates/theme.yaml', 'cyberpunk': './cyberpunk/theme.yaml', 'rockstar': './rockstar/theme.yaml'}
        """
        discovered: Dict[str, str] = {}

        try:
            for item in directory.iterdir():
                if not item.is_dir():
                    continue

                theme_file = item / "theme.yaml"
                if theme_file.exists():
                    theme_name = item.name
                    discovered[theme_name] = str(theme_file)

        except (OSError, PermissionError):
            # Silently skip directories we can't read
            pass

        return discovered

    def discover_themes(self) -> List[ThemeConfig]:
        """
        Discover all available themes in themes/ directory.

        Searches for:
        - Explicit themes (directories with theme.yaml)
        - Implicit themes (inferred from {theme}_*.yaml files)

        Returns:
            List of ThemeConfig objects

        Example:
            >>> loader = ThemeLoader(Path("/configs"))
            >>> themes = loader.discover_themes()
            >>> [t.name for t in themes]
            ['cyberpunk', 'rockstar', 'pirates']
        """
        if not self.themes_dir.exists():
            return []

        themes: List[ThemeConfig] = []

        # Find all subdirectories in themes/
        for theme_dir in self.themes_dir.iterdir():
            if not theme_dir.is_dir():
                continue

            theme_name = theme_dir.name
            theme_yaml = theme_dir / "theme.yaml"

            if theme_yaml.exists():
                # Explicit theme
                theme = self.load_explicit_theme(theme_dir, theme_name)
            else:
                # Implicit theme (infer from files)
                theme = self.load_implicit_theme(theme_dir, theme_name)

            if theme:
                themes.append(theme)

        return themes

    def load_theme(self, theme_name: str) -> Optional[ThemeConfig]:
        """
        Load a specific theme by name.

        Args:
            theme_name: Name of the theme (e.g., "cyberpunk")

        Returns:
            ThemeConfig or None if not found

        Example:
            >>> loader = ThemeLoader(Path("/configs"))
            >>> theme = loader.load_theme("cyberpunk")
            >>> theme.name
            'cyberpunk'
        """
        theme_dir = self.themes_dir / theme_name
        if not theme_dir.exists():
            return None

        theme_yaml = theme_dir / "theme.yaml"

        if theme_yaml.exists():
            return self.load_explicit_theme(theme_dir, theme_name)
        else:
            return self.load_implicit_theme(theme_dir, theme_name)

    def load_theme_from_file(self, theme_path: str) -> ThemeConfig:
        """
        Load a theme from a specific file path (for --theme-file option).

        Args:
            theme_path: Path to theme.yaml file (absolute or relative)

        Returns:
            ThemeConfig

        Raises:
            FileNotFoundError: If theme file doesn't exist
            ValueError: If theme file is invalid

        Example:
            >>> loader = ThemeLoader(Path("/configs"))
            >>> theme = loader.load_theme_from_file("./custom/my_theme.yaml")
            >>> theme.name
            'my_theme'
        """
        theme_file = Path(theme_path)
        if not theme_file.exists():
            raise FileNotFoundError(f"Theme file not found: {theme_path}")

        # Get theme directory and infer name from file
        theme_dir = theme_file.parent
        theme_name = theme_file.stem.replace("_theme", "").replace(".theme", "")

        return self.load_explicit_theme(theme_dir, theme_name)

    def load_explicit_theme(self, theme_dir: Path, theme_name: str) -> ThemeConfig:
        """
        Load an explicit theme from theme.yaml.

        Args:
            theme_dir: Path to theme directory
            theme_name: Theme name

        Returns:
            ThemeConfig with explicit imports

        Example theme.yaml:
            ```yaml
            type: theme_config
            version: "1.0"
            imports:
              Ambiance: cyberpunk/cyberpunk_ambiance.yaml
              Outfit.sfw: cyberpunk/cyberpunk_outfit.sfw.yaml
              Outfit.sexy: cyberpunk/cyberpunk_outfit.sexy.yaml
            ```
        """
        theme_yaml = theme_dir / "theme.yaml"

        with open(theme_yaml, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        imports = data.get('imports', {})

        # Extract variation categories (base placeholder names)
        variations = self._extract_variations_from_imports(imports)

        return ThemeConfig(
            name=theme_name,
            path=theme_dir,
            explicit=True,
            imports=imports,
            variations=variations
        )

    def load_implicit_theme(self, theme_dir: Path, theme_name: str) -> Optional[ThemeConfig]:
        """
        Infer theme from {theme}_*.yaml files.

        Scans directory for files matching pattern:
        - {theme}_ambiance.yaml → Ambiance
        - {theme}_outfit.sfw.yaml → Outfit.sfw
        - {theme}_locations.yaml → Locations

        Args:
            theme_dir: Path to theme directory
            theme_name: Theme name

        Returns:
            ThemeConfig with inferred imports, or None if no matching files

        Example:
            Directory: themes/rockstar/
            Files:
            - rockstar_ambiance.yaml
            - rockstar_outfit.sfw.yaml
            - rockstar_outfit.sexy.yaml

            Result:
            imports = {
                "Ambiance": "rockstar/rockstar_ambiance.yaml",
                "Outfit.sfw": "rockstar/rockstar_outfit.sfw.yaml",
                "Outfit.sexy": "rockstar/rockstar_outfit.sexy.yaml"
            }
        """
        prefix = f"{theme_name}_"
        imports: Dict[str, str] = {}

        # Scan for {theme}_*.yaml files
        for yaml_file in theme_dir.glob(f"{prefix}*.yaml"):
            # Extract placeholder name from filename
            # Example: "rockstar_outfit.sfw.yaml" → "outfit.sfw"
            relative_name = yaml_file.stem[len(prefix):]  # "outfit.sfw"

            # Convert to PascalCase placeholder
            # "outfit.sfw" → "Outfit.sfw"
            # "cyberpunk_ambiance" → "Ambiance"
            placeholder = self._filename_to_placeholder(relative_name)

            # Store relative path from configs_dir
            relative_path = f"{theme_name}/{yaml_file.name}"
            imports[placeholder] = relative_path

        if not imports:
            return None

        variations = self._extract_variations_from_imports(imports)

        return ThemeConfig(
            name=theme_name,
            path=theme_dir,
            explicit=False,
            imports=imports,
            variations=variations
        )

    def _filename_to_placeholder(self, filename: str) -> str:
        """
        Convert filename to placeholder name.

        Handles:
        - Basic: "ambiance" → "Ambiance"
        - Rating suffix: "outfit.sfw" → "Outfit.sfw"
        - Multi-word: "hair_color" → "HairColor"

        Args:
            filename: Filename without theme prefix (e.g., "outfit.sfw")

        Returns:
            PascalCase placeholder name

        Examples:
            >>> _filename_to_placeholder("ambiance")
            'Ambiance'
            >>> _filename_to_placeholder("outfit.sfw")
            'Outfit.sfw'
            >>> _filename_to_placeholder("hair_color.sexy")
            'HairColor.sexy'
        """
        # Split on dot to separate base from rating suffix
        parts = filename.split('.')
        base = parts[0]
        suffix = '.' + '.'.join(parts[1:]) if len(parts) > 1 else ''

        # Convert base to PascalCase
        # "hair_color" → "HairColor"
        words = base.split('_')
        pascal_base = ''.join(word.capitalize() for word in words)

        return pascal_base + suffix

    def _extract_variations_from_imports(self, imports: Dict[str, str]) -> List[str]:
        """
        Extract base variation categories from import keys.

        Strips rating suffixes to get unique placeholder names.

        Args:
            imports: Dict of import mappings (may include rating suffixes)

        Returns:
            List of unique base placeholder names

        Example:
            >>> imports = {"Outfit.sfw": "...", "Outfit.sexy": "...", "Ambiance": "..."}
            >>> _extract_variations_from_imports(imports)
            ['Outfit', 'Ambiance']
        """
        variations = set()

        for key in imports.keys():
            # Strip rating suffix (e.g., "Outfit.sfw" → "Outfit")
            base = key.split('.')[0]
            variations.add(base)

        return sorted(variations)

    def get_theme_variants(self, theme_name: str, placeholder: str) -> List[str]:
        """
        Get all rating variants for a placeholder in a theme.

        Args:
            theme_name: Theme name
            placeholder: Base placeholder name (e.g., "Outfit")

        Returns:
            List of available ratings for this placeholder

        Example:
            >>> loader.get_theme_variants("cyberpunk", "Outfit")
            ['sfw', 'sexy', 'nsfw']
        """
        theme = self.load_theme(theme_name)
        if not theme:
            return []

        variants = []
        for key in theme.imports.keys():
            if key.startswith(f"{placeholder}."):
                # Extract rating suffix
                rating = key.split('.', 1)[1]
                variants.append(rating)

        return sorted(variants)
