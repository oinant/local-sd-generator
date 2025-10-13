# CLI Documentation

Command-line interface for Stable Diffusion batch image generation with variations.

## Overview

The CLI provides a powerful system for generating multiple image variations using:
- **YAML Templates**: Declarative `.prompt.yaml` configuration files (Phase 2)
- **Placeholders**: Dynamic prompt templating with `{PlaceholderName}`
- **Variation files**: External YAML files containing variation options
- **Chunk Templates**: Reusable prompt components with inheritance
- **Multi-field Variations**: Combine multiple variation files
- **Batch processing**: Generate hundreds of variations automatically

## Documentation

### Usage Documentation
User guides and how-to articles:
- [Getting Started](./usage/getting-started.md) - Installation and first generation
- [YAML Templating Guide](./usage/yaml-templating-guide.md) - Creating `.prompt.yaml` templates
- [Variation Files](./usage/variation-files.md) - Creating and managing variations
- [Examples](./usage/examples.md) - Common use cases and patterns
- ~~[JSON Config System](./usage/json-config-system.md)~~ - **DEPRECATED** (removed in favor of YAML)

### Technical Documentation
Architecture and implementation details:
- [Architecture Overview](./technical/architecture.md) - System design
- [V2.0 Templating Engine](./technical/v2-templating-engine.md) - Current template system architecture
- [Error Handling & Validation](./technical/error-handling-validation.md) - Validation system and error messages ✨ New!
- [Output System](./technical/output-system.md) - File naming & metadata
- [Design Decisions](./technical/design-decisions.md) - Why we made certain choices

## Quick Start

```bash
# Interactive mode - select from available templates
python3 template_cli.py

# Run specific template
python3 template_cli.py --template prompts/portrait.prompt.yaml

# Dry-run mode (save JSON requests without calling API)
python3 template_cli.py --template test.yaml --dry-run

# List available templates
python3 template_cli.py --list
```

## Current Features (V2.0)

✅ **YAML Templates**: `.prompt.yaml` format with comprehensive validation
✅ **Placeholder System**: `{Expression}`, `{Angle}`, inline variations
✅ **Template Inheritance**: Extend base templates with `implements:`
✅ **Modular Imports**: Multi-file imports with `imports:`
✅ **Reusable Chunks**: Composable template blocks
✅ **Advanced Selectors**: `[random:N]`, `[limit:N]`, `[indexes:1,5,8]`, `[keys:foo,bar]`
✅ **Weight-based Loops**: Control loop ordering with `$W` syntax
✅ **Generation Modes**: Combinatorial (all combinations), Random (sampling)
✅ **Seed Control**: Fixed, progressive, random
✅ **Variation Statistics Display**: See detected variations before generation ✨ New!
✅ **Comprehensive Error Messages**: Clear validation with examples ✨ New!
✅ **Enhanced File Naming**: Descriptive filenames with variation values
✅ **JSON Metadata**: Complete generation metadata export
✅ **Global Config**: Project-level configuration (`.sdgen_config.json`)
✅ **Hires Fix Support**: Two-pass upscaling configuration

## Migration from Phase 1 (JSON)

**Phase 1 JSON system has been removed.** Use YAML templates instead:

- **Old:** `generator_cli.py --config config.json`
- **New:** `template_cli.py --template config.prompt.yaml`

See [YAML Templating Guide](./usage/yaml-templating-guide.md) for migration instructions.

## See Also

- [Roadmap](../roadmap/README.md) - Feature planning
- [Development Setup](../tooling/usage/development-setup.md) - Contributing
