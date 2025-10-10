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
from typing import List, Dict, Any

from templating.v2.loaders.yaml_loader import YamlLoader
from templating.v2.loaders.parser import ConfigParser
from templating.v2.validators.validator import ConfigValidator
from templating.v2.resolvers.inheritance_resolver import InheritanceResolver
from templating.v2.resolvers.import_resolver import ImportResolver
from templating.v2.resolvers.template_resolver import TemplateResolver
from templating.v2.normalizers.normalizer import PromptNormalizer
from templating.v2.generators.generator import PromptGenerator
from templating.v2.models.config_models import (
    PromptConfig,
    TemplateConfig,
    ChunkConfig,
    ResolvedContext
)


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

    def __init__(self, configs_dir: str = None):
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
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        data = self.loader.load_file(config_path, config_path.parent)

        # Parse into model
        config = self.parser.parse_prompt(data, config_path)

        # Validate
        validation_result = self.validator.validate(config)
        if not validation_result.is_valid:
            raise ValueError(f"Validation failed: {validation_result.to_json()}")

        return config

    def resolve(self, config: PromptConfig) -> ResolvedContext:
        """
        Resolve inheritance, imports, and templates.

        This performs:
        1. Inheritance resolution (implements: chain)
        2. Import resolution (imports: declarations)
        3. Parameter merging from inheritance chain

        Args:
            config: Parsed PromptConfig

        Returns:
            ResolvedContext with all imports and chunks loaded

        Raises:
            ValueError: If resolution fails
        """
        # Phase 3: Resolve inheritance chain
        resolved_config = self.inheritance_resolver.resolve_implements(config)
        # Build simple chain for parameter merging (just use the resolved config)
        inheritance_chain = [resolved_config]

        # Phase 4: Resolve imports
        # Use the config's source file directory as base path for import resolution
        base_path = config.source_file.parent
        resolved_imports = self.import_resolver.resolve_imports(
            config,
            base_path
        )

        # Merge parameters from inheritance chain
        merged_params = self._merge_parameters(inheritance_chain)

        # Build resolved context
        context = ResolvedContext(
            imports=resolved_imports,
            chunks={},  # Chunks will be available via imports
            parameters=merged_params
        )

        return context

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
        template = config.template

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

    def run(self, config_path: str) -> List[Dict[str, Any]]:
        """
        End-to-end pipeline: load → resolve → generate.

        Args:
            config_path: Path to .prompt.yaml file

        Returns:
            List of generated prompts

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid or resolution fails
        """
        # Load config
        config = self.load(config_path)

        # Resolve inheritance and imports
        context = self.resolve(config)

        # Generate prompts
        prompts = self.generate(config, context)

        return prompts

    def _merge_parameters(
        self,
        inheritance_chain: List
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
