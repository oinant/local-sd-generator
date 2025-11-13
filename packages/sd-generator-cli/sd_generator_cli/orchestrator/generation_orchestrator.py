"""GenerationOrchestrator - high-level orchestration of generation workflow."""

from pathlib import Path
from typing import Optional

from rich.console import Console

from ..config.global_config import GlobalConfig
from .cli_config import CLIConfig
from .session_config import SessionConfig
from .session_config_builder import SessionConfigBuilder
from .session_event_collector import SessionEventCollector
from .event_types import EventType


class GenerationOrchestrator:
    """Orchestrates the complete image generation workflow.

    This class coordinates all phases of generation:
    1. Configuration building (CLI + Prompt → SessionConfig)
    2. Template validation
    3. Template loading and resolution
    4. Prompt generation
    5. Manifest creation
    6. API connection testing
    7. Image generation
    8. Manifest finalization

    The orchestrator uses SessionEventCollector for all CLI output,
    ensuring clean separation between business logic and presentation.

    Example:
        >>> orchestrator = GenerationOrchestrator(
        ...     global_config=global_config,
        ...     console=console
        ... )
        >>> orchestrator.orchestrate(
        ...     template_path=Path("prompt.yaml"),
        ...     count=100,
        ...     api_url="http://127.0.0.1:7860",
        ...     dry_run=False
        ... )
    """

    def __init__(
        self,
        global_config: GlobalConfig,
        console: Console,
        verbose: bool = False
    ):
        """Initialize orchestrator with global config and console.

        Args:
            global_config: Global configuration (sdgen_config.json)
            console: Rich Console for output
            verbose: Enable verbose output (debug events)
        """
        self.global_config = global_config
        self.console = console
        self.verbose = verbose

        # Initialize event collector for output management
        self.events = SessionEventCollector(console, verbose=verbose)

        # Initialize config builder
        self.config_builder = SessionConfigBuilder(global_config)

    def orchestrate(
        self,
        template_path: Path,
        count: Optional[int],
        api_url: str,
        dry_run: bool,
        session_name_override: Optional[str] = None,
        theme_name: Optional[str] = None,
        theme_file: Optional[Path] = None,
        style: str = "default",
        skip_validation: bool = False,
        use_fixed: Optional[str] = None,
        seeds: Optional[str] = None
    ) -> None:
        """Execute complete generation workflow.

        This is the main entry point that coordinates all phases of generation.
        It mirrors the signature of _generate() for easy migration.

        Args:
            template_path: Path to prompt YAML file
            count: Number of images to generate (overrides template)
            api_url: Stable Diffusion API URL
            dry_run: If True, generate prompts but don't call API
            session_name_override: Override session name (CLI --session-name)
            theme_name: Theme name (CLI --theme)
            theme_file: Path to theme file (CLI --theme-file)
            style: Style variant (CLI --style)
            skip_validation: Skip template validation (CLI --skip-validation)
            use_fixed: Fixed placeholder values (CLI --use-fixed)
            seeds: Seed sweep list (CLI --seeds)

        Raises:
            SystemExit: On validation errors or critical failures
        """
        try:
            # Phase 1: Build unified session configuration
            session_config = self._build_session_config(
                template_path=template_path,
                count=count,
                api_url=api_url,
                dry_run=dry_run,
                session_name_override=session_name_override,
                theme_name=theme_name,
                style=style,
                skip_validation=skip_validation,
                use_fixed=use_fixed,
                seeds=seeds
            )

            # Phase 2: Validate template (unless skipped)
            if not skip_validation:
                self._validate_template(session_config)

            # Phase 3: Test API connection early (unless dry-run)
            # This fails fast before expensive prompt generation
            if not dry_run:
                self._test_api_connection(session_config)

            # Phase 4: Load and resolve template
            prompt_config = self._load_and_resolve(session_config, theme_file)

            # Phase 5: Generate prompts
            prompts, stats = self._generate_prompts(session_config, prompt_config)

            # Phase 6: Prepare manifest
            self._prepare_manifest(session_config, prompt_config, prompts, stats)

            # Phase 7: Run generation
            self._run_generation(session_config, prompts)

            # Phase 8: Finalize manifest
            self._finalize_manifest(session_config, status="completed")

        except KeyboardInterrupt:
            self.events.emit(EventType.GENERATION_ABORTED, {"error": "User interrupted"})
            self._finalize_manifest(session_config, status="aborted")
            raise SystemExit(1)
        except Exception as e:
            self.events.emit(EventType.GENERATION_ABORTED, {"error": str(e)})
            self._finalize_manifest(session_config, status="aborted")
            raise

    # ========================================================================
    # Phase 1: Configuration
    # ========================================================================

    def _build_session_config(
        self,
        template_path: Path,
        count: Optional[int],
        api_url: str,
        dry_run: bool,
        session_name_override: Optional[str],
        theme_name: Optional[str],
        style: str,
        skip_validation: bool,
        use_fixed: Optional[str],
        seeds: Optional[str]
    ) -> SessionConfig:
        """Build unified SessionConfig from CLI args and template.

        This phase:
        - Parses CLI arguments into CLIConfig
        - Loads PromptConfig from template YAML (via V2Pipeline)
        - Builds unified SessionConfig with priority resolution

        Returns:
            SessionConfig: Unified immutable configuration
        """
        # Step 1: Create CLIConfig from CLI arguments
        cli_config = CLIConfig(
            template_path=template_path,
            api_url=api_url,
            output_base_dir=self.global_config.output_dir,
            count=count,
            dry_run=dry_run,
            session_name_override=session_name_override,
            theme_name=theme_name,
            style=style,
            skip_validation=skip_validation,
            use_fixed=use_fixed,
            seeds=seeds
        )

        # Step 2: Load PromptConfig from template (TODO: needs V2Pipeline integration)
        # For now, this will be implemented when we integrate with template loading
        # prompt_config = self._load_prompt_config(template_path)

        # Step 3: Build unified SessionConfig
        # session_config = self.config_builder.build(cli_config, prompt_config)

        # Step 4: Emit event
        # self.events.emit(EventType.SESSION_CONFIG_BUILT)

        # return session_config

        # Temporary placeholder until we implement template loading
        raise NotImplementedError(
            "Phase 1: Configuration building requires V2Pipeline integration"
        )

    # ========================================================================
    # Phase 2: Validation
    # ========================================================================

    def _validate_template(self, session_config: SessionConfig) -> None:
        """Validate template schema.

        This phase:
        - Validates YAML against schema
        - Emits VALIDATION_SUCCESS or VALIDATION_ERROR events
        - Exits on validation failure

        Args:
            session_config: Session configuration
        """
        # TODO: Implement in next step
        # 1. Use TemplateValidator to validate
        # 2. Emit appropriate events
        raise NotImplementedError("Phase 2: Template validation")

    # ========================================================================
    # Phase 3: API Connection (Early Fail-Fast)
    # ========================================================================

    def _test_api_connection(self, session_config: SessionConfig) -> None:
        """Test connection to Stable Diffusion API.

        This phase runs EARLY (before prompt generation) to fail fast.
        No point generating prompts if the API is unreachable.

        This phase:
        - Tests API connectivity
        - Emits API_CONNECTION_SUCCESS or API_CONNECTION_ERROR events
        - Exits on connection failure

        Args:
            session_config: Session configuration
        """
        # TODO: Implement in next step
        # 1. Create SDAPIClient
        # 2. Test connection
        # 3. Emit API_CONNECTION_* events
        raise NotImplementedError("Phase 3: API connection test")

    # ========================================================================
    # Phase 4: Loading & Resolution
    # ========================================================================

    def _load_and_resolve(
        self,
        session_config: SessionConfig,
        theme_file: Optional[Path]
    ):
        """Load and resolve template with theme/style.

        This phase:
        - Loads template from path
        - Applies theme and style
        - Resolves inheritance and imports
        - Returns PromptConfig

        Args:
            session_config: Session configuration
            theme_file: Optional theme file path

        Returns:
            PromptConfig: Resolved prompt configuration
        """
        # TODO: Implement in next step
        # 1. Use V2Pipeline to load and resolve
        # 2. Emit TEMPLATE_LOADED events
        raise NotImplementedError("Phase 3: Template loading")

    # ========================================================================
    # Phase 5: Prompt Generation
    # ========================================================================

    def _generate_prompts(self, session_config: SessionConfig, prompt_config):
        """Generate prompts from resolved template.

        This phase:
        - Generates prompts (combinatorial or random)
        - Computes statistics
        - Emits PROMPT_STATS events

        Args:
            session_config: Session configuration
            prompt_config: Resolved prompt configuration

        Returns:
            Tuple of (prompts, stats)
        """
        # TODO: Implement in next step
        # 1. Use PromptGenerator to generate prompts
        # 2. Emit PROMPT_GENERATION_START, PROMPT_STATS events
        raise NotImplementedError("Phase 5: Prompt generation")

    # ========================================================================
    # Phase 6: Manifest Preparation
    # ========================================================================

    def _prepare_manifest(
        self,
        session_config: SessionConfig,
        prompt_config,
        prompts: list,
        stats: dict
    ) -> None:
        """Prepare and initialize manifest.

        This phase:
        - Builds manifest snapshot
        - Initializes manifest.json with 'ongoing' status
        - Emits MANIFEST_CREATED events

        Args:
            session_config: Session configuration
            prompt_config: Resolved prompt configuration
            prompts: Generated prompts
            stats: Prompt generation statistics
        """
        # TODO: Implement in next step
        # 1. Use ManifestBuilder to build snapshot
        # 2. Use ManifestManager to initialize manifest
        # 3. Emit MANIFEST_CREATED events
        raise NotImplementedError("Phase 6: Manifest preparation")

    # ========================================================================
    # Phase 7: Generation
    # ========================================================================

    def _run_generation(
        self,
        session_config: SessionConfig,
        prompts: list
    ) -> None:
        """Run image generation.

        This phase:
        - Creates API components (client, session manager, etc.)
        - Starts annotation worker if enabled
        - Executes batch generation
        - Updates manifest incrementally
        - Emits GENERATION_START, IMAGE_SUCCESS/ERROR events

        Args:
            session_config: Session configuration
            prompts: List of prompts to generate
        """
        # TODO: Implement in next step
        # 1. Create API components
        # 2. Start annotation worker
        # 3. Run batch generation with progress
        # 4. Emit GENERATION_* events
        raise NotImplementedError("Phase 7: Image generation")

    # ========================================================================
    # Phase 8: Finalization
    # ========================================================================

    def _finalize_manifest(
        self,
        session_config: SessionConfig,
        status: str
    ) -> None:
        """Finalize manifest with status.

        This phase:
        - Updates manifest status (completed/aborted)
        - Emits MANIFEST_FINALIZED event

        Args:
            session_config: Session configuration
            status: Final status ("completed" or "aborted")
        """
        # TODO: Implement in next step
        # 1. Use ManifestManager to finalize
        # 2. Emit MANIFEST_FINALIZED event
        raise NotImplementedError("Phase 8: Manifest finalization")
