"""Orchestrator package for V2 generation architecture.

This package contains the new orchestrator-based architecture that replaces
the monolithic _generate() function with modular, testable components.

Core Components:
- EventType: Event types for session lifecycle
- CLIConfig: Parsed CLI arguments
- SessionConfig: Unified immutable configuration (single source of truth)
- SessionConfigBuilder: Builds SessionConfig from CLI + Template configs
- SessionEventCollector: Event-driven CLI output management

Migration Strategy:
This code is part of a Strangler Fig migration. The old _generate()
implementation routes to either the old path or the new orchestrator
based on the SDGEN_USE_NEW_ARCH environment variable.
"""

from .event_types import EventType
from .cli_config import CLIConfig
from .session_config import SessionConfig
from .session_config_builder import SessionConfigBuilder
from .session_event_collector import SessionEventCollector

__all__ = [
    "EventType",
    "CLIConfig",
    "SessionConfig",
    "SessionConfigBuilder",
    "SessionEventCollector",
]
