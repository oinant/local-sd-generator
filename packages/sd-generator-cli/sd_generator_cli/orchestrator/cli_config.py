"""CLIConfig dataclass - parsed CLI arguments from sdgen generate command."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class CLIConfig:
    """Configuration parsed from CLI arguments (sdgen generate ...).

    This is an immutable snapshot of what the user passed on the command line.
    It will be merged with TemplateConfig by SessionConfigBuilder to produce
    the final SessionConfig.

    Attributes:
        template_path: Path to the template YAML file
        count: Number of images to generate (overrides template if set)
        api_url: Stable Diffusion API URL
        dry_run: If True, generate prompts but don't call API
        output_base_dir: Base output directory (from global config)
        session_name_override: Session name override from CLI (highest priority)
        theme_name: Theme name to apply (e.g., "cyberpunk")
        theme_file: Path to explicit theme file (overrides theme_name)
        style: Style variant to use (e.g., "default", "anime")
        skip_validation: Skip YAML schema validation
        use_fixed: Fixed placeholder values (format: "Hair=blue,Eyes=green")
        seeds: Seed-sweep mode (comma-separated seeds: "42,43,44")
    """

    # Required parameters
    template_path: Path
    api_url: str
    output_base_dir: Path

    # Optional parameters with defaults
    count: Optional[int] = None
    dry_run: bool = False
    session_name_override: Optional[str] = None
    theme_name: Optional[str] = None
    theme_file: Optional[Path] = None
    style: str = "default"
    skip_validation: bool = False
    use_fixed: Optional[str] = None
    seeds: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate CLI config after initialization."""
        # Validate template_path exists
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")

        # Validate theme_file exists if specified
        if self.theme_file and not self.theme_file.exists():
            raise FileNotFoundError(f"Theme file not found: {self.theme_file}")

        # Validate count is positive if specified
        if self.count is not None and self.count <= 0:
            raise ValueError(f"Count must be positive, got: {self.count}")

        # Validate use_fixed format if specified
        if self.use_fixed:
            self._validate_fixed_placeholders(self.use_fixed)

        # Validate seeds format if specified
        if self.seeds:
            self._validate_seeds(self.seeds)

    @staticmethod
    def _validate_fixed_placeholders(fixed_str: str) -> None:
        """Validate fixed placeholder format: 'Key=value,Key2=value2'."""
        for pair in fixed_str.split(","):
            if "=" not in pair:
                raise ValueError(
                    f"Invalid fixed placeholder format: '{pair}'. "
                    f"Expected format: 'Placeholder=value,Placeholder2=value2'"
                )

    @staticmethod
    def _validate_seeds(seeds_str: str) -> None:
        """Validate seeds format: '42,43,44' or range '100-110'."""
        try:
            # Check if it's a range format (START-END)
            if "-" in seeds_str and seeds_str.count("-") == 1:
                # Range format: "9485300-9485305"
                parts = seeds_str.split("-")
                start = int(parts[0].strip())
                end = int(parts[1].strip())

                if start < -1 or end < -1:
                    raise ValueError("Seed values must be >= -1")
                if start > end:
                    raise ValueError("Range start must be <= end")

                # Valid range
                return

            # Comma-separated format: "42,43,44"
            seeds = [int(s.strip()) for s in seeds_str.split(",")]
            if not seeds:
                raise ValueError("Seeds list cannot be empty")
            if any(seed < -1 for seed in seeds):
                raise ValueError("Seed values must be >= -1")
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(
                    f"Invalid seeds format: '{seeds_str}'. "
                    f"Expected comma-separated integers (e.g., '42,43,44') or range (e.g., '100-110')"
                ) from e
            raise
