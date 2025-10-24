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

    def __init__(self, configs_dir: Optional[str] = None):
        """
        Initialize the V2 pipeline.

        Args:
            configs_dir: Base directory for config files (optional)
        """
        self.configs_dir = Path(configs_dir) if configs_dir else None

        # Initialize all components
        self.loader = YamlLoader()
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

        # Phase 3.5: Theme merging (if themable template)
        # Check if this is a themable template (TemplateConfig with themable=True)
        theme: Optional[ThemeConfig] = None
        import_resolution_metadata: Dict[str, Any] = {}

        # Check if themable (only TemplateConfig can be themable, not PromptConfig)
        is_themable = (
            hasattr(resolved_config, 'themable') and
            getattr(resolved_config, 'themable', False)
        )

        if is_themable and isinstance(resolved_config, TemplateConfig):
            if not self.theme_resolver:
                raise ValueError("Theme support requires configs_dir to be set")

            # Load theme if specified
            if theme_name and self.theme_loader:
                theme = self.theme_loader.load_theme(theme_name)

            # Merge theme imports with template imports
            merged_imports, import_resolution_metadata = self.theme_resolver.merge_imports(
                template=resolved_config,
                theme=theme,
                style=style
            )

            # Replace template imports with merged imports
            from copy import deepcopy
            resolved_config = deepcopy(resolved_config)
            resolved_config.imports = merged_imports

        # Phase 4: Resolve imports
        # Use the config's source file directory as base path for import resolution
        base_path = config.source_file.parent
        resolved_imports = self.import_resolver.resolve_imports(
            resolved_config,
            base_path
        )

        # Merge parameters from inheritance chain
        merged_params = self._merge_parameters(inheritance_chain)

        # Build resolved context
        context = ResolvedContext(
            imports=resolved_imports,
            chunks={},  # Chunks will be available via imports
            parameters=merged_params,
            # Theme metadata (Phase 1)
            style=style,
            import_resolution=import_resolution_metadata
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

        # Generate prompts
        prompts = self.generator.generate_prompts(
            template=template,
            context=context,
            generation=config.generation
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
        resolved_config, context = self.resolve(config, theme_name, style)

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

                    # Try to detect multi-source imports (this is approximate)
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
