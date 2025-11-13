"""Complete unit tests for SessionConfigBuilder.

Test coverage:
- Session name resolution priority logic (4 scenarios)
- Total images resolution (CLI override vs template default)
- Seed configuration resolution (CLI seeds vs template seed_mode)
- Fixed placeholders parsing (valid/invalid formats)
- Annotations enabled detection
- Edge cases and error handling
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from sd_generator_cli.config.global_config import GlobalConfig
from sd_generator_cli.templating.models.config_models import (
    PromptConfig,
    GenerationConfig,
    OutputConfig,
    AnnotationsConfig,
)
from sd_generator_cli.orchestrator.cli_config import CLIConfig
from sd_generator_cli.orchestrator.session_config import SessionConfig
from sd_generator_cli.orchestrator.session_config_builder import SessionConfigBuilder


@pytest.fixture
def global_config() -> GlobalConfig:
    """Create minimal GlobalConfig for tests."""
    config = Mock(spec=GlobalConfig)
    config.configs_dir = Path("/fake/configs")
    config.output_dir = Path("/fake/output")
    return config


@pytest.fixture
def minimal_cli_config(tmp_path: Path) -> CLIConfig:
    """Create minimal valid CLIConfig for tests."""
    template_file = tmp_path / "test_template.yaml"
    template_file.touch()  # Create empty file

    return CLIConfig(
        template_path=template_file,
        api_url="http://127.0.0.1:7860",
        output_base_dir=tmp_path / "output",
    )


@pytest.fixture
def minimal_prompt_config(tmp_path: Path) -> PromptConfig:
    """Create minimal valid PromptConfig for tests."""
    return _make_prompt_config(tmp_path)


def _make_prompt_config(tmp_path: Path, **overrides) -> PromptConfig:
    """Helper to create PromptConfig with defaults + overrides."""
    defaults = {
        "version": "2.0",
        "name": "test_prompt",
        "prompt": "test prompt content",
        "source_file": tmp_path / "test.prompt.yaml",
        "generation": GenerationConfig(
            mode="combinatorial",
            seed_mode="progressive",
            seed=42,
            max_images=100,
        ),
        "output": OutputConfig(),
    }
    defaults.update(overrides)
    return PromptConfig(**defaults)


# ============================================================================
# Test: Session Name Resolution Priority
# ============================================================================


class TestSessionNameResolution:
    """Test session name resolution with different priority scenarios."""

    def test_priority_1_cli_override_wins(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """CLI --session-name override has highest priority."""
        # Setup: CLI has override
        cli_config = CLIConfig(
            **{**minimal_cli_config.__dict__, "session_name_override": "cli_override_session"}
        )

        # Setup: Prompt has session_name and name
        prompt_config = _make_prompt_config(
            tmp_path,
            name="prompt_name",
            output=OutputConfig(session_name="prompt_output_session"),
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, prompt_config)

        # Assert: CLI override wins
        assert session_config.session_name == "cli_override_session"

    def test_priority_2_prompt_output_session_name(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """prompt.output.session_name used if no CLI override."""
        # Setup: No CLI override
        cli_config = minimal_cli_config

        # Setup: Prompt has output.session_name and name
        prompt_config = _make_prompt_config(
            tmp_path,
            name="prompt_name",
            output=OutputConfig(session_name="prompt_output_session"),
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, prompt_config)

        # Assert: prompt.output.session_name wins
        assert session_config.session_name == "prompt_output_session"

    def test_priority_3_template_name(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """prompt.name used if no CLI override or output.session_name."""
        # Setup: No CLI override, no output.session_name
        cli_config = minimal_cli_config
        prompt_config = _make_prompt_config(
            tmp_path,
            name="prompt_name",
            output=OutputConfig(),  # No session_name
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, prompt_config)

        # Assert: prompt.name wins
        assert session_config.session_name == "prompt_name"

    def test_priority_4_template_filename_fallback(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Prompt filename used as fallback."""
        # Setup: No CLI override, no output.session_name, no prompt.name
        cli_config = minimal_cli_config
        prompt_config = _make_prompt_config(
            tmp_path,
            name=None,  # No name
            output=OutputConfig(),
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, prompt_config)

        # Assert: Template filename (stem) used
        assert session_config.session_name == minimal_cli_config.template_path.stem


# ============================================================================
# Test: Total Images Resolution
# ============================================================================


