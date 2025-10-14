# Roadmap Archive

This directory contains obsolete roadmap documents kept for historical reference.

## Archived Documents

### Session Planning Documents (Obsolete)
- **NEXT_SESSION.md** - Session planning for Phase 1/2 features (now complete)
- **PHASE2_CONTINUATION_PART2.md** - Phase 2 implementation notes (completed 2025-10-07)
- **PHASE2_CONTINUATION_PROMPT.md** - Phase 2 implementation prompts (completed)

### Legacy Roadmap
- **roadmap.md** - Old roadmap format (replaced by organized structure in `/done/`, `/next/`, `/future/`)

### Superseded Specifications
- **json-config-feature.md** - JSON config system spec (1168 lines, obsolete)
  - **Why archived:** Project chose YAML templating instead of JSON configs
  - **Current equivalent:** Phase 2 YAML system (see `/docs/cli/technical/yaml-templating-system.md`)
  - **Features completed differently:**
    - SF-4 (Enhanced Naming) - Implemented in `output_namer.py`
    - SF-5 (JSON Metadata) - Implemented in `metadata_generator.py`
    - SF-7 (Global Config) - Implemented in `global_config.py`
  - **Status:** JSON approach abandoned in favor of YAML (more flexible, human-friendly)

## Current Roadmap Structure

The active roadmap is now organized as:
- `/done/` - Completed features with implementation details
- `/next/` - Features planned for next sprint
- `/future/` - Backlog items for future implementation
- `README.md` - Current status and roadmap overview
- `braindump.md` - Ideas and feature proposals

## Current System Documentation

- **YAML Templating:** `/docs/cli/technical/yaml-templating-system.md`
- **Architecture:** `/docs/cli/technical/architecture.md`
- **User Guide (New):** `/docs/cli/guide/README.md` - Complete progressive learning path
- **Getting Started:** `/docs/cli/guide/getting-started.md`
- **Templates Advanced:** `/docs/cli/guide/4-templates-advanced.md`

---

**Archived:** 2025-10-07
**Reason:** Features completed, replaced by new organizational structure and YAML-based system
