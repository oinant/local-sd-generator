"""
Migration registry - Central registry of all available migrations.

This module provides a single function to get all migrations in order.
When adding a new migration, import it here and add it to get_all_migrations().
"""

from typing import List

from sd_generator_webui.migrations.base import Migration
from sd_generator_webui.migrations.v001_initial_schema import InitialSchemaMigration


def get_all_migrations() -> List[Migration]:
    """
    Get all available migrations in order.

    When adding a new migration:
    1. Import it at the top of this file
    2. Add an instance to this list

    Returns:
        List of all migration instances (will be sorted by version)
    """
    return [
        InitialSchemaMigration(),
        # Add new migrations here:
        # V002_AddColumnXMigration(),
        # V003_CreateIndexYMigration(),
    ]
