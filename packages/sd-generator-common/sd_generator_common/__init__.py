"""
SD Generator Common - Shared models and utilities.

This package contains shared data models used across CLI, Watchdog, and WebUI packages.
"""

from sd_generator_common.models.manifest import ManifestModel, SessionStatus

__version__ = "0.1.0"

__all__ = [
    "ManifestModel",
    "SessionStatus",
]
