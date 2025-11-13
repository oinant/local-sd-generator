# Migration Guide: New Orchestrator Architecture

## Overview

The CLI now supports **two code paths** using the **Strangler Fig Pattern**:
- **Legacy path** (default): Original monolithic `_generate()` function (562 lines)
- **New path** (opt-in): Modular `GenerationOrchestrator` with tested components

This allows progressive migration and easy rollback if issues are found.

## Feature Flag

Use the `SDGEN_USE_NEW_ARCH` environment variable to switch between architectures:

```bash
# Default: Use legacy code (backward compatible)
sdgen generate -t template.yaml

# Opt-in: Use new orchestrator
SDGEN_USE_NEW_ARCH=true sdgen generate -t template.yaml
```

## Testing Both Paths

### Quick Comparison Test

```bash
# Test 1: Legacy code (baseline)
sdgen generate -t test.yaml -n 10
mv apioutput/session_001 apioutput/session_001_legacy

# Test 2: New orchestrator
SDGEN_USE_NEW_ARCH=true sdgen generate -t test.yaml -n 10
mv apioutput/session_001 apioutput/session_001_new

# Compare outputs
diff -r apioutput/session_001_legacy apioutput/session_001_new
```

### What to Compare

1. **Manifest structure** - Should be identical
2. **Image generation** - Same prompts, same seeds → same images
3. **Error handling** - Both should handle errors gracefully
4. **Performance** - Should be similar (new might be slightly faster)

## Architecture Differences

### Legacy Code (562 lines)
- Monolithic function in `cli.py`
- All logic in one place
- Hard to test individual parts
- Well-tested in production

### New Code (Phases 1-5)
- Modular components (6 classes)
- Event-driven architecture
- 89 unit tests (100% passing)
- Clean separation of concerns

## Components (New Architecture)

1. **SessionConfigBuilder** - Unified configuration (CLI + Template)
2. **ManifestBuilder** - Manifest snapshot creation
3. **ManifestManager** - Manifest lifecycle (FSM: ongoing → completed/aborted)
4. **PromptGenerator** - Prompt generation + statistics
5. **PromptConfigConverter** - V2 prompts → API PromptConfig
6. **ImageGenerator** - Batch image generation orchestration
7. **GenerationOrchestrator** - Coordinates all components (8 phases)

## Workflow Phases (New Architecture)

1. **Configuration** - Build `SessionConfig` from CLI + template
2. **Validation** - Validate template schema
3. **API Connection** - Early fail-fast connection test
4. **Loading & Resolution** - Load and resolve template via V2Pipeline
5. **Prompt Generation** - Generate prompts with statistics
6. **Manifest Preparation** - Build snapshot + initialize manifest
7. **Image Generation** - Generate images via ImageGenerator
8. **Finalization** - Update manifest status (completed/aborted)

## Migration Timeline

### Phase 1-5: Build Components (DONE ✅)
- All orchestrator components implemented
- 89/89 tests passing
- Architecture validated

### Phase 6: Feature Flag Integration (CURRENT)
- ✅ Feature flag added to `cli.py`
- ⏳ **Testing required by user**
- ⏳ Production validation

### Phase 7: Gradual Rollout (FUTURE)
- Enable by default (flip feature flag)
- Monitor for issues
- Keep legacy code as fallback

### Phase 8: Cleanup (FUTURE)
- Remove legacy code after validation
- Delete 562 lines from `cli.py`
- Archive migration documentation

## Known Differences

### SessionEventCollector vs Direct Console
- **Legacy**: Direct `console.print()` calls throughout
- **New**: Event-driven output via `SessionEventCollector`
- **Impact**: Output format might differ slightly (same info, different styling)

### Manifest Status FSM
- **Legacy**: Manual status updates
- **New**: Proper FSM (ongoing → completed/aborted)
- **Impact**: Manifest always has correct status, even on crashes

### Error Handling
- **Legacy**: Mixed exception handling
- **New**: Centralized error handling in orchestrator
- **Impact**: More consistent error messages

## Rollback Plan

If issues are found with new orchestrator:

```bash
# 1. Immediately switch back to legacy
unset SDGEN_USE_NEW_ARCH
# or explicitly:
SDGEN_USE_NEW_ARCH=false sdgen generate -t template.yaml

# 2. Report issue with comparison:
#    - Legacy output (working)
#    - New output (broken)
#    - Diff between manifests
```

## Performance Expectations

**New architecture should be:**
- ✅ Same or faster (fewer redundant operations)
- ✅ More memory efficient (better cleanup)
- ✅ More reliable (proper error handling)

**If you observe:**
- ❌ Slower generation
- ❌ Higher memory usage
- ❌ Different outputs (for same seed)

→ **Report immediately** with benchmark data

## Documentation

- **Architecture**: See `/docs/cli/technical/orchestrator-architecture.md` (TODO)
- **API Reference**: See `/docs/cli/reference/` (TODO)
- **Migration**: This file

## Support

**Questions? Issues?**
- Check GitHub Issues: https://github.com/oinant/local-sd-generator/issues
- Feature flag discussions: Add label `orchestrator-migration`

---

**Status**: Phase 6 (Feature Flag Integration) - **Testing Required**

**Last Updated**: 2025-11-13
