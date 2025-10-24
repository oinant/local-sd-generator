"""
Style-based import resolution for Themable Templates.

This module handles resolution of style-sensitive imports by replacing
style suffixes in filenames (.cartoon.yaml → .realistic.yaml → .photorealistic.yaml).

Styles are freeform and user-defined - no hardcoded list.
Common examples: cartoon, manga, realistic, photorealistic, minimalist, watercolor, etc.
"""

from pathlib import Path
from typing import Optional, List


class StyleResolver:
    """Resolver for style-based file variants."""

    @staticmethod
    def replace_style_suffix(filepath: str, target_style: str, known_styles: Optional[List[str]] = None) -> str:
        """
        Replace style suffix in filepath.

        Handles:
        - .cartoon.yaml → .realistic.yaml
        - rendering.manga.yaml → rendering.photorealistic.yaml
        - No style → unchanged (caller handles adding style)

        Args:
            filepath: Original filepath (e.g., "common/outfit.cartoon.yaml")
            target_style: Target style (e.g., "realistic")
            known_styles: Optional list of known styles to detect (if None, no replacement)

        Returns:
            Filepath with replaced style suffix

        Examples:
            >>> StyleResolver.replace_style_suffix("outfit.cartoon.yaml", "realistic", ["cartoon"])
            'outfit.realistic.yaml'
            >>> StyleResolver.replace_style_suffix("rendering.manga.yaml", "photorealistic", ["manga"])
            'rendering.photorealistic.yaml'
            >>> StyleResolver.replace_style_suffix("ambiance.yaml", "realistic")
            'ambiance.yaml'  # No change if not style-sensitive
        """
        if not known_styles:
            return filepath

        path = Path(filepath)
        stem = path.stem
        suffix = path.suffix

        # Check if stem contains a style suffix
        parts = stem.split('.')

        # Find and replace style in parts
        new_parts = []
        style_found = False

        for part in parts:
            if part in known_styles:
                # Replace with target style
                new_parts.append(target_style)
                style_found = True
            else:
                new_parts.append(part)

        # If no style found, don't auto-add (caller handles fallback)
        new_stem = '.'.join(new_parts)

        # Reconstruct path
        return str(path.parent / f"{new_stem}{suffix}")

    @staticmethod
    def add_style_suffix(filepath: str, style: str) -> str:
        """
        Add style suffix to filepath (between stem and .yaml).

        Args:
            filepath: Original filepath (e.g., "common/outfit.yaml")
            style: Style to add (e.g., "cartoon")

        Returns:
            Filepath with style suffix added

        Example:
            >>> StyleResolver.add_style_suffix("outfit.yaml", "cartoon")
            'outfit.cartoon.yaml'
            >>> StyleResolver.add_style_suffix("common/rendering.base.yaml", "photorealistic")
            'common/rendering.base.photorealistic.yaml'
        """
        path = Path(filepath)
        stem = path.stem
        suffix = path.suffix

        new_filename = f"{stem}.{style}{suffix}"
        return str(path.parent / new_filename)

    @staticmethod
    def extract_style_from_path(filepath: str, known_styles: List[str]) -> Optional[str]:
        """
        Extract style suffix from filepath if present.

        Args:
            filepath: Filepath to analyze
            known_styles: List of known styles to detect

        Returns:
            Style string or None if no known style found

        Example:
            >>> StyleResolver.extract_style_from_path("outfit.cartoon.yaml", ["cartoon", "realistic"])
            'cartoon'
            >>> StyleResolver.extract_style_from_path("ambiance.yaml", ["cartoon"])
            None
        """
        path = Path(filepath)
        stem = path.stem
        parts = stem.split('.')

        for part in parts:
            if part in known_styles:
                return part

        return None

    @staticmethod
    def resolve_style_fallback(
        base_path: str,
        target_style: str,
        configs_dir: Path,
        known_styles: List[str],
        fallback_dirs: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Resolve import with style, trying multiple fallback strategies.

        Strategy:
        1. Try exact style match
        2. Try fallback directories (e.g., common/)
        3. Try without style (base file)

        Args:
            base_path: Base import path (e.g., "cyberpunk/outfit.cartoon.yaml")
            target_style: Desired style (e.g., "realistic")
            configs_dir: Base configs directory
            known_styles: List of known styles for detection
            fallback_dirs: List of fallback directories (e.g., ["common"])

        Returns:
            Resolved filepath or None if not found

        Example:
            >>> # Theme has outfit.cartoon, wants outfit.realistic
            >>> resolve_style_fallback(
            ...     "cyberpunk/outfit.cartoon.yaml",
            ...     "realistic",
            ...     Path("/configs"),
            ...     ["cartoon", "realistic"],
            ...     ["common"]
            ... )
            '/configs/common/outfit.realistic.yaml'  # Falls back to common
        """
        # Strategy 1: Try replacing style in original path
        with_style = StyleResolver.replace_style_suffix(base_path, target_style, known_styles)
        full_path = configs_dir / with_style
        if full_path.exists():
            return str(with_style)

        # Strategy 2: Try fallback directories
        if fallback_dirs:
            filename = Path(base_path).name
            filename_with_style = Path(
                StyleResolver.replace_style_suffix(filename, target_style, known_styles)
            ).name

            for fallback_dir in fallback_dirs:
                fallback_path = configs_dir / fallback_dir / filename_with_style
                if fallback_path.exists():
                    return str(Path(fallback_dir) / filename_with_style)

        # Strategy 3: Try base file without style (if different from original)
        base_file = Path(base_path)
        current_style = StyleResolver.extract_style_from_path(base_path, known_styles)

        if current_style:
            # Remove style suffix and try
            stem_parts = base_file.stem.split('.')
            stem_parts = [p for p in stem_parts if p not in known_styles]
            base_stem = '.'.join(stem_parts)
            base_filename = f"{base_stem}{base_file.suffix}"
            base_full_path = configs_dir / base_file.parent / base_filename

            if base_full_path.exists():
                return str(base_file.parent / base_filename)

        return None
