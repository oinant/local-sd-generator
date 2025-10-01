# CLI Documentation

Command-line interface for Stable Diffusion batch image generation with variations.

## Overview

The CLI provides a powerful system for generating multiple image variations using:
- **Placeholders**: Dynamic prompt templating with `{PlaceholderName}`
- **Variation files**: External text files containing variation options
- **JSON configs**: Declarative configuration for reproducible generations
- **Batch processing**: Generate hundreds of variations automatically

## Documentation

### Usage Documentation
User guides and how-to articles:
- [Getting Started](./usage/getting-started.md) - Installation and first generation
- [JSON Config System](./usage/json-config-system.md) - Using JSON configurations
- [Variation Files](./usage/variation-files.md) - Creating and managing variations
- [Examples](./usage/examples.md) - Common use cases and patterns

### Technical Documentation
Architecture and implementation details:
- [Architecture Overview](./technical/architecture.md) - System design
- [Config System](./technical/config-system.md) - JSON config loading & validation
- [Output System](./technical/output-system.md) - File naming & metadata
- [Variation Loader](./technical/variation-loader.md) - Placeholder system
- [Design Decisions](./technical/design-decisions.md) - Why we made certain choices

## Quick Start

```bash
# Using Python script
python CLI/facial_expression_generator.py

# Using JSON config (Phase 3+)
python CLI/generator_cli.py --config configs/my_config.json
```

## Current Features

✅ **Placeholder System**: `{Expression}`, `{Angle}`, etc.
✅ **Variation Loading**: From external text files
✅ **Generation Modes**: Combinatorial, random
✅ **Seed Control**: Fixed, progressive, random
✅ **Enhanced File Naming**: Descriptive filenames with variation values
✅ **JSON Metadata**: Complete generation metadata export
✅ **Global Config**: Project-level configuration (`.sdgen_config.json`)
✅ **JSON Config Loading**: Load and validate generation configs

🔄 **In Progress**: JSON-driven generation (Phase 3)

## See Also

- [Roadmap](../roadmap/README.md) - Feature planning
- [Development Setup](../tooling/usage/development-setup.md) - Contributing
