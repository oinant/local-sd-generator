"""
Inheritance resolver for Template System V2.0.

This module handles the resolution of the implements: field in configs,
loading parent configs recursively and merging them according to V2.0 merge rules.
"""

import logging
from pathlib import Path
from typing import Union, Optional
from copy import deepcopy

from ..models.config_models import TemplateConfig, ChunkConfig, PromptConfig
from ..loaders.yaml_loader import YamlLoader
from ..loaders.parser import ConfigParser

logger = logging.getLogger(__name__)


class InheritanceResolver:
    """
    Resolves inheritance chains (implements:) with recursive loading and merging.

    The resolver maintains a cache of resolved configs to avoid redundant loads.
    It implements the V2.0 merge rules for each config section.

    Merge Rules:
    - parameters: MERGE (child overrides parent keys)
    - imports: MERGE (child overrides parent keys)
    - chunks: MERGE (child overrides parent keys)
    - defaults: MERGE (child overrides parent keys)
    - template: REPLACE (child replaces parent, logs WARNING)
    - negative_prompt: REPLACE (child replaces parent if provided)

    Attributes:
        loader: YamlLoader instance for loading YAML files
        parser: ConfigParser instance for parsing configs
        resolution_cache: Dict mapping absolute file paths to resolved configs
    """

    ConfigType = Union[TemplateConfig, ChunkConfig, PromptConfig]

    def __init__(self, loader: YamlLoader, parser: ConfigParser):
        """
        Initialize the inheritance resolver.

        Args:
            loader: YamlLoader instance for loading YAML files
            parser: ConfigParser instance for parsing raw YAML data
        """
        self.loader = loader
        self.parser = parser
        self.resolution_cache: dict[str, InheritanceResolver.ConfigType] = {}

    def resolve_implements(self, config: ConfigType) -> ConfigType:
        """
        Resolve inheritance chain recursively.

        This method loads parent configs recursively, merges them according to
        V2.0 merge rules, and returns the fully resolved config.

        Args:
            config: Config object (Template, Chunk, or Prompt) to resolve

        Returns:
            Fully resolved config with all parent fields merged

        Raises:
            FileNotFoundError: If a parent file doesn't exist
            ValueError: If inheritance creates a type mismatch (chunks only)
        """
        # If no inheritance, return as-is
        if not config.implements:
            return config

        # Check cache (keyed by absolute path)
        cache_key = str(config.source_file.resolve())
        if cache_key in self.resolution_cache:
            logger.debug(f"Cache hit for {config.source_file.name}")
            return self.resolution_cache[cache_key]

        logger.info(f"Resolving inheritance for {config.source_file.name}")

        # Load parent
        base_path = config.source_file.parent
        try:
            parent_path = self.loader.resolve_path(
                config.implements,
                base_path,
                allow_absolute=False  # Enforce relative paths for portability
            )
        except ValueError as e:
            raise ValueError(
                f"Invalid implements path in {config.source_file.name}: {e}"
            )

        # Load parent YAML data
        parent_data = self.loader.load_file(parent_path, base_path=parent_path.parent)

        # Parse parent config (auto-detect type)
        parent_config = self._parse_config(parent_data, parent_path)

        # Recursively resolve parent's implements
        parent_resolved = self.resolve_implements(parent_config)

        # Validate type compatibility (chunks only)
        if isinstance(config, ChunkConfig):
            self._validate_chunk_types(config, parent_resolved)

        # Merge parent and child
        merged = self._merge_configs(parent_resolved, config)

        # Cache the result
        self.resolution_cache[cache_key] = merged

        return merged

    def _parse_config(self, data: dict, source_file: Path) -> ConfigType:
        """
        Parse config data and auto-detect type.

        Detection logic:
        - If 'generation' field exists → PromptConfig
        - Else if 'type' field exists → ChunkConfig
        - Else → TemplateConfig

        Args:
            data: Raw YAML dictionary
            source_file: Absolute path to the source file

        Returns:
            Parsed config object (TemplateConfig, ChunkConfig, or PromptConfig)

        Raises:
            KeyError: If required fields are missing
        """
        if 'generation' in data:
            return self.parser.parse_prompt(data, source_file)
        elif 'type' in data:
            return self.parser.parse_chunk(data, source_file)
        else:
            return self.parser.parse_template(data, source_file)

    def _validate_chunk_types(
        self,
        child: ChunkConfig,
        parent: ConfigType
    ) -> None:
        """
        Validate type compatibility for chunk inheritance.

        Rules:
        - Child chunk can only implement parent chunk with same type
        - If parent has no type → WARNING (assume child type)
        - If types mismatch → ERROR

        Args:
            child: Child ChunkConfig
            parent: Parent config (should be ChunkConfig)

        Raises:
            ValueError: If types are incompatible
        """
        # Parent must be a chunk too
        if not isinstance(parent, ChunkConfig):
            raise ValueError(
                f"Chunk {child.source_file.name} cannot implement "
                f"non-chunk {parent.source_file.name}"
            )

        # Check type compatibility
        if parent.type != child.type:
            if not parent.type:
                # Warning: parent has no type, assume child type
                logger.warning(
                    f"Parent {parent.source_file.name} has no type, "
                    f"assuming '{child.type}' from child {child.source_file.name}"
                )
            else:
                # Error: type mismatch
                raise ValueError(
                    f"Type mismatch: {child.source_file.name} (type='{child.type}') "
                    f"cannot implement {parent.source_file.name} (type='{parent.type}')"
                )

    def _merge_configs(
        self,
        parent: ConfigType,
        child: ConfigType
    ) -> ConfigType:
        """
        Merge parent and child configs according to V2.0 merge rules.

        Merge Rules:
        - parameters: MERGE (child keys override parent keys)
        - imports: MERGE (child keys override parent keys)
        - chunks: MERGE (child keys override parent keys)
        - defaults: MERGE (child keys override parent keys)
        - template: REPLACE (child replaces parent, logs WARNING if parent had template)
        - negative_prompt: REPLACE (child replaces if provided)

        Args:
            parent: Resolved parent config
            child: Child config

        Returns:
            Merged config (child type preserved)

        Note:
            The merge is non-destructive (uses deepcopy internally)
        """
        # Create a deep copy of child to avoid mutations
        merged = deepcopy(child)

        # --- MERGE RULES ---

        # 1. parameters: MERGE (TemplateConfig and PromptConfig)
        if isinstance(child, TemplateConfig) and isinstance(parent, TemplateConfig):
            merged.parameters = {**parent.parameters, **child.parameters}
        elif isinstance(child, PromptConfig) and isinstance(parent, (TemplateConfig, PromptConfig)):
            # PromptConfig can inherit from TemplateConfig or PromptConfig
            merged.parameters = {**parent.parameters, **child.parameters}

        # 2. imports: MERGE (all config types)
        merged.imports = {**parent.imports, **child.imports}

        # 3. chunks and defaults: MERGE (ChunkConfig only)
        if isinstance(child, ChunkConfig) and isinstance(parent, ChunkConfig):
            merged.chunks = {**parent.chunks, **child.chunks}
            merged.defaults = {**parent.defaults, **child.defaults}

        # 4. template: REPLACE with WARNING
        # Note: child.template always replaces parent.template
        # We log a warning only if parent had a non-empty template
        if parent.template and parent.template.strip():
            if child.template != parent.template:
                logger.warning(
                    f"Overriding parent template in {child.source_file.name}. "
                    f"Consider creating a new base config instead of overriding."
                )

        # 5. negative_prompt: REPLACE (TemplateConfig and PromptConfig)
        # Child's negative_prompt is already set, but we inherit if child didn't specify
        if hasattr(parent, 'negative_prompt') and hasattr(child, 'negative_prompt'):
            # If child explicitly provided negative_prompt, use it (already in child)
            # If child didn't provide (empty or None), inherit from parent
            if not child.negative_prompt:
                merged.negative_prompt = parent.negative_prompt

        return merged

    def clear_cache(self) -> None:
        """Clear the resolution cache."""
        self.resolution_cache.clear()
        logger.debug("Inheritance resolution cache cleared")

    def invalidate(self, file_path: Path | str) -> None:
        """
        Invalidate a specific file in the resolution cache.

        Args:
            file_path: Path to the file to invalidate (absolute or relative)
        """
        cache_key = str(Path(file_path).resolve())
        if cache_key in self.resolution_cache:
            del self.resolution_cache[cache_key]
            logger.debug(f"Invalidated cache for {file_path}")
