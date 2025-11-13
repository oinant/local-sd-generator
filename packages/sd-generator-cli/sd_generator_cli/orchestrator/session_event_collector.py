"""SessionEventCollector - event-driven CLI output management."""

from typing import Any, Callable, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .event_types import EventType


class SessionEventCollector:
    """Collects session events and produces formatted CLI output.

    This class implements event-driven output management for the generation session.
    Components emit events (via .emit()), and this collector handles formatting
    and displaying them to the user.

    Benefits:
    - Single responsibility: ALL CLI output in one place
    - Components are decoupled from Console (just emit events)
    - Easy to test (mock SessionEventCollector)
    - Easy to extend (add new event types without touching components)
    - Can easily implement quiet mode, JSON output, logging, etc.

    Example:
        >>> console = Console()
        >>> collector = SessionEventCollector(console, verbose=False)
        >>> collector.emit(EventType.VALIDATION_SUCCESS)
        >>> collector.emit(EventType.PROMPT_STATS, {"total": 100, "variations": 5})
    """

    def __init__(self, console: Console, verbose: bool = False):
        """Initialize event collector.

        Args:
            console: Rich Console instance for output
            verbose: If True, show debug events and extra details
        """
        self.console = console
        self.verbose = verbose
        self._progress: Optional[Progress] = None
        self._progress_task_id: Optional[int] = None

    def emit(self, event_type: EventType, data: Optional[dict[str, Any]] = None) -> None:
        """Emit a session event and handle output formatting.

        Args:
            event_type: Type of event to emit
            data: Optional event data (context-dependent)
        """
        handler = self._get_handler(event_type)
        handler(data or {})

    def _get_handler(self, event_type: EventType) -> Callable[[dict[str, Any]], None]:
        """Map event type to handler method.

        Args:
            event_type: Event type

        Returns:
            Handler function for this event type
        """
        handlers: dict[EventType, Callable[[dict[str, Any]], None]] = {
            # Configuration & Validation
            EventType.SESSION_CONFIG_BUILT: self._handle_session_config_built,
            EventType.VALIDATION_START: self._handle_validation_start,
            EventType.VALIDATION_SUCCESS: self._handle_validation_success,
            EventType.VALIDATION_ERROR: self._handle_validation_error,
            # Template Loading
            EventType.TEMPLATE_LOADING: self._handle_template_loading,
            EventType.TEMPLATE_LOADED: self._handle_template_loaded,
            EventType.TEMPLATE_LOAD_ERROR: self._handle_template_load_error,
            # Context & Prompts
            EventType.CONTEXT_ENRICHED: self._handle_context_enriched,
            EventType.PROMPT_GENERATION_START: self._handle_prompt_generation_start,
            EventType.PROMPT_STATS: self._handle_prompt_stats,
            EventType.PROMPT_GENERATION_ERROR: self._handle_prompt_generation_error,
            # Session & API
            EventType.SESSION_CREATED: self._handle_session_created,
            EventType.API_CONNECTION_TEST_START: self._handle_api_connection_test_start,
            EventType.API_CONNECTION_SUCCESS: self._handle_api_connection_success,
            EventType.API_CONNECTION_ERROR: self._handle_api_connection_error,
            # Manifest
            EventType.MANIFEST_CREATED: self._handle_manifest_created,
            EventType.MANIFEST_FINALIZED: self._handle_manifest_finalized,
            # Annotation Worker
            EventType.ANNOTATION_WORKER_START: self._handle_annotation_worker_start,
            EventType.ANNOTATION_WORKER_STOPPED: self._handle_annotation_worker_stopped,
            # Image Generation
            EventType.GENERATION_START: self._handle_generation_start,
            EventType.IMAGE_SUCCESS: self._handle_image_success,
            EventType.IMAGE_ERROR: self._handle_image_error,
            EventType.GENERATION_PROGRESS: self._handle_generation_progress,
            # Finalization
            EventType.GENERATION_COMPLETE: self._handle_generation_complete,
            EventType.GENERATION_ABORTED: self._handle_generation_aborted,
            # General
            EventType.DEBUG: self._handle_debug,
            EventType.WARNING: self._handle_warning,
            EventType.INFO: self._handle_info,
        }
        return handlers.get(event_type, self._handle_unknown)

    # ========================================================================
    # Configuration & Validation Handlers
    # ========================================================================

    def _handle_session_config_built(self, data: dict[str, Any]) -> None:
        if self.verbose:
            self.console.print("[dim]✓ Session configuration built[/dim]")

    def _handle_validation_start(self, data: dict[str, Any]) -> None:
        if self.verbose:
            self.console.print("[dim]Validating template schema...[/dim]")

    def _handle_validation_success(self, data: dict[str, Any]) -> None:
        self.console.print("✓ Template validation passed", style="green")

    def _handle_validation_error(self, data: dict[str, Any]) -> None:
        errors = data.get("errors", [])
        self.console.print("[red]✗ Template validation failed:[/red]")
        for error in errors:
            self.console.print(f"  • {error}", style="red")

    # ========================================================================
    # Template Loading Handlers
    # ========================================================================

    def _handle_template_loading(self, data: dict[str, Any]) -> None:
        if self.verbose:
            self.console.print("[dim]Loading template...[/dim]")

    def _handle_template_loaded(self, data: dict[str, Any]) -> None:
        self.console.print("✓ Template loaded", style="green")
        if self.verbose and "stats" in data:
            stats = data["stats"]
            self.console.print(f"[dim]  Placeholders: {stats.get('placeholders', 'N/A')}[/dim]")

    def _handle_template_load_error(self, data: dict[str, Any]) -> None:
        error = data.get("error", "Unknown error")
        self.console.print(f"[red]✗ Template loading failed: {error}[/red]")

    # ========================================================================
    # Context & Prompt Handlers
    # ========================================================================

    def _handle_context_enriched(self, data: dict[str, Any]) -> None:
        if self.verbose:
            self.console.print("[dim]✓ Context enriched with fixed placeholders[/dim]")

    def _handle_prompt_generation_start(self, data: dict[str, Any]) -> None:
        if self.verbose:
            self.console.print("[dim]Generating prompts...[/dim]")

    def _handle_prompt_stats(self, data: dict[str, Any]) -> None:
        stats = data.get("stats", {})
        self.console.print("\n[bold]Generation Statistics:[/bold]")
        self.console.print(f"  Total combinations: {stats.get('total_combinations', 0):,}")
        self.console.print(f"  Variations loaded: {stats.get('variations_count', 0)}")
        if "mode" in stats:
            self.console.print(f"  Generation mode: {stats['mode']}")

    def _handle_prompt_generation_error(self, data: dict[str, Any]) -> None:
        error = data.get("error", "Unknown error")
        self.console.print(f"[red]✗ Prompt generation failed: {error}[/red]")

    # ========================================================================
    # Session & API Handlers
    # ========================================================================

    def _handle_session_created(self, data: dict[str, Any]) -> None:
        session_path = data.get("session_path", "N/A")
        self.console.print(f"[cyan]Session:[/cyan] {session_path}")

    def _handle_api_connection_test_start(self, data: dict[str, Any]) -> None:
        if self.verbose:
            self.console.print("[dim]Testing API connection...[/dim]")

    def _handle_api_connection_success(self, data: dict[str, Any]) -> None:
        self.console.print("✓ API connection successful", style="green")

    def _handle_api_connection_error(self, data: dict[str, Any]) -> None:
        error = data.get("error", "Unknown error")
        api_url = data.get("api_url", "N/A")
        self.console.print(f"[red]✗ API connection failed ({api_url}): {error}[/red]")

    # ========================================================================
    # Manifest Handlers
    # ========================================================================

    def _handle_manifest_created(self, data: dict[str, Any]) -> None:
        manifest_path = data.get("manifest_path", "N/A")
        if self.verbose:
            self.console.print(f"[dim]✓ Manifest created: {manifest_path}[/dim]")

    def _handle_manifest_finalized(self, data: dict[str, Any]) -> None:
        status = data.get("status", "unknown")
        if self.verbose:
            self.console.print(f"[dim]✓ Manifest finalized (status: {status})[/dim]")

    # ========================================================================
    # Annotation Worker Handlers
    # ========================================================================

    def _handle_annotation_worker_start(self, data: dict[str, Any]) -> None:
        if self.verbose:
            self.console.print("[dim]✓ Annotation worker started[/dim]")

    def _handle_annotation_worker_stopped(self, data: dict[str, Any]) -> None:
        pending = data.get("pending_count", 0)
        if self.verbose:
            self.console.print(f"[dim]✓ Annotation worker stopped (pending: {pending})[/dim]")

    # ========================================================================
    # Image Generation Handlers
    # ========================================================================

    def _handle_generation_start(self, data: dict[str, Any]) -> None:
        total = data.get("total_images", 0)
        self.console.print(f"\n[bold]Generating {total} images...[/bold]\n")

        # Start progress bar
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )
        self._progress.start()
        self._progress_task_id = self._progress.add_task("Generating...", total=total)

    def _handle_image_success(self, data: dict[str, Any]) -> None:
        if self._progress and self._progress_task_id is not None:
            self._progress.update(self._progress_task_id, advance=1)

    def _handle_image_error(self, data: dict[str, Any]) -> None:
        idx = data.get("index", "?")
        error = data.get("error", "Unknown error")
        self.console.print(f"[red]✗ Image {idx} failed: {error}[/red]")
        if self._progress and self._progress_task_id is not None:
            self._progress.update(self._progress_task_id, advance=1)

    def _handle_generation_progress(self, data: dict[str, Any]) -> None:
        # Progress is handled by IMAGE_SUCCESS, but this could be used for checkpoints
        pass

    # ========================================================================
    # Finalization Handlers
    # ========================================================================

    def _handle_generation_complete(self, data: dict[str, Any]) -> None:
        # Stop progress bar
        if self._progress:
            self._progress.stop()
            self._progress = None
            self._progress_task_id = None

        summary = data.get("summary_stats", {})
        self.console.print("\n[bold green]✓ Generation complete![/bold green]")
        if summary:
            total = summary.get("total", 0)
            success = summary.get("success", 0)
            failed = summary.get("failed", 0)
            self.console.print(f"  Total: {total} | Success: {success} | Failed: {failed}")

    def _handle_generation_aborted(self, data: dict[str, Any]) -> None:
        # Stop progress bar
        if self._progress:
            self._progress.stop()
            self._progress = None
            self._progress_task_id = None

        error = data.get("error", "Unknown error")
        self.console.print(f"\n[bold red]✗ Generation aborted: {error}[/bold red]")

    # ========================================================================
    # General Handlers
    # ========================================================================

    def _handle_debug(self, data: dict[str, Any]) -> None:
        if self.verbose:
            message = data.get("message", "")
            self.console.print(f"[dim]DEBUG: {message}[/dim]")

    def _handle_warning(self, data: dict[str, Any]) -> None:
        message = data.get("message", "")
        self.console.print(f"[yellow]⚠ {message}[/yellow]")

    def _handle_info(self, data: dict[str, Any]) -> None:
        message = data.get("message", "")
        self.console.print(f"[cyan]ℹ {message}[/cyan]")

    def _handle_unknown(self, data: dict[str, Any]) -> None:
        if self.verbose:
            self.console.print(f"[dim]Unknown event: {data}[/dim]")
