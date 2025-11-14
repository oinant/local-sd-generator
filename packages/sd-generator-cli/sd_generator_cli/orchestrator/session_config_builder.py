"""SessionConfigBuilder - builds unified SessionConfig from CLI + Template configs."""

from pathlib import Path
from typing import Optional

from ..config.global_config import GlobalConfig
from ..templating.models.config_models import PromptConfig
from .cli_config import CLIConfig
from .session_config import SessionConfig


class SessionConfigBuilder:
    """Builds SessionConfig from CLIConfig + PromptConfig with priority resolution.

    This builder centralizes all priority logic for configuration resolution:
    1. CLI explicit flags (highest priority)
    2. Prompt YAML config
    3. Global defaults (lowest priority)

    Example:
        >>> cli_config = CLIConfig(template_path=..., api_url=..., ...)
        >>> prompt_config = PromptConfig(...)  # Loaded from YAML
        >>> builder = SessionConfigBuilder(global_config)
        >>> session_config = builder.build(cli_config, prompt_config)
    """

    def __init__(self, global_config: GlobalConfig):
        """Initialize builder with global configuration.

        Args:
            global_config: Global configuration (sdgen_config.json)
        """
        self.global_config = global_config

    def build(
        self,
        cli_config: CLIConfig,
        prompt_config: PromptConfig
    ) -> SessionConfig:
        """Build unified SessionConfig from CLI and prompt configs.

        Priority resolution:
        - session_name: CLI override > prompt.output.session_name > prompt.name > template filename
        - total_images: CLI count > calculated from prompt (combinatorial space or prompt.generation.max_images)
        - seed_mode: CLI seeds (sweep) > prompt.generation.seed_mode
        - base_seed: prompt.generation.seed (if not -1)
        - theme/style: CLI values (always respected)
        - fixed_placeholders: Parsed from CLI --use-fixed
        - annotations: prompt.output.annotations.enabled

        Args:
            cli_config: Parsed CLI arguments
            prompt_config: Loaded prompt configuration (has GenerationConfig)

        Returns:
            SessionConfig: Unified immutable configuration

        Raises:
            ValueError: If configuration is invalid or inconsistent
        """
        # Resolve session name with priority logic
        session_name = self._resolve_session_name(cli_config, prompt_config)

        # Resolve total images count
        total_images = self._resolve_total_images(cli_config, prompt_config)

        # Resolve seed configuration
        seed_mode, base_seed, seed_list = self._resolve_seeds(cli_config, prompt_config)

        # Parse fixed placeholders from CLI
        fixed_placeholders = self._parse_fixed_placeholders(cli_config.use_fixed)

        # Determine if annotations are enabled
        annotations_enabled = self._is_annotations_enabled(prompt_config)

        return SessionConfig(
            # Session identity
            session_name=session_name,
            output_dir=cli_config.output_base_dir,
            # Prompt info
            template_path=cli_config.template_path,
            prompt_config=prompt_config,
            # Generation parameters
            total_images=total_images,
            generation_mode=prompt_config.generation.mode,
            seed_mode=seed_mode,
            base_seed=base_seed,
            seed_list=seed_list,
            # API configuration
            api_url=cli_config.api_url,
            dry_run=cli_config.dry_run,
            # Theme/style
            theme_name=cli_config.theme_name,
            style=cli_config.style,
            # Fixed placeholders
            fixed_placeholders=fixed_placeholders,
            # Flags
            skip_validation=cli_config.skip_validation,
            annotations_enabled=annotations_enabled,
        )

    def _resolve_session_name(
        self,
        cli: CLIConfig,
        prompt: PromptConfig
    ) -> str:
        """Resolve session name with priority logic and add timestamp.

        Priority:
        1. CLI --session-name override (highest)
        2. prompt.output.session_name
        3. prompt.name
        4. prompt filename (lowest)

        The resolved name is then prefixed with a timestamp in format:
        YYYYMMDD_HHMMSS-{name}

        Args:
            cli: CLI configuration
            prompt: Prompt configuration

        Returns:
            Resolved session name with timestamp prefix
        """
        # Resolve base name with priority
        base_name = None

        # Priority 1: CLI override
        if cli.session_name_override:
            base_name = cli.session_name_override
        # Priority 2: prompt.output.session_name
        elif prompt.output and prompt.output.session_name:
            base_name = prompt.output.session_name
        # Priority 3: prompt.name
        elif prompt.name:
            base_name = prompt.name
        # Priority 4: prompt filename (fallback)
        else:
            base_name = cli.template_path.stem

        # Add timestamp prefix
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}-{base_name}"

    def _resolve_total_images(
        self,
        cli: CLIConfig,
        prompt: PromptConfig
    ) -> int:
        """Resolve total images count with priority logic.

        Priority:
        1. CLI --count (explicit override)
        2. Template limit or calculated combinatorial space

        Args:
            cli: CLI configuration
            tpl: Template configuration

        Returns:
            Number of images to generate

        Note:
            The actual combinatorial space calculation will be done by
            PromptGenerator after context is loaded. For now, we use
            a placeholder default of 100 if not specified.
        """
        # Priority 1: CLI explicit count
        if cli.count is not None:
            return cli.count

        # Priority 2: Template-defined limit
        # TODO: This should be calculated from combinatorial space
        # For now, return a default or template-specified limit
        # This will be refined when PromptGenerator is implemented
        return 100  # Placeholder default

    def _resolve_seeds(
        self,
        cli: CLIConfig,
        prompt: PromptConfig
    ) -> tuple[str, Optional[int], Optional[list[int]]]:
        """Resolve seed configuration with priority logic.

        Priority:
        1. CLI --seeds flag (seed-sweep mode)
        2. Template generation.seed_mode and generation.seed

        Args:
            cli: CLI configuration
            tpl: Template configuration

        Returns:
            Tuple of (seed_mode, base_seed, seed_list)
            - seed_mode: "fixed", "progressive", "random", or "sweep"
            - base_seed: Base seed value (None if random or sweep)
            - seed_list: List of seeds for sweep mode (None otherwise)
        """
        # Priority 1: CLI --seeds flag overrides everything
        if cli.seeds:
            seed_list = self._parse_seed_list(cli.seeds)
            return "sweep", None, seed_list

        # Priority 2: Use prompt configuration
        seed_mode = prompt.generation.seed_mode
        base_seed = prompt.generation.seed if prompt.generation.seed != -1 else None

        return seed_mode, base_seed, None

    @staticmethod
    def _parse_seed_list(seeds_str: str) -> list[int]:
        """Parse seed list from CLI --seeds parameter.

        Supports two formats:
        - Comma-separated: "42,43,44" → [42, 43, 44]
        - Range: "100-110" → [100, 101, 102, ..., 110]

        Args:
            seeds_str: Seeds string from CLI (already validated)

        Returns:
            List of seed integers
        """
        # Check if it's a range format (START-END)
        if "-" in seeds_str and seeds_str.count("-") == 1:
            parts = seeds_str.split("-")
            start = int(parts[0].strip())
            end = int(parts[1].strip())
            return list(range(start, end + 1))

        # Comma-separated format
        return [int(s.strip()) for s in seeds_str.split(",")]

    def _parse_fixed_placeholders(self, fixed_str: Optional[str]) -> dict[str, str]:
        """Parse --use-fixed CLI parameter into dictionary.

        Format: 'Placeholder=value,Placeholder2=value2'

        Args:
            fixed_str: Raw --use-fixed string from CLI

        Returns:
            Dictionary of placeholder -> fixed value

        Raises:
            ValueError: If format is invalid
        """
        if not fixed_str:
            return {}

        result = {}
        for pair in fixed_str.split(","):
            if "=" not in pair:
                raise ValueError(
                    f"Invalid fixed placeholder format: '{pair}'. "
                    f"Expected: 'Placeholder=value'"
                )
            key, value = pair.split("=", 1)
            result[key.strip()] = value.strip()

        return result

    def _is_annotations_enabled(self, prompt: PromptConfig) -> bool:
        """Check if annotations are enabled in prompt config.

        Args:
            prompt: Prompt configuration

        Returns:
            True if annotations are enabled
        """
        if not prompt.output or not prompt.output.annotations:
            return False
        return prompt.output.annotations.enabled
