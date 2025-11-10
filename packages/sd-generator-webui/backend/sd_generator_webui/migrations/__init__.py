"""
Database migrations system.

This module provides an idempotent migration system for managing database schema evolution.

Key features:
- Idempotent: Can be run multiple times safely
- Tracked: Maintains migration history in schema_version table
- Isolated: Migrations are separate from business logic
- Ordered: Migrations run in sequence by version number
"""

from sd_generator_webui.migrations.runner import MigrationRunner

__all__ = ["MigrationRunner"]
