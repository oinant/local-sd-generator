"""
V2Pipeline orchestrator for Template System V2.0 - Phase 6.

This module provides the main orchestrator that coordinates all V2 components:
- YamlLoader: Load YAML files
- ConfigParser: Parse YAML into models
- ConfigValidator: Validate configs
- InheritanceResolver: Resolve implements: chains
- ImportResolver: Resolve imports: declarations
- TemplateResolver: Resolve templates with chunks and placeholders
- PromptNormalizer: Normalize final prompts
- PromptGenerator: Generate prompt variations
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

from sd_generator_cli.templating.loaders.yaml_loader import YamlLoader
from sd_generator_cli.templating.loaders.parser import ConfigParser
from sd_generator_cli.templating.loaders.theme_loader import ThemeLoader
from sd_generator_cli.templating.validators.validator import ConfigValidator
from sd_generator_cli.templating.resolvers.inheritance_resolver import InheritanceResolver
from sd_generator_cli.templating.resolvers.import_resolver import ImportResolver
from sd_generator_cli.templating.resolvers.template_resolver import TemplateResolver
from sd_generator_cli.templating.resolvers.theme_resolver import ThemeResolver
from sd_generator_cli.templating.normalizers.normalizer import PromptNormalizer
from sd_generator_cli.templating.generators.generator import PromptGenerator
from sd_generator_cli.templating.models.config_models import (
    PromptConfig,
    TemplateConfig,
    ChunkConfig,
    ResolvedContext
)
from sd_generator_cli.templating.models.theme_models import ThemeConfig


class V2Pipeline:
    """
    Main orchestrator for Template System V2.0.

    Coordinates the full pipeline:
    1. Load: Read YAML files and parse into models
    2. Validate: Check config correctness
    3. Resolve: Apply inheritance, imports, and templates
    4. Generate: Create prompt variations with normalization

    Example:
        pipeline = V2Pipeline()
        prompts = pipeline.run('path/to/prompt.yaml')
    """

    def __init__(self, configs_dir: Optional[str] = None, strict_validation: bool = False):
        """
        Initialize the V2 pipeline.

        Args:
            configs_dir: Base directory for config files (optional)
            strict_validation: If True, schema validation errors raise exceptions.
                             If False (default), validation errors are warnings only.
        """
        self.configs_dir = Path(configs_dir) if configs_dir else None
        self.strict_validation = strict_validation

        # Initialize all components
        self.loader = YamlLoader(strict_validation=strict_validation)
        self.parser = ConfigParser()
        self.validator = ConfigValidator(loader=self.loader)
        self.inheritance_resolver = InheritanceResolver(
            loader=self.loader,
            parser=self.parser
        )
        self.import_resolver = ImportResolver(
            loader=self.loader,
            parser=self.parser
        )
        self.template_resolver = TemplateResolver(
            loader=self.loader,
            parser=self.parser,
            import_resolver=self.import_resolver
        )
        self.normalizer = PromptNormalizer()
        self.generator = PromptGenerator(
            resolver=self.template_resolver,
            normalizer=self.normalizer
        )

        # Themable Templates support (Phase 1)
        self.theme_loader: Optional[ThemeLoader]
        self.theme_resolver: Optional[ThemeResolver]
        if self.configs_dir:
            self.theme_loader = ThemeLoader(self.configs_dir)
            self.theme_resolver = ThemeResolver(self.configs_dir)
        else:
            self.theme_loader = None
            self.theme_resolver = None

    def load(self, config_path: str) -> PromptConfig:
        """
        Load and parse a prompt config file.

        Args:
            config_path: Path to .prompt.yaml file

        Returns:
            Parsed PromptConfig object

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        # Load YAML
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        # Si path est absolu, ne pas passer de base_path pour éviter duplication
        base_path = None if path.is_absolute() else path.parent
        data = self.loader.load_file(path, base_path)

        # Parse into model (detect type from extension)
        if '.template.' in path.name:
            config = self.parser.parse_template(data, path)
        else:
            config = self.parser.parse_prompt(data, path)

        # Validate
        validation_result = self.validator.validate(config)
        if not validation_result.is_valid:
            raise ValueError(f"Validation failed: {validation_result.to_json()}")

        return config

    def resolve(
        self,
        config: PromptConfig,
        theme_name: Optional[str] = None,
        theme_file: Optional[Path] = None,
        style: str = "default"
    ) -> tuple[PromptConfig, ResolvedContext]:
        """
        Resolve inheritance, imports, and templates.

        This performs:
        1. Inheritance resolution (implements: chain)
        2. Theme merging (if themable template + theme provided)
        3. Import resolution (imports: declarations)
        4. Parameter merging from inheritance chain
        5. Phase 1 chunk injection (structural only, preserving placeholders)

        Args:
            config: Parsed PromptConfig
            theme_name: Optional theme name (for themable templates)
            style: Art style (default, cartoon, realistic, etc.)

        Returns:
            Tuple of (resolved_config, context)
            - resolved_config: PromptConfig with template field populated after injection
            - context: ResolvedContext with all imports, chunks, and theme metadata

        Raises:
            ValueError: If resolution fails
        """
        # Phase 3: Resolve inheritance chain
        resolved_config = self.inheritance_resolver.resolve_implements(config)

        # Type narrow: ensure we got back a PromptConfig or TemplateConfig
        if not isinstance(resolved_config, (PromptConfig, TemplateConfig)):
            raise ValueError(f"Expected PromptConfig or TemplateConfig after resolution, got {type(resolved_config).__name__}")

        # Build simple chain for parameter merging (just use the resolved config)
        inheritance_chain = [resolved_config]

        # Phase 3.5: Theme resolution (if theme specified)
        # All templates/prompts are themable by default - just apply if theme is provided
        theme: Optional[ThemeConfig] = None
        import_sources: Dict[str, str] = {}  # Track which file provides each placeholder
        import_resolution_metadata: Dict[str, Any] = {}
        removed_placeholders: set = set()  # Track placeholders explicitly removed via [Remove]

        if theme_name or theme_file:
            if not self.theme_resolver or not self.theme_loader:
                raise ValueError("Theme support requires configs_dir to be set")

            # Load theme (either from theme_file or by discovering from themes block)
            if theme_file:
                # Direct theme file path provided
                theme = self.theme_loader.load_theme_from_file(str(theme_file))
            elif theme_name:
                # Theme name provided - discover available themes from template
                if not resolved_config.themes:
                    raise ValueError(
                        f"❌ No 'themes:' block found in {resolved_config.name}\n"
                        f"💡 Use --theme-file to specify theme path directly, or add a themes: block to your template"
                    )

                # Discover all available themes (explicit + autodiscovered)
                available_themes = self.theme_loader.discover_available_themes(
                    resolved_config.source_file,
                    resolved_config.themes
                )

                if theme_name not in available_themes:
                    available_str = ', '.join(sorted(available_themes.keys())) if available_themes else '(none)'
                    raise ValueError(
                        f"❌ Theme '{theme_name}' not found\n"
                        f"💡 Available themes: {available_str}\n"
                        f"   Or use --theme-file to load a custom theme"
                    )

                # Load theme from discovered path
                theme_path = available_themes[theme_name]
                theme = self.theme_loader.load_theme_from_file(theme_path)

            # Apply theme - COMPLETE substitution for thematic variations
            # Theme imports replace template's thematic imports
            # But preserve prompt's explicit imports (final overrides)
            from copy import deepcopy
            resolved_config = deepcopy(resolved_config)

            # Save prompt's explicit imports (from the original config before template merge)
            prompt_explicit_imports = config.imports.copy() if hasattr(config, 'imports') else {}

            # Start with theme imports (complete substitution of template)
            # Filter theme imports by style (handle PlaceholderName.style notation and [Remove] directive)
            filtered_theme_imports = {}
            for import_name, import_path in theme.imports.items():
                # Check for [Remove] directive FIRST (before style filtering)
                if self._is_remove_directive(import_path):
                    # Track placeholder name as explicitly removed
                    # For style-specific names like "Underwear.teasing", track base name only
                    base_name = import_name.rsplit('.', 1)[0] if '.' in import_name else import_name
                    removed_placeholders.add(base_name)
                    # Skip this placeholder entirely (will be missing → resolves to "")
                    continue

                if '.' in import_name:
                    # Style-specific import (e.g., "TeasingGestures.xxx")
                    base_name, import_style = import_name.rsplit('.', 1)
                    if import_style == style:
                        # Check if style-specific [Remove] directive
                        if self._is_remove_directive(import_path):
                            # Track placeholder as removed for this style
                            removed_placeholders.add(base_name)
                            # Remove for this style (also remove any default version)
                            filtered_theme_imports.pop(base_name, None)
                        else:
                            # Use this style variant
                            filtered_theme_imports[base_name] = import_path
                    # Otherwise skip (wrong style)
                else:
                    # Regular import (no style suffix)
                    # Only use if we don't already have a style-specific one
                    if import_name not in filtered_theme_imports:
                        filtered_theme_imports[import_name] = import_path

            resolved_config.imports = filtered_theme_imports

            # Re-apply prompt's explicit imports as final overrides
            # This allows prompts to override theme-provided variations
            resolved_config.imports.update(prompt_explicit_imports)

            # Track sources for manifest
            for placeholder in theme.imports.keys():
                import_sources[placeholder] = f"theme:{theme.name}"
            for placeholder in prompt_explicit_imports.keys():
                import_sources[placeholder] = f"prompt:{config.source_file.name}"

        # Phase 4: Resolve imports
        # Use the config's source file directory as base path for import resolution
        base_path = config.source_file.parent

        # Get style_sensitive_placeholders from resolved config
        style_sensitive_placeholders = getattr(resolved_config, 'style_sensitive_placeholders', [])

        resolved_imports, import_metadata = self.import_resolver.resolve_imports(
            resolved_config,
            base_path,
            style=style,
            style_sensitive_placeholders=style_sensitive_placeholders
        )

        # Merge parameters from inheritance chain
        merged_params = self._merge_parameters(inheritance_chain)

        # Build resolved context
        context = ResolvedContext(
            imports=resolved_imports,
            chunks={},  # Chunks will be available via imports
            parameters=merged_params,
            # Themes metadata
            style=style,
            import_resolution=import_resolution_metadata,
            import_sources=import_sources,  # Track which file provides each placeholder
            import_metadata=import_metadata,  # Track source counts for multi-file imports
            removed_placeholders=removed_placeholders  # Placeholders explicitly removed via [Remove]
        )

        # Phase 1: Inject chunks structurally (preserving placeholders)
        # This replaces @Chunk and @{Chunk with params} with the chunk's template text
        # but leaves all placeholders like {HairCut}, {HairColor} unresolved
        from copy import deepcopy
        resolved_config_with_chunks = deepcopy(resolved_config)

        # Call template resolver in Phase 1 mode (inject chunks only, no placeholder resolution)
        template_str = resolved_config.template if resolved_config.template else ""
        template_with_chunks = self.template_resolver._inject_all_chunks_phase1(
            template_str,
            {
                'imports': context.imports,
                'chunks': context.chunks,
                'defaults': {}
            }
        )

        resolved_config_with_chunks.template = template_with_chunks

        return resolved_config_with_chunks, context

    def generate(
        self,
        config: PromptConfig,
        context: ResolvedContext
    ) -> List[Dict[str, Any]]:
        """
        Generate prompt variations.

        Args:
            config: Prompt configuration
            context: Resolved context with imports

        Returns:
            List of prompt dicts with format:
            {
                'prompt': str,
                'negative_prompt': str,
                'seed': int,
                'variations': Dict[str, str]
            }
        """
        # Use config.template (the final template after inheritance)
        template = config.template if config.template else ""

        # Get generation config (with default for TemplateConfig)
        from sd_generator_cli.templating.models import GenerationConfig
        if hasattr(config, 'generation') and config.generation:
            generation_config = config.generation
        else:
            # Default generation for standalone templates (used in tests)
            generation_config = GenerationConfig(
                mode='combinatorial',
                seed=42,
                seed_mode='progressive',
                max_images=10
            )

        # Generate prompts
        prompts = self.generator.generate_prompts(
            template=template,
            context=context,
            generation=generation_config
        )

        # Add negative prompt if specified
        negative_prompt = config.negative_prompt or ''
        if negative_prompt:
            # Normalize negative prompt
            normalized_negative = self.normalizer.normalize_prompt(negative_prompt)
            for prompt in prompts:
                prompt['negative_prompt'] = normalized_negative

        # Add parameters from config
        for prompt in prompts:
            prompt['parameters'] = context.parameters.copy()

        return prompts

    def run(
        self,
        config_path: str,
        theme_name: Optional[str] = None,
        style: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        End-to-end pipeline: load → resolve → generate.

        Args:
            config_path: Path to .prompt.yaml or .template.yaml file
            theme_name: Optional theme name (for themable templates)
            style: Art style (default, cartoon, realistic, etc.)

        Returns:
            List of generated prompts

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid or resolution fails
        """
        # Load config
        config = self.load(config_path)

        # Resolve inheritance and imports (with theme support)
        resolved_config, context = self.resolve(config, theme_name, None, style)

        # Generate prompts (use resolved_config with template field populated)
        prompts = self.generate(resolved_config, context)

        return prompts

    def _merge_parameters(
        self,
        inheritance_chain: List[Any]
    ) -> Dict[str, Any]:
        """
        Merge parameters from inheritance chain.

        Parameters are merged from base to derived (child overrides parent).

        Args:
            inheritance_chain: List of configs from base to derived

        Returns:
            Merged parameters dict
        """
        merged = {}

        for config in inheritance_chain:
            if hasattr(config, 'parameters') and config.parameters:
                merged.update(config.parameters)

        return merged

    def _is_remove_directive(self, value: Any) -> bool:
        """
        Check if a theme import value is the [Remove] directive.

        The [Remove] directive is a YAML list with single string "Remove" (case-sensitive).
        Used to explicitly remove a placeholder for certain styles.

        Args:
            value: Import value from theme.yaml

        Returns:
            True if value is [Remove] directive, False otherwise

        Examples:
            >>> self._is_remove_directive(["Remove"])
            True
            >>> self._is_remove_directive("./file.yaml")
            False
            >>> self._is_remove_directive([])
            False
        """
        return (
            isinstance(value, list) and
            len(value) == 1 and
            value[0] == "Remove"
        )

    def validate_template(self, template: str, context: ResolvedContext) -> bool:
        """
        Validate that a template can be resolved with given context.

        Useful for pre-flight checks before generation.

        Args:
            template: Template string
            context: Resolved context

        Returns:
            True if template is valid, False otherwise
        """
        try:
            # Try to resolve template
            self.template_resolver.resolve_template(
                template,
                {
                    'imports': context.imports,
                    'chunks': context.chunks,
                    'defaults': {}
                }
            )
            return True
        except Exception:
            return False

    def get_available_variations(
        self,
        template: str,
        context: ResolvedContext
    ) -> Dict[str, List[str]]:
        """
        Get all available variations for a template.

        Useful for UI/debugging to see what variations will be used.

        Args:
            template: Template string
            context: Resolved context

        Returns:
            Dict mapping placeholder names to lists of variation values
        """
        import re

        variations = {}
        placeholder_pattern = re.compile(r'\{(\w+)(?:\[[^\]]+\])?\}')

        for match in placeholder_pattern.finditer(template):
            name = match.group(1)
            if name in context.imports:
                import_data = context.imports[name]
                if isinstance(import_data, dict):
                    variations[name] = list(import_data.values())

        return variations

    def calculate_total_combinations(
        self,
        template: str,
        context: ResolvedContext
    ) -> int:
        """
        Calculate total number of combinatorial combinations.

        Does not account for selectors or weight 0 exclusions.

        Args:
            template: Template string
            context: Resolved context

        Returns:
            Total number of combinations
        """
        variations = self.get_available_variations(template, context)

        if not variations:
            return 1

        total = 1
        for values in variations.values():
            total *= len(values)

        return total

    def get_variation_statistics(
        self,
        template: str,
        context: ResolvedContext
    ) -> Dict[str, Any]:
        """
        Get detailed statistics about variations used in template.

        Args:
            template: Template string
            context: Resolved context

        Returns:
            Dict with statistics:
            {
                'placeholders': {
                    'PlaceholderName': {
                        'count': int,
                        'sources': int (number of files merged),
                        'is_multi_source': bool
                    }
                },
                'total_combinations': int,
                'total_placeholders': int
            }
        """
        import re

        # Find all placeholders in template
        placeholder_pattern = re.compile(r'\{(\w+)(?:\[[^\]]+\])?\}')
        placeholder_names = set(placeholder_pattern.findall(template))

        statistics: Dict[str, Any] = {
            'placeholders': {},
            'total_combinations': 1,
            'total_placeholders': 0
        }

        for name in sorted(placeholder_names):
            if name in context.imports:
                import_data = context.imports[name]
                if isinstance(import_data, dict):
                    count = len(import_data)

                    # Get real source count from metadata (if available)
                    if name in context.import_metadata:
                        sources = context.import_metadata[name].get('source_count', 1)
                    else:
                        # Fallback: Try to detect multi-source imports (approximate heuristic)
                        # We check if the keys look like they have prefixes (source_key format)
                        keys = list(import_data.keys())
                        has_prefixes = any('_' in k for k in keys[:5])  # Sample first 5 keys

                        # Estimate number of sources (very rough heuristic)
                        sources = 1
                        if has_prefixes:
                            # Count unique prefixes
                            prefixes = set()
                            for key in keys:
                                if '_' in key:
                                    prefix = key.split('_')[0]
                                    prefixes.add(prefix)
                            sources = len(prefixes) if prefixes else 1

                    statistics['placeholders'][name] = {
                        'count': count,
                        'sources': sources,
                        'is_multi_source': sources > 1
                    }
                    total_comb = statistics['total_combinations']
                    if isinstance(total_comb, int):
                        statistics['total_combinations'] = total_comb * count
                    total_ph = statistics['total_placeholders']
                    if isinstance(total_ph, int):
                        statistics['total_placeholders'] = total_ph + 1

        return statistics

    # Themable Templates helper methods (Phase 1)

    def list_themes(self) -> List[str]:
        """
        List all available themes.

        Returns:
            List of theme names

        Raises:
            ValueError: If theme support not initialized (requires configs_dir)
        """
        if not self.theme_loader:
            raise ValueError("Theme support requires configs_dir to be set")

        themes = self.theme_loader.discover_themes()
        return [theme.name for theme in themes]

    def get_theme_info(self, theme_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a theme.

        Args:
            theme_name: Theme name

        Returns:
            Dict with theme info:
            {
                'name': str,
                'path': Path,
                'explicit': bool,
                'imports': Dict[str, str],
                'variations': List[str],
                'styles': List[str]  # Auto-discovered from imports
            }

        Raises:
            ValueError: If theme support not initialized or theme not found
        """
        if not self.theme_loader:
            raise ValueError("Theme support requires configs_dir to be set")

        theme = self.theme_loader.load_theme(theme_name)

        # Auto-discover styles from imports
        styles: set[str] = set()
        for key in theme.imports.keys():
            if '.' in key:
                parts = key.split('.')
                if len(parts) >= 2:
                    styles.add(parts[-1])

        return {
            'name': theme.name,
            'path': str(theme.path),
            'explicit': theme.explicit,
            'imports': theme.imports,
            'variations': theme.variations,
            'styles': sorted(styles)
        }

    def validate_theme_compatibility(
        self,
        config: TemplateConfig,
        theme_name: str,
        style: str = "default"
    ) -> Dict[str, str]:
        """
        Validate theme compatibility with template.

        Args:
            config: Template configuration
            theme_name: Theme name
            style: Target style

        Returns:
            Dict mapping placeholder to status ("provided" | "missing" | "fallback")

        Raises:
            ValueError: If theme support not initialized
        """
        if not self.theme_resolver or not self.theme_loader:
            raise ValueError("Theme support requires configs_dir to be set")

        theme = self.theme_loader.load_theme(theme_name)

        return self.theme_resolver.validate_theme_compatibility(
            template=config,
            theme=theme,
            style=style
        )
