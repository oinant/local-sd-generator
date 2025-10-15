# Documentation Refactoring - Migration Plan

**Status:** 📋 Preparation complete, ready for execution
**Created:** 2025-10-01
**Estimated Duration:** 30-45 minutes (next session)

## Objective

Reorganize documentation into a clear, maintainable structure with separation by component (CLI, WebApp, Tooling) and purpose (usage vs technical).

## Current Structure (to reorganize)

```
docs/
├── features.md                      # Mixed content
├── json-config-feature.md          # Roadmap + spec
├── placeholders.md                 # Usage guide
├── roadmap/                        # Mixed items
│   ├── config-file-launch.md
│   ├── interactive-metadata.md
│   ├── json-session-config.md
│   ├── sqlite-database.md
│   ├── webapp-architecture.md
│   └── webp-thumbnails.md
```

## Target Structure (new)

```
docs/
├── README.md                       # ✅ Created - Index général
│
├── cli/                            # ✅ Created - CLI docs
│   ├── README.md                   # ✅ Created - Overview
│   ├── usage/                      # User guides
│   │   ├── getting-started.md      # 🔄 To create
│   │   ├── json-config-system.md   # 🔄 Extract from json-config-feature.md
│   │   ├── variation-files.md      # 🔄 Move from placeholders.md
│   │   └── examples.md             # 🔄 Extract from CLAUDE.md
│   └── technical/                  # Technical docs
│       ├── architecture.md         # 🔄 To create
│       ├── config-system.md        # 🔄 Extract from json-config-feature.md
│       ├── output-system.md        # 🔄 To create (SF-4, SF-5)
│       ├── variation-loader.md     # 🔄 Extract from CLAUDE.md
│       └── design-decisions.md     # 🔄 To create
│
├── webapp/                         # ✅ Created - Web app docs
│   ├── README.md                   # 🔄 To create
│   ├── usage/
│   │   ├── getting-started.md      # 🔄 To create
│   │   └── features.md             # 🔄 Extract from features.md
│   └── technical/
│       ├── architecture.md         # 🔄 Move from roadmap/webapp-architecture.md
│       ├── backend-api.md          # 🔄 To create
│       ├── frontend-components.md  # 🔄 To create
│       └── design-decisions.md     # 🔄 To create
│
├── tooling/                        # ✅ Created - Dev tools docs
│   ├── README.md                   # 🔄 To create
│   ├── usage/
│   │   ├── development-setup.md    # 🔄 To create
│   │   └── testing.md              # 🔄 To create
│   └── technical/
│       ├── test-framework.md       # 🔄 To create
│       └── ci-cd.md                # 🔄 To create (future)
│
└── roadmap/                        # ✅ Created - Feature planning
    ├── README.md                   # ✅ Created - Roadmap index
    ├── done/                       # Completed features
    │   ├── json-config-phase1.md   # 🔄 Extract from json-config-feature.md
    │   ├── json-config-phase2.md   # 🔄 Extract from json-config-feature.md
    │   └── placeholder-priority.md # 🔄 To create (existing feature)
    ├── wip/                        # Work in progress
    │   └── (empty)
    ├── next/                       # Next tasks
    │   └── json-config-phase3.md   # 🔄 Extract from json-config-feature.md
    └── future/                     # Future backlog
        ├── json-config-phase4.md   # 🔄 Extract from json-config-feature.md
        ├── inline-variations.md    # 🔄 Extract from json-config-feature.md
        ├── sqlite-database.md      # 🔄 Move from roadmap/
        ├── webapp-features.md      # 🔄 Consolidate webapp items
        ├── webp-thumbnails.md      # 🔄 Move from roadmap/
        └── config-file-launch.md   # 🔄 Move from roadmap/
```

## Migration Steps

### Step 1: Extract CLI Usage Documentation (15 min)

1. **Create `cli/usage/getting-started.md`**
   - Extract intro from CLAUDE.md
   - Add installation steps
   - Basic first generation example

2. **Create `cli/usage/json-config-system.md`**
   - Extract JSON schema from json-config-feature.md (lines 85-246)
   - Extract usage examples
   - Link to technical docs

3. **Move `placeholders.md` → `cli/usage/variation-files.md`**
   - Rename and reorganize
   - Add examples from CLAUDE.md
   - Document placeholder syntax (`{Name}`, `{Name:N}`, `{Name:#|1|2}`, `{Name:$N}`)

