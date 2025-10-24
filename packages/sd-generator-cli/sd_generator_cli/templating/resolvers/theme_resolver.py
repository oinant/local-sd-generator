"""
Theme and style resolution for Themable Templates.

This module implements the core merge logic:
- Theme imports override template imports
- Style-based variant resolution
- Fallback chain: theme → template → common
- Import resolution tracking for manifest
"""

from pathlib import Path
from typing import Dict, Optional, List
import logging

from sd_generator_cli.templating.models import (
    TemplateConfig,
    ThemeConfig,
    ImportResolution
)
from sd_generator_cli.templating.resolvers.style_resolver import StyleResolver

logger = logging.getLogger(__name__)


class ThemeResolver:
    """Resolver for theme + style based import resolution."""

    def __init__(self, configs_dir: Path):
        """
        Initialize theme resolver.

        Args:
            configs_dir: Base configs directory
        """
        self.configs_dir = Path(configs_dir)
        self.style_resolver = StyleResolver()

    def merge_imports(
        self,
        template: TemplateConfig,
        theme: Optional[ThemeConfig],
        style: str = "default",
        known_styles: Optional[List[str]] = None
    ) -> tuple[Dict[str, str], Dict[str, ImportResolution]]:
        """
        Merge template imports with theme overrides and style resolution.

        Resolution priority:
        1. Theme override (with style if sensitive)
        2. Template import (with style if sensitive)
        3. Common fallback (with style if sensitive)

        Args:
            template: Template configuration
            theme: Theme configuration (optional)
            style: Target style (e.g., "cartoon", "realistic", "photorealistic")
            known_styles: List of known styles for detection (auto-discovered if None)

        Returns:
            Tuple of (resolved_imports, import_resolution_metadata)

        Example:
            >>> resolver = ThemeResolver(Path("/configs"))
            >>> template = TemplateConfig(...)
            >>> theme = ThemeConfig(name="cyberpunk", ...)
            >>> imports, metadata = resolver.merge_imports(template, theme, "cartoon")
            >>> imports["Rendering"]
            'cyberpunk/cyberpunk_rendering.cartoon.yaml'
        """
        # Auto-discover known styles from theme if not provided
        if known_styles is None and theme:
            known_styles = self._discover_styles_from_theme(theme)

        resolved_imports: Dict[str, str] = {}
        resolution_metadata: Dict[str, ImportResolution] = {}

        # Get all placeholders from template imports
        for placeholder, template_import in template.imports.items():
            # Check if placeholder is style-sensitive
            is_style_sensitive = placeholder in template.style_sensitive_placeholders

            # Resolve this import
            resolved_file, metadata = self._resolve_import(
                placeholder=placeholder,
                template_import=str(template_import),
                theme=theme,
                style=style,
                is_style_sensitive=is_style_sensitive,
                known_styles=known_styles or []
            )

            if resolved_file:
                resolved_imports[placeholder] = resolved_file
                resolution_metadata[placeholder] = metadata
            else:
                # Log warning but don't fail
                logger.warning(
                    f"Could not resolve import for '{placeholder}' "
                    f"(style={style}, theme={theme.name if theme else 'none'})"
                )

        return resolved_imports, resolution_metadata

    def _resolve_import(
        self,
        placeholder: str,
        template_import: str,
        theme: Optional[ThemeConfig],
        style: str,
        is_style_sensitive: bool,
        known_styles: List[str]
    ) -> tuple[Optional[str], ImportResolution]:
        """
        Resolve a single import with theme + style logic.

        Args:
            placeholder: Placeholder name (e.g., "Rendering")
            template_import: Template's default import path
            theme: Theme config (optional)
            style: Target style
            is_style_sensitive: Whether this placeholder varies by style
            known_styles: List of known styles for detection

        Returns:
            Tuple of (resolved_path, resolution_metadata)
        """
        # Build import key with style if sensitive
        if is_style_sensitive:
            import_key = f"{placeholder}.{style}"
        else:
            import_key = placeholder

        # Strategy 1: Try theme override
        if theme and import_key in theme.imports:
            file_path = theme.imports[import_key]
            full_path = self.configs_dir / "themes" / file_path

            if full_path.exists():
                return file_path, ImportResolution(
                    source="theme",
                    file=file_path,
                    type="thematic",
                    override=True,
                    style_sensitive=is_style_sensitive,
                    resolved_style=style if is_style_sensitive else None
                )

        # Strategy 2: Try template import with style resolution
        if is_style_sensitive and known_styles:
            # Try to resolve template import with style
            resolved_path = self.style_resolver.resolve_style_fallback(
                base_path=template_import,
                target_style=style,
                configs_dir=self.configs_dir,
                known_styles=known_styles,
                fallback_dirs=["common"]
            )

            if resolved_path:
                # Determine source (common vs template)
                source = "common" if resolved_path.startswith("common/") else "template"
                import_type = "common" if source == "common" else "thematic"

                return resolved_path, ImportResolution(
                    source=source,
                    file=resolved_path,
                    type=import_type,
                    override=False,
                    style_sensitive=True,
                    resolved_style=style
                )
        else:
            # Not style-sensitive, use template import as-is
            full_path = self.configs_dir / template_import

            if full_path.exists():
                return template_import, ImportResolution(
                    source="template",
                    file=template_import,
                    type="thematic",
                    override=False,
                    style_sensitive=False
                )

        # Strategy 3: Try common fallback (extract filename from template_import)
        if is_style_sensitive and known_styles:
            filename = Path(template_import).name
            filename_with_style = self.style_resolver.replace_style_suffix(
                filename, style, known_styles
            )

            common_path = Path("common") / Path(template_import).parent.name / filename_with_style
            full_common_path = self.configs_dir / common_path

            if full_common_path.exists():
                return str(common_path), ImportResolution(
                    source="common",
                    file=str(common_path),
                    type="common",
                    override=False,
                    style_sensitive=True,
                    resolved_style=style,
                    note=f"Fallback to common (theme/template not found for style={style})"
                )

        # Resolution failed
        return None, ImportResolution(
            source="none",
            file="",
            type="unknown",
            override=False,
            style_sensitive=is_style_sensitive,
            resolved_style=style if is_style_sensitive else None,
            note=f"Import not found for '{placeholder}' (style={style})"
        )

    def _discover_styles_from_theme(self, theme: ThemeConfig) -> List[str]:
        """
        Auto-discover styles from theme import keys.

        Example:
            theme.imports = {
                "Rendering.cartoon": "...",
                "Rendering.realistic": "...",
                "Details.minimalist": "..."
            }
            → Returns ["cartoon", "realistic", "minimalist"]
        """
        styles = set()
        for key in theme.imports.keys():
            if '.' in key:
                # Extract style suffix
                parts = key.split('.')
                if len(parts) >= 2:
                    styles.add(parts[-1])
        return sorted(styles)

    def validate_theme_compatibility(
        self,
        template: TemplateConfig,
        theme: ThemeConfig,
        style: str = "default",
        known_styles: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Validate theme compatibility with template.

        Checks which template imports the theme provides and which are missing.

        Args:
            template: Template configuration
            theme: Theme configuration
            style: Target style
            known_styles: List of known styles

        Returns:
            Dict mapping placeholder to status ("provided" | "missing" | "fallback")

        Example:
            >>> status = resolver.validate_theme_compatibility(template, theme, "cartoon")
            >>> status["Rendering"]
            'provided'
            >>> status["Accessories"]
            'missing'
        """
        if known_styles is None:
            known_styles = self._discover_styles_from_theme(theme)

        status: Dict[str, str] = {}

        for placeholder in template.imports.keys():
            is_style_sensitive = placeholder in template.style_sensitive_placeholders

            if is_style_sensitive:
                import_key = f"{placeholder}.{style}"
            else:
                import_key = placeholder

            if import_key in theme.imports:
                status[placeholder] = "provided"
            else:
                # Check if fallback exists
                template_import = str(template.imports[placeholder])
                resolved_path = self.style_resolver.resolve_style_fallback(
                    base_path=template_import,
                    target_style=style,
                    configs_dir=self.configs_dir,
                    known_styles=known_styles,
                    fallback_dirs=["common"]
                )

                if resolved_path:
                    status[placeholder] = "fallback"
                else:
                    status[placeholder] = "missing"

        return status
