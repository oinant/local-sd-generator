"""
Repository pattern implementations for data access abstraction.

This module provides abstract base classes and concrete implementations
for accessing session data (stats and metadata) from various storage backends.
"""

from sd_generator_webui.repositories.base import Repository, BatchRepository
from sd_generator_webui.repositories.session_stats_repository import (
    SessionStatsRepository,
    SQLiteSessionStatsRepository
)
from sd_generator_webui.repositories.session_metadata_repository import (
    SessionMetadataRepository,
    SQLiteSessionMetadataRepository
)

__all__ = [
    "Repository",
    "BatchRepository",
    "SessionStatsRepository",
    "SQLiteSessionStatsRepository",
    "SessionMetadataRepository",
    "SQLiteSessionMetadataRepository",
]
