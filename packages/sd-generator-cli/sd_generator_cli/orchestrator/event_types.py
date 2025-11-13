"""Event types for session lifecycle and CLI output management."""

from enum import Enum


class EventType(Enum):
    """Event types emitted during generation session lifecycle.

    Events are emitted by various components and handled by SessionEventCollector
    for formatted CLI output (progress bars, stats, errors, success messages).

    Event naming convention:
    - COMPONENT_ACTION (e.g., VALIDATION_START, MANIFEST_CREATED)
    - Use present tense for ongoing actions (GENERATING, LOADING)
    - Use past tense for completed actions (GENERATED, LOADED)
    """

    # ========================================================================
    # Configuration & Validation Events
    # ========================================================================
    SESSION_CONFIG_BUILT = "session_config_built"
    """SessionConfig was successfully built from CLI + template configs."""

    VALIDATION_START = "validation_start"
    """Template validation started."""

    VALIDATION_SUCCESS = "validation_success"
    """Template validation passed."""

    VALIDATION_ERROR = "validation_error"
    """Template validation failed (data: errors list)."""

    # ========================================================================
    # Template Loading Events
    # ========================================================================
    TEMPLATE_LOADING = "template_loading"
    """Template loading started."""

    TEMPLATE_LOADED = "template_loaded"
    """Template loaded and resolved (data: stats)."""

    TEMPLATE_LOAD_ERROR = "template_load_error"
    """Template loading failed (data: error)."""

    # ========================================================================
    # Context & Prompt Generation Events
    # ========================================================================
    CONTEXT_ENRICHED = "context_enriched"
    """Context enriched with fixed placeholders and seed sweep."""

    PROMPT_GENERATION_START = "prompt_generation_start"
    """Prompt generation started."""

    PROMPT_STATS = "prompt_stats"
    """Prompt statistics ready (data: stats dict with combinations, variations)."""

    PROMPT_GENERATION_ERROR = "prompt_generation_error"
    """Prompt generation failed (data: error)."""

    # ========================================================================
    # Session & API Setup Events
    # ========================================================================
    SESSION_CREATED = "session_created"
    """Session directory created (data: session_path)."""

    API_CONNECTION_TEST_START = "api_connection_test_start"
    """Testing API connection."""

    API_CONNECTION_SUCCESS = "api_connection_success"
    """API connection successful."""

    API_CONNECTION_ERROR = "api_connection_error"
    """API connection failed (data: error, api_url)."""

    # ========================================================================
    # Manifest Events
    # ========================================================================
    MANIFEST_RUNTIME_FETCH_START = "manifest_runtime_fetch_start"
    """Fetching runtime info from SD API."""

    MANIFEST_RUNTIME_FETCH_SUCCESS = "manifest_runtime_fetch_success"
    """Runtime info fetched successfully (data: info dict)."""

    MANIFEST_RUNTIME_FETCH_ERROR = "manifest_runtime_fetch_error"
    """Runtime info fetch failed (data: error)."""

    MANIFEST_CREATED = "manifest_created"
    """Manifest.json created (data: manifest_path)."""

    MANIFEST_UPDATED = "manifest_updated"
    """Manifest updated incrementally (data: image_index)."""

    MANIFEST_FINALIZED = "manifest_finalized"
    """Manifest finalized with final status (data: status='completed'/'aborted')."""

    # ========================================================================
    # Annotation Worker Events
    # ========================================================================
    ANNOTATION_WORKER_START = "annotation_worker_start"
    """Annotation worker started."""

    ANNOTATION_WORKER_STOPPED = "annotation_worker_stopped"
    """Annotation worker stopped (data: pending_count)."""

    ANNOTATION_JOB_SUBMITTED = "annotation_job_submitted"
    """Image submitted to annotation queue (data: image_path)."""

    # ========================================================================
    # Prompt Config Conversion Events
    # ========================================================================
    PROMPT_CONFIGS_READY = "prompt_configs_ready"
    """PromptConfig objects ready for generation (data: count)."""

    # ========================================================================
    # Image Generation Events
    # ========================================================================
    IMAGE_GENERATION_START = "image_generation_start"
    """Image generation batch started (data: total_images)."""

    IMAGE_GENERATION_COMPLETE = "image_generation_complete"
    """Image generation batch completed (data: success_count, total_count, failed_count)."""

    GENERATION_START = "generation_start"
    """Batch generation started (data: total_images)."""

    IMAGE_START = "image_start"
    """Single image generation started (data: index, prompt_preview)."""

    IMAGE_SUCCESS = "image_success"
    """Single image generated successfully (data: index, path, seed)."""

    IMAGE_ERROR = "image_error"
    """Single image generation failed (data: index, error)."""

    GENERATION_PROGRESS = "generation_progress"
    """Generation progress update (data: current, total, percentage)."""

    # ========================================================================
    # Finalization Events
    # ========================================================================
    GENERATION_COMPLETE = "generation_complete"
    """Generation completed successfully (data: summary_stats)."""

    GENERATION_ABORTED = "generation_aborted"
    """Generation aborted due to error (data: error, partial_results)."""

    # ========================================================================
    # General Events
    # ========================================================================
    DEBUG = "debug"
    """Debug information (data: message) - only shown in verbose mode."""

    WARNING = "warning"
    """Warning message (data: message)."""

    INFO = "info"
    """Informational message (data: message)."""
