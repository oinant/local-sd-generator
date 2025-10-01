# Roadmap

Feature planning and implementation tracking for SD Image Generator.

## 📊 Current Status

**Active Work:** JSON Config System - Phase 3
**Progress:** 2/3 core phases completed (66%)
**Tests:** 135 passing ✅

## 🗂️ Roadmap Organization

### [✅ Done](./done/)
Completed features with full documentation and tests.

**Recent completions:**
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
