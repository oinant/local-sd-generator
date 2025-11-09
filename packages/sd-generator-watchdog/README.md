# SD Generator Watchdog

Background filesystem watcher service for SD Image Generator.

## Purpose

Automatically monitors the sessions output directory (e.g., `apioutput/`) and imports new sessions into the SQLite database for the WebUI.

## Features

- **Initial catch-up**: Imports all existing sessions on startup
- **Real-time monitoring**: Watches for new session directories using `watchdog`
- **Graceful shutdown**: Handles SIGINT/SIGTERM cleanly
- **Standalone service**: Can run independently of WebUI

## Usage

### Standalone

```bash
# Run watchdog service
sdgen-watchdog run --sessions-dir ./apioutput

# With custom database path
sdgen-watchdog run --sessions-dir ./apioutput --db-path ./custom.db

# Show version
sdgen-watchdog version
```

### Integrated with WebUI

The watchdog service is automatically started/stopped by `sdgen webui start/stop`.

## Architecture

```
CLI (generates sessions)
  ↓ writes to filesystem
apioutput/
  ├── session_001/
  ├── session_002/
  └── ...
  ↓ watched by
Watchdog Service
  ↓ imports into
.sdgen/sessions.db
  ↓ read by
WebUI Backend
```

## Dependencies

- `watchdog` - Filesystem monitoring
- `sd-generator-webui` - For SessionStatsService (database operations)

## Development

```bash
# Install in editable mode
cd packages/sd-generator-watchdog
poetry install

# Run locally
python -m sd_generator_watchdog.cli run --sessions-dir ../../apioutput
```
