"""
Data models for Themable Templates feature.

This module defines the models for theme configuration, import resolution tracking,
and rating-based variant resolution.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List


@dataclass
class ThemeConfig:
    """
    Configuration for a theme.

    A theme is a collection of imports that can be applied to themable templates.
    Themes can be explicit (with theme.yaml) or implicit (inferred from files).

    Attributes:
        name: Theme name (e.g., "cyberpunk", "rockstar")
        path: Path to theme directory
        explicit: True if theme.yaml exists, False if inferred
        imports: Import mappings (may include rating suffixes like "Outfit.sexy")
        variations: List of available variation categories
    """
    name: str
    path: Path
    explicit: bool
    imports: Dict[str, str] = field(default_factory=dict)
    variations: List[str] = field(default_factory=list)


@dataclass
class ImportResolution:
    """
    Metadata about how an import was resolved.

    Tracks the source and context of each import resolution for debugging,
    validation, and manifest generation.

    Attributes:
        source: Where the import came from ("theme" | "template" | "common")
        file: Path to resolved file
        type: Category of import ("thematic" | "common")
        override: True if theme overrode template default
        style_sensitive: True if import varies by style
        resolved_style: Style used for resolution (e.g., "cartoon", "realistic")
        note: Optional warning or info message
    """
    source: str  # "theme" | "template" | "common"
    file: str
    type: str  # "thematic" | "common"
    override: bool
    style_sensitive: bool = False
    resolved_style: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            "source": self.source,
            "file": self.file,
            "type": self.type,
            "override": self.override,
            "style_sensitive": self.style_sensitive,
            "resolved_style": self.resolved_style,
            "note": self.note,
        }