class TestTotalImagesResolution:
    """Test total images count resolution."""

    def test_cli_count_overrides_template(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """CLI --count overrides template default."""
        # Setup: CLI has explicit count
        cli_config = CLIConfig(
            **{**minimal_cli_config.__dict__, "count": 50}
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, minimal_prompt_config)

        # Assert: CLI count wins
        assert session_config.total_images == 50

    def test_default_when_no_cli_count(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Default value used when no CLI count specified."""
        # Setup: No CLI count
        cli_config = minimal_cli_config

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, minimal_prompt_config)

        # Assert: Default value (placeholder: 100)
        assert session_config.total_images == 100  # Current placeholder default


# ============================================================================
# Test: Seed Configuration Resolution
# ============================================================================


class TestSeedConfigurationResolution:
    """Test seed configuration resolution logic."""

    def test_cli_seeds_enables_sweep_mode(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """CLI --seeds flag enables seed-sweep mode."""
        # Setup: CLI has seeds
        cli_config = CLIConfig(
            **{**minimal_cli_config.__dict__, "seeds": "42,43,44"}
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, minimal_prompt_config)

        # Assert: Seed-sweep mode enabled
        assert session_config.seed_mode == "sweep"
        assert session_config.seed_list == [42, 43, 44]
        assert session_config.base_seed is None

    def test_template_seed_mode_used_when_no_cli_seeds(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Prompt seed_mode used when no CLI --seeds."""
        # Setup: No CLI seeds, prompt has seed_mode
        cli_config = minimal_cli_config
        prompt_config = _make_prompt_config(
            tmp_path,
            generation=GenerationConfig(
                mode="combinatorial",
                seed_mode="progressive",
                seed=42,
                max_images=100,
            ),
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, prompt_config)

        # Assert: Prompt seed_mode used
        assert session_config.seed_mode == "progressive"
        assert session_config.base_seed == 42
        assert session_config.seed_list is None

    def test_base_seed_none_when_template_seed_is_minus_one(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """base_seed is None when prompt.generation.seed == -1."""
        # Setup: Prompt seed = -1 (random)
        cli_config = minimal_cli_config
        prompt_config = _make_prompt_config(
            tmp_path,
            generation=GenerationConfig(
                mode="combinatorial",
                seed_mode="random",
                seed=-1,
                max_images=100,
            ),
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, prompt_config)

        # Assert: base_seed is None
        assert session_config.base_seed is None


# ============================================================================
# Test: Fixed Placeholders Parsing
# ============================================================================


class TestFixedPlaceholdersParsing:
    """Test fixed placeholders parsing from CLI --use-fixed."""

    def test_valid_single_placeholder(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Parse single fixed placeholder correctly."""
        # Setup: CLI has single fixed placeholder
        cli_config = CLIConfig(
            **{**minimal_cli_config.__dict__, "use_fixed": "Hair=blue"}
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, minimal_prompt_config)

        # Assert: Parsed correctly
        assert session_config.fixed_placeholders == {"Hair": "blue"}

    def test_valid_multiple_placeholders(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Parse multiple fixed placeholders correctly."""
        # Setup: CLI has multiple fixed placeholders
        cli_config = CLIConfig(
            **{**minimal_cli_config.__dict__, "use_fixed": "Hair=blue,Eyes=green,Outfit=casual"}
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, minimal_prompt_config)

        # Assert: All parsed correctly
        assert session_config.fixed_placeholders == {
            "Hair": "blue",
            "Eyes": "green",
            "Outfit": "casual",
        }

    def test_placeholder_with_spaces_trimmed(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Spaces around keys/values are trimmed."""
        # Setup: CLI has placeholders with spaces
        cli_config = CLIConfig(
            **{**minimal_cli_config.__dict__, "use_fixed": " Hair = blue , Eyes = green "}
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, minimal_prompt_config)

        # Assert: Spaces trimmed
        assert session_config.fixed_placeholders == {
            "Hair": "blue",
            "Eyes": "green",
        }

    def test_empty_fixed_string_returns_empty_dict(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Empty or None use_fixed returns empty dict."""
        # Setup: No fixed placeholders
        cli_config = CLIConfig(
            **{**minimal_cli_config.__dict__, "use_fixed": None}
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, minimal_prompt_config)

        # Assert: Empty dict
        assert session_config.fixed_placeholders == {}

    def test_invalid_format_missing_equals_raises_error(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Invalid format (missing '=') raises ValueError."""
        # Assert: Raises ValueError when creating CLIConfig with invalid use_fixed
        with pytest.raises(ValueError, match="Invalid fixed placeholder format"):
            cli_config = CLIConfig(
                **{**minimal_cli_config.__dict__, "use_fixed": "Hair:blue"}  # Wrong separator
            )


# ============================================================================
# Test: Annotations Enabled Detection
# ============================================================================


class TestAnnotationsEnabled:
    """Test annotations enabled detection from template config."""

    def test_annotations_enabled_when_true(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Annotations enabled when prompt.output.annotations.enabled = True."""
        # Setup: Prompt has annotations enabled
        cli_config = minimal_cli_config
        prompt_config = _make_prompt_config(
            tmp_path,
            output=OutputConfig(
                annotations=AnnotationsConfig(enabled=True),
            ),
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, prompt_config)

        # Assert: Annotations enabled
        assert session_config.annotations_enabled is True

    def test_annotations_disabled_when_false(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Annotations disabled when prompt.output.annotations.enabled = False."""
        # Setup: Prompt has annotations disabled
        cli_config = minimal_cli_config
        prompt_config = _make_prompt_config(
            tmp_path,
            output=OutputConfig(
                annotations=AnnotationsConfig(enabled=False),
            ),
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, prompt_config)

        # Assert: Annotations disabled
        assert session_config.annotations_enabled is False

    def test_annotations_disabled_when_not_configured(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """Annotations disabled when not configured in prompt."""
        # Setup: Prompt has no annotations config
        cli_config = minimal_cli_config
        prompt_config = _make_prompt_config(
            tmp_path,
            output=OutputConfig(),  # No annotations
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, prompt_config)

        # Assert: Annotations disabled (default)
        assert session_config.annotations_enabled is False


# ============================================================================
# Test: SessionConfig Properties and Validation
# ============================================================================


class TestSessionConfigProperties:
    """Test SessionConfig properties and validation."""

    def test_session_config_is_immutable(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """SessionConfig is immutable (frozen dataclass)."""
        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(minimal_cli_config, minimal_prompt_config)

        # Assert: Cannot modify attributes
        with pytest.raises(Exception):  # FrozenInstanceError
            session_config.session_name = "modified"  # type: ignore[misc]

    def test_session_path_computed_property(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """session_path is computed from output_dir / session_name."""
        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(minimal_cli_config, minimal_prompt_config)

        # Assert: session_path is correctly computed
        expected_path = minimal_cli_config.output_base_dir / session_config.session_name
        assert session_config.session_path == expected_path

    def test_manifest_path_computed_property(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """manifest_path is session_path / manifest.json."""
        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(minimal_cli_config, minimal_prompt_config)

        # Assert: manifest_path is correctly computed
        expected_path = session_config.session_path / "manifest.json"
        assert session_config.manifest_path == expected_path

    def test_is_seed_sweep_mode_true_when_seed_list_present(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """is_seed_sweep_mode() returns True when seed_list is present."""
        # Setup: CLI has seeds
        cli_config = CLIConfig(
            **{**minimal_cli_config.__dict__, "seeds": "42,43"}
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, minimal_prompt_config)

        # Assert: Seed sweep mode detected
        assert session_config.is_seed_sweep_mode() is True

    def test_is_seed_sweep_mode_false_when_no_seed_list(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """is_seed_sweep_mode() returns False when no seed_list."""
        # Setup: No CLI seeds
        cli_config = minimal_cli_config

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, minimal_prompt_config)

        # Assert: Not seed sweep mode
        assert session_config.is_seed_sweep_mode() is False


# ============================================================================
# Test: Edge Cases and Error Handling
# ============================================================================


class TestEdgeCasesAndErrors:
    """Test edge cases and error handling."""

    def test_all_fields_populated_correctly(
        self,
        global_config: GlobalConfig,
        minimal_cli_config: CLIConfig,
        minimal_prompt_config: PromptConfig,
        tmp_path: Path,
    ) -> None:
        """All SessionConfig fields are populated correctly."""
        # Setup: Full configuration
        cli_config = CLIConfig(
            **{
                **minimal_cli_config.__dict__,
                "count": 50,
                "dry_run": True,
                "theme_name": "cyberpunk",
                "style": "anime",
                "use_fixed": "Hair=blue",
                "seeds": "42,43",
            }
        )

        prompt_config = _make_prompt_config(
            tmp_path,
            name="test_prompt",
            generation=GenerationConfig(
                mode="random",
                seed_mode="progressive",
                seed=123,
                max_images=100,
            ),
            output=OutputConfig(
                session_name="prompt_session",
                annotations=AnnotationsConfig(enabled=True),
            ),
        )

        # Build
        builder = SessionConfigBuilder(global_config)
        session_config = builder.build(cli_config, prompt_config)

        # Assert: All fields populated
        assert session_config.session_name == "prompt_session"
        assert session_config.output_dir == minimal_cli_config.output_base_dir
        assert session_config.template_path == minimal_cli_config.template_path
        assert session_config.prompt_config == prompt_config
        assert session_config.total_images == 50
        assert session_config.generation_mode == "random"
        assert session_config.seed_mode == "sweep"
        assert session_config.seed_list == [42, 43]
        assert session_config.api_url == "http://127.0.0.1:7860"
        assert session_config.dry_run is True
        assert session_config.theme_name == "cyberpunk"
        assert session_config.style == "anime"
        assert session_config.fixed_placeholders == {"Hair": "blue"}
        assert session_config.skip_validation is False
        assert session_config.annotations_enabled is True
