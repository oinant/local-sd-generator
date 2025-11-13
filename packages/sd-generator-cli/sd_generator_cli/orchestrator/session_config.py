"""SessionConfig - unified immutable configuration for generation session."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..templating.models.config_models import PromptConfig


@dataclass(frozen=True)
class SessionConfig:
    """Unified configuration for the entire generation session.

    This is the single source of truth for all components in the orchestrator.
    It combines CLI arguments, template config, and global config with proper
    priority resolution.

    Priority order (highest to lowest):
    1. CLI explicit flags (--session-name, --count, --seeds, etc.)
    2. Template YAML config
    3. Global defaults (sdgen_config.json)

    This class is immutable (frozen=True) to prevent accidental mutations
    during the session lifecycle.

    Attributes:
        # Session identity
        session_name: Resolved session name (with priority logic)
        output_dir: Base output directory (from global config)
        session_path: Computed property -> output_dir / session_name

        # Template info
        template_path: Path to the template YAML file
        template_config: Full template configuration (from YAML)

        # Generation parameters (with overrides applied)
        total_images: Number of images to generate (resolved from CLI vs template)
        generation_mode: "combinatorial" or "random"
        seed_mode: "fixed", "progressive", or "random"
        base_seed: Base seed value (None if random mode)
        seed_list: List of seeds for seed-sweep mode (None otherwise)

        # API configuration
        api_url: Stable Diffusion API URL
        dry_run: If True, don't call API (just generate prompts)

        # Theme/style
        theme_name: Theme name (e.g., "cyberpunk")
        style: Style variant (e.g., "default", "anime")

        # Fixed placeholders (from --use-fixed)
        fixed_placeholders: Dict of placeholder -> fixed value

        # Flags
        skip_validation: Skip YAML schema validation
        annotations_enabled: Enable annotation worker
    """

    # ========================================================================
    # Session Identity
    # ========================================================================
    session_name: str
    output_dir: Path

    # ========================================================================
    # Prompt Config
    # ========================================================================
    template_path: Path  # Path to the loaded template/prompt file
    prompt_config: PromptConfig  # Resolved prompt configuration (has GenerationConfig)

    # ========================================================================
    # Generation Parameters
    # ========================================================================
    total_images: int
    generation_mode: str  # "combinatorial" or "random"
    seed_mode: str  # "fixed", "progressive", "random"
    base_seed: Optional[int] = None
    seed_list: Optional[list[int]] = None

    # ========================================================================
    # API Configuration
    # ========================================================================
    api_url: str = "http://127.0.0.1:7860"
    dry_run: bool = False

    # ========================================================================
    # Theme/Style
    # ========================================================================
    theme_name: Optional[str] = None
    style: str = "default"

    # ========================================================================
    # Fixed Placeholders
    # ========================================================================
    fixed_placeholders: dict[str, str] = None  # type: ignore[assignment]

    # ========================================================================
    # Flags
    # ========================================================================
    skip_validation: bool = False
    annotations_enabled: bool = False

    def __post_init__(self) -> None:
        """Post-initialization validation and defaults."""
        # Handle mutable default for fixed_placeholders
        if self.fixed_placeholders is None:
            # Use object.__setattr__ because dataclass is frozen
            object.__setattr__(self, "fixed_placeholders", {})

        # Validate generation_mode
        valid_modes = {"combinatorial", "random"}
        if self.generation_mode not in valid_modes:
            raise ValueError(
                f"Invalid generation_mode: {self.generation_mode}. "
                f"Must be one of {valid_modes}"
            )

        # Validate seed_mode
        valid_seed_modes = {"fixed", "progressive", "random", "sweep"}
        if self.seed_mode not in valid_seed_modes:
            raise ValueError(
                f"Invalid seed_mode: {self.seed_mode}. "
                f"Must be one of {valid_seed_modes}"
            )

        # Validate total_images is positive
        if self.total_images <= 0:
            raise ValueError(f"total_images must be positive, got: {self.total_images}")

        # Validate seed_list and seed_mode consistency
        if self.seed_list and self.seed_mode != "sweep":
            # Note: seed_mode "sweep" is implicit when seed_list is provided
            pass  # Allow for now, builder should handle this

        # Validate base_seed range
        if self.base_seed is not None and self.base_seed < -1:
            raise ValueError(f"base_seed must be >= -1, got: {self.base_seed}")

    @property
    def session_path(self) -> Path:
        """Computed session directory path.

        Returns:
            Full path to session directory (output_dir / session_name)
        """
        return self.output_dir / self.session_name

    @property
    def manifest_path(self) -> Path:
        """Computed manifest.json path.

        Returns:
            Full path to manifest.json file
        """
        return self.session_path / "manifest.json"

    def is_seed_sweep_mode(self) -> bool:
        """Check if session is in seed-sweep mode.

        Returns:
            True if seed_list is provided (seed-sweep mode)
        """
        return self.seed_list is not None and len(self.seed_list) > 0
