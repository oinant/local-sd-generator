"""
Manifest data model for SD Generator sessions.

The manifest.json file is the source of truth for session metadata.
It contains:
- Generation configuration (snapshot)
- Generated images list
- Session status (FSM: ongoing → completed/aborted)
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """
    Session status FSM.

    State transitions:
    - ongoing → completed (all images generated successfully)
    - ongoing → aborted (interrupted by user or error)
    """

    ONGOING = "ongoing"
    COMPLETED = "completed"
    ABORTED = "aborted"


class ImageEntry(BaseModel):
    """Entry for a single generated image in the manifest."""

    filename: str
    seed: int
    prompt: str
    negative_prompt: str
    applied_variations: Dict[str, str] = Field(default_factory=dict)


class VariationInfo(BaseModel):
    """Information about variations for a placeholder."""

    available: List[str] = Field(default_factory=list)
    used: List[str] = Field(default_factory=list)


class GenerationParams(BaseModel):
    """Generation parameters (mode, seed, etc.)."""

    mode: str = "unknown"
    seed_mode: str = "unknown"
    seed_base: int = 42
    max_images: int = 0


class APIParams(BaseModel):
    """Stable Diffusion API parameters."""

    width: int
    height: int
    steps: int
    cfg_scale: float
    sampler_name: str
    scheduler: Optional[str] = None


class ResolvedTemplate(BaseModel):
    """Resolved prompt template."""

    prompt: str
    negative: str


class RuntimeInfo(BaseModel):
    """Runtime information (model checkpoint, etc.)."""

    sd_model_checkpoint: Optional[str] = None


class InferenceInfo(BaseModel):
    """Information about manifest inference (for legacy sessions)."""

    source: str
    confidence: str
    errors: List[str] = Field(default_factory=list)


class SnapshotModel(BaseModel):
    """
    Snapshot of generation configuration.

    Contains all parameters used for generation at the time the session started.
    """

    version: str
    timestamp: str
    inference_info: Optional[InferenceInfo] = None
    runtime_info: RuntimeInfo
    resolved_template: ResolvedTemplate
    generation_params: GenerationParams
    api_params: APIParams
    variations: Dict[str, VariationInfo] = Field(default_factory=dict)


class ManifestModel(BaseModel):
    """
    Complete manifest model for a session.

    The manifest.json is the source of truth for:
    - Session configuration (snapshot)
    - Generated images list
    - Session status (FSM)

    This model is shared between:
    - CLI (writes manifest)
    - Watchdog (reads manifest → updates DB)
    - WebUI (reads manifest for display)
    """

    snapshot: SnapshotModel
    images: List[ImageEntry] = Field(default_factory=list)

    # FSM status field
    status: SessionStatus = Field(
        default=SessionStatus.ONGOING,
        description="Session status: ongoing → completed|aborted",
    )

    # Computed fields
    images_requested: Optional[int] = Field(
        default=None,
        description="Total number of images requested (from generation_params.max_images)",
    )

    images_actual: Optional[int] = Field(
        default=None,
        description="Actual number of images generated (len(images))",
    )

    def update_image_counts(self) -> None:
        """Update images_requested and images_actual from snapshot and images list."""
        self.images_requested = self.snapshot.generation_params.max_images
        self.images_actual = len(self.images)

    class Config:
        """Pydantic config."""

        use_enum_values = True  # Serialize enums as strings