4. **Create `cli/usage/examples.md`**
   - Extract examples from CLAUDE.md (lines 158-202)
   - Add more practical use cases
   - Link to demo scripts

### Step 2: Extract CLI Technical Documentation (15 min)

1. **Create `cli/technical/architecture.md`**
   - Module structure diagram
   - Data flow
   - Component interactions
   - Extract from json-config-feature.md (lines 762-851)

2. **Create `cli/technical/config-system.md`**
   - Document SF-7 (Global Config)
   - Document SF-1 (Config Loading & Validation)
   - API reference for config modules
   - Validation rules

3. **Create `cli/technical/output-system.md`**
   - Document SF-4 (File Naming)
   - Document SF-5 (Metadata Export)
   - File naming algorithm
   - Metadata schema

4. **Create `cli/technical/variation-loader.md`**
   - Extract from CLAUDE.md (lines 92-109)
   - Document placeholder parsing
   - Document variation file format
   - Document nested variations

5. **Create `cli/technical/design-decisions.md`**
   - Why JSON configs?
   - Why separate schema/loader/validator?
   - Why camelCase for filenames?
   - Trade-offs made

### Step 3: Reorganize Roadmap (10 min)

1. **Create roadmap/done/ items**
   - `json-config-phase1.md` - Extract Phase 1 from json-config-feature.md
   - `json-config-phase2.md` - Extract Phase 2 from json-config-feature.md
   - `placeholder-priority.md` - Document existing feature

2. **Create roadmap/next/ items**
   - `json-config-phase3.md` - Extract Phase 3 from json-config-feature.md

3. **Create roadmap/future/ items**
   - `json-config-phase4.md` - Extract Phase 4
   - `inline-variations.md` - Extract from json-config-feature.md
   - Move existing roadmap files
   - Consolidate webapp items

### Step 4: WebApp Documentation (5 min - minimal)

1. **Create `webapp/README.md`**
   - Overview
   - Link to usage/technical docs (to be created later)

2. **Extract from `features.md`**
   - Identify webapp-specific content
   - Move to `webapp/usage/features.md`

3. **Move `roadmap/webapp-architecture.md`**
   - Move to `webapp/technical/architecture.md`

### Step 5: Tooling Documentation (5 min - minimal)

1. **Create `tooling/README.md`**
   - Overview of dev setup
   - Link to pytest docs

2. **Create `tooling/usage/development-setup.md`**
   - Python environment setup
   - WSL considerations
   - Running tests

3. **Create `tooling/usage/testing.md`**
   - pytest usage
   - Test structure
   - Running specific tests

### Step 6: Cleanup (5 min)

1. **Review old files**
   - Keep `features.md` if still has unique content
   - Archive `json-config-feature.md` (or delete after extraction)
   - Archive old roadmap items after migration

2. **Update cross-references**
   - Update links in README files
   - Update links in CLAUDE.md
   - Verify no broken links

3. **Git operations**
   - Stage all changes
   - Commit with detailed message
   - Verify git history clean

## Files to Create/Modify

### ✅ Already Created (Preparation Phase)
- `docs/README.md`
- `docs/cli/README.md`
- `docs/roadmap/README.md`
- `CLAUDE.md` (updated with guidelines)
- Directory structure

### 🔄 To Create/Extract (Next Session)
- 4 files in `cli/usage/`
- 5 files in `cli/technical/`
- 3 files in `roadmap/done/`
- 1 file in `roadmap/next/`
- 6+ files in `roadmap/future/`
- 3 files in `webapp/` (minimal)
- 3 files in `tooling/` (minimal)

**Total:** ~25 files to create/extract

## Post-Migration Checklist

- [ ] All old content extracted or archived
- [ ] No broken links in documentation
- [ ] README files provide clear navigation
- [ ] Technical docs explain architecture
- [ ] Usage docs provide examples
- [ ] Roadmap organized by status (done/wip/next/future)
- [ ] CLAUDE.md updated with new structure
- [ ] Git history clean with good commit message

## Success Criteria

✅ Documentation organized by component (CLI, WebApp, Tooling)
✅ Clear separation usage vs technical docs
✅ Roadmap organized by implementation status
✅ No duplicate or stale information
✅ Easy navigation with README indexes
✅ Guidelines in CLAUDE.md for future maintenance

## Notes

- Keep this migration plan for reference
- Use as template for future refactorings
- Consider this a living document
- Update as we discover new needs

---

**Ready for execution in next session with fresh context!** 🚀
