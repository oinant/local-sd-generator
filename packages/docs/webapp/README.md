# Web Application Documentation

**Status:** 🚧 Planned (not yet implemented)

---

## Overview

The Web Application will provide a browser-based interface for managing and running image generation sessions.

**Current status:** CLI-only implementation complete. Web app is planned for future development.

---

## Planned Features

### Core Functionality

- **Config Management**
  - Create, edit, and save JSON configs visually
  - Config validation with inline error messages
  - Template library for common use cases

- **Generation Management**
  - Start, pause, resume generation runs
  - Real-time progress monitoring
  - Image preview gallery
  - Session history and replay

- **Variation Management**
  - Upload and edit variation files
  - Inline variation editor
  - Nested variation builder
  - Variation file library

### Advanced Features

- **Metadata Browser**
  - Search and filter generated images
  - View full generation metadata
  - Export to various formats

- **Checkpoint Manager**
  - Browse available checkpoints
  - Switch between models
  - Model comparison tools

- **Batch Processing**
  - Queue multiple configs
  - Schedule generation runs
  - Resource management

---

## Roadmap

See [roadmap/future/webapp-architecture.md](../roadmap/future/webapp-architecture.md) for detailed planning.

---

## Current Workflow (CLI)

Until the web app is available, use the CLI:

```bash
# Run from JSON config
python3 CLI/generator_cli.py --config configs/my_config.json

# Interactive mode
python3 CLI/generator_cli.py
```

See [CLI Usage Documentation](../cli/usage/getting-started.md) for details.

---

## Contributing

Interested in helping build the web app? See the architecture design in [roadmap/future/webapp-architecture.md](../roadmap/future/webapp-architecture.md).

---

**Last updated:** 2025-10-01
