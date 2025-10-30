"""
Import resolver for Template System V2.0 - Phase 4.

This module handles resolution of imports with support for:
- Single file imports
- Inline string imports (with MD5 auto-generated keys)
- Multi-source merging with conflict detection
- Nested imports (e.g., chunks: {positive: ..., negative: ...})
"""

from pathlib import Path
from typing import Dict, List, Any, Union
from ..utils.hash_utils import md5_short


class ImportResolver:
    """
    Resolves imports from configuration files.

    Supports:
    - Single file: Outfit: ../variations/outfit.yaml
    - Inline strings: Place: ["luxury room", "jungle"]
    - Multi-source: Outfit: [../urban.yaml, ../chic.yaml, "red dress"]
    - Nested imports: chunks: {positive: ..., negative: ...}
    """

    def __init__(self, loader, parser):
        """
        Initialize the import resolver.

        Args:
            loader: YamlLoader instance for loading files
            parser: ConfigParser instance for parsing variations
        """
        self.loader = loader
        self.parser = parser

    def resolve_imports(
        self,
        config,
        base_path: Path,
        style: str = "default",
        style_sensitive_placeholders: List[str] = None
    ) -> tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, Any]]]:
        """
        Resolve all imports from a configuration.

        Args:
            config: Configuration object (TemplateConfig, ChunkConfig, or PromptConfig)
            base_path: Base path for resolving relative paths
            style: Target style for style-sensitive placeholders (e.g., "sports", "casual")
            style_sensitive_placeholders: List of placeholder names that vary by style

        Returns:
            Tuple of (resolved imports, metadata)
            - resolved: Dict mapping import names to variation dictionaries
              Format: {import_name: {key: value}}
              Example: {"Outfit": {"Urban1": "jeans", "7d8e3a2f": "red dress"}}
            - metadata: Dict mapping import names to metadata
              Format: {import_name: {"source_count": int}}
              Example: {"Outfit": {"source_count": 3}}

        Raises:
            ValueError: If duplicate keys found in multi-source merge
            FileNotFoundError: If import file not found
        """
        resolved = {}
        metadata = {}  # Track metadata for each import
        style_sensitive = style_sensitive_placeholders or []

        for import_name, import_value in config.imports.items():
            # Check if this placeholder is style-sensitive
            is_style_sensitive = import_name in style_sensitive

            if isinstance(import_value, str):
                # Single file import
                variations = self._load_variation_file(
                    import_value,
                    base_path,
                    style=style if is_style_sensitive else None
                )
                resolved[import_name] = variations
                # Analyze variations for metadata
                var_metadata = self._analyze_variations(variations)
                metadata[import_name] = {
                    "source_count": 1,
                    **var_metadata  # Add is_multipart, parts if applicable
                }

            elif isinstance(import_value, list):
                # Multi-source merge (files + inline strings)
                merged, source_count = self._merge_multi_sources(
                    import_value,
                    base_path,
                    import_name,
                    style=style if is_style_sensitive else None
                )
                resolved[import_name] = merged
                # Analyze merged variations for metadata
                var_metadata = self._analyze_variations(merged)
                metadata[import_name] = {
                    "source_count": source_count,
                    **var_metadata  # Add is_multipart, parts if applicable
                }

            elif isinstance(import_value, dict):
                # Nested imports (e.g., chunks: {positive: ..., negative: ...})
                nested = {}
                for nested_name, nested_value in import_value.items():
                    if isinstance(nested_value, str):
                        # Single file
                        variations = self._load_variation_file(
                            nested_value,
                            base_path,
                            style=style if is_style_sensitive else None
                        )
                        nested[nested_name] = variations
                    elif isinstance(nested_value, list):
                        # Multi-source in nested context
                        merged, source_count = self._merge_multi_sources(
                            nested_value,
                            base_path,
                            f"{import_name}.{nested_name}",
                            style=style if is_style_sensitive else None
                        )
                        nested[nested_name] = merged
                resolved[import_name] = nested
                # For nested imports, we don't track metadata separately (yet)

        return resolved, metadata

    def _load_variation_file(
        self,
        path: str,
        base_path: Path,
        style: str = None
    ) -> Union[Dict[str, str], Dict[str, Dict[str, str]], Dict[str, Any]]:
        """
        Load variations from a single file.

        If file is a .chunk.yaml, returns full chunk config dict.
        If file is a .adetailer.yaml, returns detector config.
        Otherwise, returns variations dict (simple or multi-part).

        Args:
            path: Relative path to variation file
            base_path: Base path for resolution
            style: Optional style for style-sensitive files (e.g., "sports", "casual")

        Returns:
            - Simple variations: Dict[str, str] - {key: value}
            - Multi-part variations: Dict[str, Dict[str, str]] - {key: {part: value}}
            - Chunk config: {template: str, imports: dict, defaults: dict, base_path: Path}
            - ADetailerDetector for .adetailer.yaml files

        Raises:
            FileNotFoundError: If file not found
            ValueError: If file format invalid
        """
        # If style is provided, try to resolve style variant first
        if style and style != "default":
            style_path = self._resolve_style_variant(path, style)
            if style_path:
                # Check if style variant exists
                try:
                    resolved_path_variant = self.loader.resolve_path(style_path, base_path)
                    if resolved_path_variant.exists():
                        # DEBUG: Print which file we're using
                        print(f"[DEBUG] Style variant found: {resolved_path_variant}")
                        path = style_path  # Use style variant
                    else:
                        print(f"[DEBUG] Style variant NOT found: {resolved_path_variant}, using default: {path}")
                except FileNotFoundError:
                    print(f"[DEBUG] Style variant resolution failed for: {style_path}, using default: {path}")
                    pass  # Fall back to default file
            else:
                print(f"[DEBUG] No style_path generated for: {path}")
        else:
            if style:
                print(f"[DEBUG] Style is 'default', using: {path}")
            else:
                print(f"[DEBUG] No style provided, using: {path}")

        resolved_path = self.loader.resolve_path(path, base_path)
        data = self.loader.load_file(resolved_path, base_path)

        # Check if this is a chunk file by extension (.chunk.yaml or .chunk.yml)
        is_chunk = (
            resolved_path.name.endswith('.chunk.yaml') or
            resolved_path.name.endswith('.chunk.yml')
        )

        # Check if this is an adetailer file by extension (.adetailer.yaml or .adetailer.yml)
        is_adetailer = (
            resolved_path.name.endswith('.adetailer.yaml') or
            resolved_path.name.endswith('.adetailer.yml')
        )

        # Check if this is a controlnet file by extension (.controlnet.yaml or .controlnet.yml)
        is_controlnet = (
            resolved_path.name.endswith('.controlnet.yaml') or
            resolved_path.name.endswith('.controlnet.yml')
        )

        if is_chunk:
            # Parse as ChunkConfig and return full config
            chunk_config = self.parser.parse_chunk(data, resolved_path)
            return {
                'template': chunk_config.template,
                'imports': chunk_config.imports,
                'defaults': chunk_config.defaults,
                'base_path': resolved_path.parent  # Store base path for import resolution
            }

        if is_adetailer:
            # Parse as ADetailerFileConfig and return detector
            adetailer_config = self.parser.parse_adetailer_file(data, resolved_path)
            # Return detector directly (will be used in parameters parsing)
            return adetailer_config.detector

        if is_controlnet:
            # Parse as ControlNetConfig and return it
            from ..loaders.controlnet_parser import parse_controlnet_file
            controlnet_config = parse_controlnet_file(resolved_path)
            # Return config directly (will be used in parameters parsing)
            return controlnet_config

        # Regular variation file - parse variations
        return self.parser.parse_variations(data)

    def _resolve_style_variant(self, path: str, style: str) -> str:
        """
        Resolve style variant path by adding style suffix.

        Converts:
          campus/campus-teasing_gesture.yaml + style="sports"
          → campus/campus-teasing_gesture.sports.yaml

        Args:
            path: Original file path
            style: Style name (e.g., "sports", "casual")

        Returns:
            Path with style suffix added
        """
        from pathlib import Path as PathLib
        p = PathLib(path)
        # Insert style before .yaml extension
        # "file.yaml" → "file.xxx.yaml"
        stem = p.stem  # "campus-teasing_gesture"
        suffix = p.suffix  # ".yaml"
        parent = p.parent  # "campus"

        new_name = f"{stem}.{style}{suffix}"
        return str(parent / new_name)

    def _merge_multi_sources(
        self,
        sources: List[str],
        base_path: Path,
        import_name: str,
        style: str = None
    ) -> tuple[Dict[str, str], int]:
        """
        Merge variations from multiple sources.

        Supports mixing files and inline strings.
        Inline strings get auto-generated MD5 keys.

        Duplicate keys are automatically prefixed with normalized source path
        to avoid conflicts (e.g., variations__hassaku__poses_dynamic__key).

        Args:
            sources: List of file paths and/or inline strings
            base_path: Base path for resolving file paths
            import_name: Name of import (for error messages)
            style: Optional style for style-sensitive files

        Returns:
            Tuple of (merged dict of variations, number of source files)
        """
        merged = {}
        key_sources = {}  # Track source of each key for conflict detection
        file_count = 0  # Track number of actual files (not inline strings)

        for source in sources:
            if self._is_inline_string(source):
                # Inline string - generate MD5 key
                inline_key = md5_short(source)
                # Remove quotes if present
                clean_value = source.strip('"\'')
                merged[inline_key] = clean_value
                key_sources[inline_key] = f"inline({inline_key})"
            else:
                # File - load and merge (with style if provided)
                variations = self._load_variation_file(source, base_path, style=style)
                file_count += 1  # Increment file counter

                # Handle conflicts with auto-prefixing
                for key, value in variations.items():
                    if key in merged:
                        # Duplicate detected - add prefix to disambiguate
                        prefix = self._normalize_path_to_prefix(source)
                        prefixed_key = f"{prefix}__{key}"
                        merged[prefixed_key] = value
                        key_sources[prefixed_key] = source
                    else:
                        # No conflict - use original key
                        merged[key] = value
                        key_sources[key] = source

        return merged, file_count

    def _normalize_path_to_prefix(self, path: str) -> str:
        """
        Normalize a file path to a safe prefix for variation keys.

        Transforms:
            ../../variations/hassaku/poses.dynamic.yaml
            → variations__hassaku__poses_dynamic

        Args:
            path: Relative file path from import

        Returns:
            Normalized prefix string (safe for use as key prefix)
        """
        import re

        # Remove ../ and ./ prefixes
        normalized = re.sub(r'^\.\./+', '', path)
        normalized = re.sub(r'^\./+', '', normalized)

        # Remove .yaml extension
        if normalized.endswith('.yaml'):
            normalized = normalized[:-5]

        # Replace path separators and dots with double underscore
        normalized = normalized.replace('/', '__')
        normalized = normalized.replace('.', '_')

        return normalized

    def _is_inline_string(self, source: str) -> bool:
        """
        Check if a source is an inline string vs a file path.

        Inline strings either:
        - Start with quotes (" or ')
        - Don't end with .yaml

        Args:
            source: Source string to check

        Returns:
            True if inline string, False if file path
        """
        source = source.strip()
        # Starts with quote = inline
        if source.startswith('"') or source.startswith("'"):
            return True
        # Doesn't end with .yaml = inline
        if not source.endswith('.yaml'):
            return True
        return False

    def _analyze_variations(self, variations: Any) -> Dict[str, Any]:
        """
        Analyze variations to extract metadata.

        Detects whether variations use multi-part format (dict values) vs
        simple format (string values) and extracts part names.

        Args:
            variations: Loaded variations (can be dict, ADetailerDetector, chunk config, etc.)

        Returns:
            Metadata dict with:
            - is_multipart: bool (True if any variation has dict value)
            - parts: List[str] (unique part names if multipart, empty otherwise)

        Examples:
            Simple variations:
                {"key1": "value1", "key2": "value2"}
                → {"is_multipart": False, "parts": []}

            Multi-part variations:
                {"hair1": {"main": "...", "lora": "..."}, "hair2": {"main": "...", "lora": "..."}}
                → {"is_multipart": True, "parts": ["main", "lora"]}

            Mixed (some simple, some multi-part):
                {"hair1": "simple", "hair2": {"main": "...", "lora": "..."}}
                → {"is_multipart": True, "parts": ["main", "lora"]}
        """
        # Handle special types (chunks, adetailer, controlnet)
        if not isinstance(variations, dict):
            return {"is_multipart": False, "parts": []}

        # Check if this is a chunk config dict (has 'template' key)
        if 'template' in variations and 'imports' in variations:
            return {"is_multipart": False, "parts": []}

        # Analyze variation values
        has_multipart = False
        part_names = set()

        for key, value in variations.items():
            if isinstance(value, dict) and not key in ['template', 'imports', 'defaults', 'base_path']:
                # This is a multi-part variation
                has_multipart = True
                # Collect part names
                for part_name in value.keys():
                    part_names.add(part_name)

        return {
            "is_multipart": has_multipart,
            "parts": sorted(part_names) if has_multipart else []
        }
