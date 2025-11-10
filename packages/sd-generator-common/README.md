# sd-generator-common

Shared models and utilities for SD Generator packages.

## Purpose

This package contains shared data models used across multiple SD Generator packages:
- `sd-generator-cli` - Command-line interface
- `sd-generator-watchdog` - Background sync services
- `sd-generator-webui` - Web UI backend

## Models

### ManifestModel

The `ManifestModel` represents the `manifest.json` file structure, which is the source of truth for session metadata.

**Key features:**
- Session status FSM (`ongoing` → `completed`/`aborted`)
- Generation configuration snapshot
- Generated images list
- Pydantic validation and serialization

**Usage:**

```python
from sd_generator_common import ManifestModel, SessionStatus

# Read manifest
with open("manifest.json") as f:
    data = json.load(f)
    manifest = ManifestModel(**data)

# Update status
manifest.status = SessionStatus.COMPLETED

# Write manifest
with open("manifest.json", "w") as f:
    json.dump(manifest.model_dump(), f, indent=2)
```

### SessionStatus

Enum for session status FSM:
- `ONGOING` - Session in progress
- `COMPLETED` - All images generated successfully
- `ABORTED` - Session interrupted (SIGTERM/SIGINT/error)

## Installation

This package is part of the SD Generator monorepo and is installed as a workspace dependency.

```bash
# From project root
poetry install
```

## Development

```bash
# Type checking
mypy sd_generator_common

# Tests
pytest
```

## Architecture

```
manifest.json (filesystem)
      ↓
   Watchdog (observer)
      ↓
session_stats DB (cache)
```

The `manifest.json` is the **source of truth**. The database is a computed cache for fast queries.
