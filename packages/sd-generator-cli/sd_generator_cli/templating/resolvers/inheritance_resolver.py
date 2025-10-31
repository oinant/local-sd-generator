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
        # If no inheritance, handle standalone configs
        if not config.implements:
            # For standalone PromptConfig: copy prompt → template
            if isinstance(config, PromptConfig):
                resolved = deepcopy(config)
                resolved.template = config.prompt
                logger.debug(
                    f"Standalone prompt {config.source_file.name}: "
                    f"using prompt as template"
                )
                return resolved
            # For Template/Chunk: return as-is
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
            file_type = data['type']
            if file_type == 'template':
                return self.parser.parse_template(data, source_file)
            elif file_type == 'chunk':
                return self.parser.parse_chunk(data, source_file)
            elif file_type == 'prompt':
                return self.parser.parse_prompt(data, source_file)
            else:
                raise ValueError(f"Unknown type '{file_type}' in {source_file.name}")
        else:
            return self.parser.parse_template(data, source_file)

    def _validate_chunk_types(
        self,
        child: ChunkConfig,
        parent: ConfigType
    ) -> None:
        """
        Validate type compatibility for chunk inheritance.

        Rules (V2.0 Corrected):
        - Child chunk can only implement parent chunk with same type
        - Maximum 1 level of inheritance (definition → implementation only)
        - If parent has no type → WARNING (assume child type)
        - If types mismatch → ERROR

        Args:
            child: Child ChunkConfig
            parent: Parent config (should be ChunkConfig)

        Raises:
            ValueError: If types are incompatible or inheritance depth exceeds 1 level
        """
        # Parent must be a chunk too
        if not isinstance(parent, ChunkConfig):
            raise ValueError(
                f"Chunk {child.source_file.name} cannot implement "
                f"non-chunk {parent.source_file.name}"
            )

        # NEW: Validate max 1 level of inheritance
        # If parent has implements, child cannot implement parent (max 1 level)
        if parent.implements:
            raise ValueError(
                f"Chunk inheritance limited to 1 level: "
                f"{child.source_file.name} cannot implement {parent.source_file.name} "
                f"(which already implements {parent.implements}). "
                f"Chunks can only have definition → implementation (1 level)."
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

        Merge Rules (V2.0 Corrected - Template Method Pattern):
        - parameters: MERGE (child keys override parent keys)
        - imports: MERGE (child keys override parent keys)
        - chunks: MERGE (child keys override parent keys)
        - defaults: MERGE (child keys override parent keys)
        - template: INJECTION (child injected into parent's {prompt} placeholder)
        - negative_prompt: INJECTION (child injected into parent's {negprompt} placeholder)

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
            assert isinstance(merged, TemplateConfig)  # Type narrow for mypy
            merged.parameters = {**parent.parameters, **child.parameters}
        elif isinstance(child, PromptConfig) and isinstance(parent, (TemplateConfig, PromptConfig)):
            # PromptConfig can inherit from TemplateConfig or PromptConfig
            assert isinstance(merged, PromptConfig)  # Type narrow for mypy
            merged.parameters = {**parent.parameters, **child.parameters}

        # 2. imports: MERGE (all config types)
        merged.imports = {**parent.imports, **child.imports}

        # 3. chunks and defaults: MERGE (ChunkConfig only)
        if isinstance(child, ChunkConfig) and isinstance(parent, ChunkConfig):
            assert isinstance(merged, ChunkConfig)  # Type narrow for mypy
            merged.chunks = {**parent.chunks, **child.chunks}
            merged.defaults = {**parent.defaults, **child.defaults}

        # 4. template: INJECTION (Template Method Pattern)
        # If parent has {prompt} placeholder → inject child content
        # Otherwise → replace with warning
        if isinstance(child, PromptConfig):
            # PromptConfig has 'prompt' field, not 'template'
            # Inject child.prompt into parent.template's {prompt}
            if parent.template and '{prompt}' in parent.template:
                merged.template = parent.template.replace('{prompt}', child.prompt)
                logger.debug(
                    f"Injected prompt from {child.source_file.name} into "
                    f"{parent.source_file.name}'s {{prompt}} placeholder"
                )
            else:
                # Parent has no {prompt} - this should not happen if validation worked
                logger.error(
                    f"Parent template {parent.source_file.name} does not contain {{prompt}} placeholder. "
                    f"Cannot inject child prompt."
                )
                # Keep parent template as-is (validation should have caught this)
                merged.template = parent.template

        elif isinstance(child, TemplateConfig) and isinstance(parent, TemplateConfig):
            # Both are templates: inject child.template into parent.template's {prompt}
            if '{prompt}' in parent.template:
                merged.template = parent.template.replace('{prompt}', child.template)
                logger.debug(
                    f"Injected template from {child.source_file.name} into "
                    f"{parent.source_file.name}'s {{prompt}} placeholder"
                )
            else:
                # Parent has no {prompt} → REPLACE with warning
                logger.warning(
                    f"Parent {parent.source_file.name} has no {{prompt}} placeholder. "
                    f"Template from {child.source_file.name} will replace parent template completely. "
                    f"Consider adding {{prompt}} placeholder to parent template."
                )
                merged.template = child.template

        elif isinstance(child, ChunkConfig) and isinstance(parent, ChunkConfig):
            # Chunks: inject if parent has {prompt} (rare), otherwise replace
            if '{prompt}' in parent.template:
                merged.template = parent.template.replace('{prompt}', child.template)
                logger.debug(
                    f"Injected chunk template from {child.source_file.name} into "
                    f"{parent.source_file.name}'s {{prompt}} placeholder"
                )
            else:
                # No {prompt} → standard replace (chunks rarely use inheritance)
                if parent.template and parent.template.strip():
                    if child.template != parent.template:
                        logger.debug(
                            f"Child chunk {child.source_file.name} overrides parent template"
                        )
                merged.template = child.template

        # 5. negative_prompt: INJECTION (if {negprompt} present)
        # Only TemplateConfig and PromptConfig have negative_prompt, not ChunkConfig
        if isinstance(child, (TemplateConfig, PromptConfig)) and isinstance(parent, (TemplateConfig, PromptConfig)):
            assert isinstance(merged, (TemplateConfig, PromptConfig))  # Type narrow for mypy
            parent_neg = parent.negative_prompt
            child_neg = getattr(child, 'negative_prompt', None)
            if parent_neg and '{negprompt}' in parent_neg:
                # Inject child negative_prompt into {negprompt}
                child_neg_str = child_neg if child_neg else ''
                merged.negative_prompt = parent_neg.replace('{negprompt}', child_neg_str)
                logger.debug(
                    f"Injected negative_prompt from {child.source_file.name} into "
                    f"{{negprompt}} placeholder"
                )
            elif child_neg:
                # No {negprompt} in parent → child overrides
                merged.negative_prompt = child_neg
            else:
                # Child has no negative_prompt → inherit from parent
                merged.negative_prompt = parent_neg

        # 6. themes: INHERIT (child overrides if present, otherwise use parent)
        # Only TemplateConfig and PromptConfig have themes
        if isinstance(child, (TemplateConfig, PromptConfig)) and isinstance(parent, (TemplateConfig, PromptConfig)):
            assert isinstance(merged, (TemplateConfig, PromptConfig))  # Type narrow for mypy
            if not merged.themes and hasattr(parent, 'themes') and parent.themes:
                # Child has no themes → inherit from parent
                merged.themes = parent.themes
                logger.debug(
                    f"Inherited themes configuration from {parent.source_file.name}"
                )

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
