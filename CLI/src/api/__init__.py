"""
API module for Stable Diffusion WebUI integration

This module provides a clean separation of concerns for API communication,
session management, file I/O, progress reporting, and batch orchestration.
"""

from .sdapi_client import SDAPIClient, GenerationConfig, PromptConfig
from .session_manager import SessionManager
from .image_writer import ImageWriter
from .progress_reporter import ProgressReporter, SilentProgressReporter
from .batch_generator import BatchGenerator, create_batch_generator

__all__ = [
    'SDAPIClient',
    'GenerationConfig',
    'PromptConfig',
    'SessionManager',
    'ImageWriter',
    'ProgressReporter',
    'SilentProgressReporter',
    'BatchGenerator',
    'create_batch_generator',
]
