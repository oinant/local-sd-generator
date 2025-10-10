# Legacy V1 Template System (Archived)

**Status:** Deprecated - Archived on 2025-10-10

This directory contains the original V1 Template System (Phase 2) code, archived during migration to V2.

## What was V1?

V1 was the original template system featuring:
- `variations:` format in YAML
- Multi-field syntax with `@multi-field` decorator
- Chunk system with basic inheritance
- Selector syntax `{Placeholder[selector]}`

## Why Archived?

V1 has been replaced by V2 which offers:
- Full inheritance with `implements:`
- Modular `imports:` system
- Reusable chunks with `@Chunk` syntax
- Advanced selectors with weights
- **100% backward compatibility** via compatibility layer

## Migration

All existing V1 templates work in V2 thanks to the compatibility layer in:
- `src/execution/legacy_compat.py`

## Files Archived

### Code (8 files)
- chunk.py
- loaders.py
- multi_field.py
- prompt_config.py
- resolver.py
- selectors.py
- types.py
- v1/__init__.py

### Tests (9 files)
See `tests/templating/legacy_v1/`

## Reference

For V2 documentation, see:
- V2 Architecture: `docs/cli/technical/v2_architecture.md`
- Migration Guide: Would be in docs if existed
- V2 Tests: `tests/v2/`

---

**Do not use this code in new projects.** Use V2 instead.
