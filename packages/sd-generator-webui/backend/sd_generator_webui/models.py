from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SeedMode(str, Enum):
    FIXED = "fixed"
    PROGRESSIVE = "progressive"
    RANDOM = "random"


class GenerationMode(str, Enum):
    COMBINATORIAL = "combinatorial"
    RANDOM = "random"


class GenerationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationRequest(BaseModel):
    prompt_template: str = Field(..., description="Template de prompt avec placeholders {Name}")
    negative_prompt: str = Field(default="", description="Prompt négatif")
    variation_files: Dict[str, str] = Field(..., description="Mapping placeholder -> fichier de variations")

    # Generation parameters
    num_images: int = Field(default=1, ge=1, le=10, description="Nombre d'images à générer")
    generation_mode: GenerationMode = Field(default=GenerationMode.RANDOM)
    seed_mode: SeedMode = Field(default=SeedMode.RANDOM)
    seed: Optional[int] = Field(default=None, description="Seed de base (si seed_mode=fixed ou progressive)")

    # SD WebUI parameters
    steps: int = Field(default=20, ge=1, le=150)
    cfg_scale: float = Field(default=7.0, ge=1.0, le=30.0)
    width: int = Field(default=512, ge=64, le=2048)
    height: int = Field(default=512, ge=64, le=2048)
    sampler_name: str = Field(default="Euler a")

    # Session
    session_name: Optional[str] = Field(default=None, description="Nom de session personnalisé")


class ImageInfo(BaseModel):
    filename: str
    path: str
    thumbnail_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    file_size: int
    dimensions: Optional[tuple[int, int]] = None


class GenerationJob(BaseModel):
    job_id: str
    status: GenerationStatus
    request: GenerationRequest
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    current_image: int = Field(default=0)
    total_images: int = Field(default=0)
    generated_images: List[str] = Field(default_factory=list)


class GenerationResponse(BaseModel):
    job_id: str
    status: GenerationStatus
    message: str


class ImageListResponse(BaseModel):
    images: List[ImageInfo]
    total_count: int
    page: int
    page_size: int


class UserInfo(BaseModel):
    guid: str
    is_admin: bool
    is_read_only: bool
    can_generate: bool
    can_view: bool


class UserRating(str, Enum):
    """User rating for a session."""
    LIKE = "like"
    DISLIKE = "dislike"


class SessionMetadata(BaseModel):
    """Metadata for a session (user ratings, flags, tags)."""
    session_id: str = Field(..., description="Session folder name")
    session_path: str = Field(..., description="Full path to session folder")

    # User flags
    is_test: bool = Field(default=False, description="Marked as test session")
    is_complete: bool = Field(default=True, description="Session is complete")
    is_favorite: bool = Field(default=False, description="Marked as favorite")

    # User ratings and notes
    user_rating: Optional[UserRating] = Field(default=None, description="Like/dislike")
    user_note: Optional[str] = Field(default=None, description="User notes")
    tags: List[str] = Field(default_factory=list, description="User tags")

    # Auto-metadata (flexible JSON)
    auto_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Auto-extracted metadata")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SessionMetadataUpdate(BaseModel):
    """Request model for updating session metadata."""
    is_test: Optional[bool] = None
    is_complete: Optional[bool] = None
    is_favorite: Optional[bool] = None
    user_rating: Optional[UserRating] = None
    user_note: Optional[str] = None
    tags: Optional[List[str]] = None


class SessionWithMetadata(BaseModel):
    """Session info with metadata attached."""
    # Session info
    name: str
    path: str
    created_at: datetime
    image_count: Optional[int] = None

    # Metadata
    metadata: Optional[SessionMetadata] = None
