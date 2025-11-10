"""
Session Statistics Data Models.

This module contains the SessionStats dataclass.
Separated from services to avoid circular imports with repositories.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class SessionStats:
    """Calculated statistics for a session."""

    # Identity
    session_name: str

    # Generation info
    sd_model: Optional[str] = None
    sampler_name: Optional[str] = None
    scheduler: Optional[str] = None
    cfg_scale: Optional[float] = None
    steps: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None

    # Images
    images_requested: int = 0
    images_actual: int = 0
    completion_percent: float = 0.0

    # Placeholders & Variations
    placeholders_count: int = 0
    placeholders: Optional[List[str]] = None
    variations_theoretical: int = 0
    variations_summary: Optional[Dict[str, int]] = None  # {placeholder: count}

    # Session type
    session_type: str = "normal"  # "normal" | "seed-sweep"
    is_seed_sweep: bool = False

    # Seed info
    seed_min: Optional[int] = None
    seed_max: Optional[int] = None
    seed_mode: Optional[str] = None  # "fixed" | "progressive" | "random"

    # Timestamps
    session_created_at: Optional[datetime] = None
    stats_computed_at: Optional[datetime] = None

    # Completion threshold (configurable)
    completion_threshold: float = 0.95
