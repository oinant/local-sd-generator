"""Module de jobs asynchrones pour l'application."""

from .thumbnail_generator import run_thumbnail_generation_job

__all__ = ['run_thumbnail_generation_job']