# Roadmap

Feature planning and implementation tracking for SD Image Generator.

## 📊 Current Status

**Active Work:** Phase 2 YAML templating complete, API module refactored
**Architecture:** New SRP-compliant `api/` module (5 classes)
**Tests:** 199 passing ✅ (52 templating + 65 API + 82 other)
**Last Update:** 2025-10-07

## 🗂️ Roadmap Organization

### [✅ Done](./done/)
Completed features with full documentation and tests.

**Recent completions (2025-10-07):**
- **API Module Refactoring** - SRP architecture with 5 focused classes (65 tests)
- **Phase 1 to Legacy Migration** - Removed 5K+ lines of monolithic code
- **Template CLI Migration** - Uses new API module architecture
- JSON Config Phase 1: Enhanced File Naming & Metadata (49 tests)
- JSON Config Phase 2: Global Config & Validation (86 tests)
- Placeholder Priority System

### [🔄 WIP](./wip/)
Features currently being implemented.

**Active:**
- (Nothing currently in active development)

### [⏭️ Next](./next/)
Features planned for next sprint.

**Up next:**
- **Numeric Slider Placeholders** - LoRA slider testing (`{DetailLevel:Unit:-1:3}`)
- **Character Templates (Phase 2)** - Reusable character definitions with inheritance
- JSON Config Phase 3: Config Selection & Execution (SF-2, SF-3)

### [🔮 Future](./future/)
Features planned for future iterations.

**Backlog:**
- JSON Config Phase 4: Advanced features (SF-6, SF-8)
- Inline variations in JSON
- SQLite database for session tracking
- Web app enhancements
- WebP thumbnail generation

## 📝 Feature Lifecycle

```
future/ → next/ → wip/ → done/
```

**When starting a feature:**
1. Move spec from `next/` to `wip/`
2. Update spec with implementation plan
3. Create related technical docs in `docs/{cli|webapp|tooling}/technical/`

**When completing a feature:**
1. Move spec from `wip/` to `done/`
2. Add completion date, test count, commits
3. Update usage docs in `docs/{cli|webapp|tooling}/usage/`
4. Link to technical documentation

## 🎯 Priority Levels

- **Priority 1-3**: Critical features (current sprint)
- **Priority 4-6**: Important features (next sprint)
- **Priority 7-8**: Nice-to-have features (future)
- **Priority 9-10**: Research/experimental

## 📋 Roadmap Files

Each roadmap file should contain:
- **Status**: done/wip/next/future
- **Priority**: 1-10
- **Description**: What and why
- **Implementation**: Technical approach
- **Tasks**: Detailed task list
- **Success Criteria**: Definition of done
- **Tests**: Test coverage information
- **Documentation**: Links to technical/usage docs
- **Commits**: Related commit hashes (for done items)

## 🔗 Related Documentation

- [CLI Roadmap Items](../cli/technical/design-decisions.md)
- [Documentation Guidelines](../../CLAUDE.md#documentation-guidelines)
