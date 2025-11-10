"""
Storage pattern implementations for filesystem abstraction.

This module provides abstract base classes and concrete implementations
for accessing files and directories (sessions, images, manifests, etc.).

Separation of concerns:
- Storage: Filesystem operations (read, write, list, exists)
- Service: Business logic (stats computation, orchestration)
- Repository: Database operations (CRUD, batch loading)
"""

from sd_generator_webui.storage.base import Storage, FileMetadata
from sd_generator_webui.storage.session_storage import (
    SessionStorage,
    LocalSessionStorage
)
from sd_generator_webui.storage.image_storage import (
    ImageStorage,
    LocalImageStorage
)

__all__ = [
    "Storage",
    "FileMetadata",
    "SessionStorage",
    "LocalSessionStorage",
    "ImageStorage",
    "LocalImageStorage",
]
