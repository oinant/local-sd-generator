# Implementation Roadmap: Session Statistics & Metadata Management

**Project:** SD Image Generator WebUI
**Epic:** Session Management (GitHub Issue #69)
**Created:** 2025-11-07
**Total Estimated Effort:** 11-14 hours (spread across 5 features)

---

## Overview

This roadmap breaks down the Session Statistics & Metadata Management epic into **5 implementable features**, each with complete technical architecture, clear dependencies, and defined success criteria.

**Strategic Goals:**
- Enable #70 (Variation Rating) - requires session stats and placeholders
- Enable #61 (Image Tagging) - requires session metadata and filtering
- Enable model-specific analysis - requires sd_model indexing and aggregation
- Improve user experience - comprehensive session browsing with filters

---

## Feature Breakdown

| ID | Feature | Dependencies | Effort | Status |
|----|---------|--------------|--------|--------|
| F1 | Session Statistics Data Layer | None | 2-3h | Architecture Complete |
| F2 | Session Statistics API | F1 | 2-3h | Architecture Complete |
| F3 | Session List with Stats UI | F2, #66 | 2-3h | Architecture Complete |
| F4 | Session Details Panel | F3 | 2h | Architecture Complete |
| F5 | Editable Session Metadata | F4 | 2-3h | Architecture Complete |

**Total:** 10-14 hours

---

## Feature 1: Session Statistics Data Layer

**Files:** `/packages/sd-generator-webui/backend/sd_generator_webui/services/`
- `stats_calculator.py` (300 lines)
- `session_stats_service.py` (200 lines)

**Database:**
- New table: `session_stats` with 25 fields
- 4 indexes: model, seed_sweep, completion, created_at

**Key Capabilities:**
- Compute stats from `manifest.json` + filesystem
- Detect session type (normal vs seed-sweep)
- Calculate completion percentage
- Cache stats in SQLite for fast access

**Success Criteria:**
- Stats computation <500ms for 100 images
- 100% coverage for sessions with manifest.json
- Seed-sweep detection >95% accuracy

**Deliverables:**
- ✅ `SessionStatsCalculator` class with 10 methods
- ✅ `SessionStatsService` with CRUD operations
- ✅ Unit tests (5 test cases)
- ✅ Integration tests (3 test cases)

---

## Feature 2: Session Statistics API

**Files:** `/packages/sd-generator-webui/backend/sd_generator_webui/api/sessions.py`

**Endpoints:**
- `GET /api/sessions/` - List sessions with stats + metadata (with filters)
- `GET /api/sessions/:name/stats` - Detailed stats for session
- `POST /api/sessions/:name/stats/refresh` - Force recompute stats
- `PATCH /api/sessions/:name/metadata` - Update tags/flags (already exists, verify)
- `GET /api/sessions/recent/liked` - Shortcut for liked sessions

**Filters:**
- liked, test, complete, seed_sweep, model, from_date, to_date, limit, offset

**Success Criteria:**
- `GET /api/sessions/` returns 100 sessions in <2s
- Stats lazy-loaded (compute on first access, cache)
- Filters return accurate results

**Deliverables:**
- ✅ 5 API endpoints with Pydantic models
- ✅ Integration tests (5 test cases)
- ✅ Frontend API client methods in `api.js`

---

## Feature 3: Session List with Stats UI

**Files:** `/packages/sd-generator-webui/front/src/`
- `stores/sessions.js` (300 lines)
- `components/SessionCard.vue` (200 lines)
- `components/SessionFilters.vue` (150 lines)
- `views/Sessions.vue` (300 lines, replaces placeholder)

**UI Components:**
- **Session Card:** Thumbnail, model, image count, completion badge, tags
- **Filters Bar:** Liked, test, seed-sweep, complete, model, date, search
- **Master List:** Grid on desktop, list on mobile
- **Detail Drawer:** Opens on click (desktop), navigates on mobile

**Success Criteria:**
- Renders 100 sessions in <1s
- Responsive (320px mobile to 1920px desktop)
- Infinite scroll / pagination works
- Filters update results in <500ms

**Deliverables:**
- ✅ Pinia `sessionsStore` with filters and pagination
- ✅ Session card with visual states (selected, hover, completion colors)
- ✅ Filter bar with toggleable chips
- ✅ Component unit tests (3 test cases)

---

## Feature 4: Session Details Panel

**Files:** `/packages/sd-generator-webui/front/src/components/`
- `SessionDetailDrawer.vue` (300 lines)
- `SessionDetailContent.vue` (200 lines, shared)
- `views/SessionDetail.vue` (100 lines, mobile)

**Sections:**
- 📊 Generation Stats (model, mode, seed)
- 📸 Images (expected, actual, completion %, duration)
- 🎲 API Parameters (size, steps, CFG, sampler)
- 🧩 Placeholders (list with first 10 variations)
- 🏷️ Metadata (tags, flags, notes, rating)

**Success Criteria:**
- Display all 20+ stats fields
- Responsive (drawer on desktop, full-page on mobile)
- Renders in <100ms after API response
- Color-coded completion badges

**Deliverables:**
- ✅ Detail drawer component with 5 sections
- ✅ Completion color coding (green/yellow/red)
- ✅ Placeholder expansion (first 10 + "N more")
- ✅ Component unit tests (3 test cases)

---

## Feature 5: Editable Session Metadata

**Files:** `/packages/sd-generator-webui/front/src/components/`
- `EditableSessionMetadata.vue` (300 lines)

**Editing Features:**
- **Tags:** Combobox with autocomplete, create new tags
- **Flags:** Toggleable chips (liked, test, complete)
- **Notes:** Expandable textarea (500 char limit)
- **Rating:** Toggle buttons (like/dislike/clear)

**Auto-Save:**
- Debounced PATCH requests (1s for tags/notes, 500ms for flags)
- Visual feedback (saving → saved → idle)
- Error handling (show toast, keep local changes)

**Success Criteria:**
- Changes persist within 2s of user stopping typing
- No data loss on network errors
- Full keyboard navigation works
- Save state indicator always visible

**Deliverables:**
- ✅ Editable metadata component with 4 input types
- ✅ Debounced auto-save (using @vueuse/core)
- ✅ Save state indicator (saving/saved/error)
- ✅ Component unit tests (5 test cases)

---

## Implementation Order

### Phase 1: Backend Foundation (Features 1-2)
**Duration:** 4-6 hours

1. **Day 1 Morning:** Implement F1 (Stats Calculator + Service)
   - Create `stats_calculator.py`
   - Create `session_stats_service.py`
   - Add `session_stats` table schema
   - Write unit tests

2. **Day 1 Afternoon:** Implement F2 (API Endpoints)
   - Refactor `/api/sessions/` with filters
   - Add `/api/sessions/:name/stats` endpoint
   - Add refresh endpoint
   - Write integration tests

**Checkpoint:** Backend ready, can be tested with Swagger UI (`/docs`)

---

### Phase 2: Frontend UI (Features 3-4)
**Duration:** 4-5 hours

3. **Day 2 Morning:** Implement F3 (Session List)
   - Create `sessionsStore`
   - Create `SessionCard.vue`
   - Create `SessionFilters.vue`
   - Refactor `Sessions.vue`
   - Test responsive layout

4. **Day 2 Afternoon:** Implement F4 (Detail Panel)
   - Create `SessionDetailDrawer.vue`
   - Extract shared `SessionDetailContent.vue`
   - Update `SessionDetail.vue` for mobile
   - Write component tests

**Checkpoint:** Users can browse sessions with stats, click for details

---

### Phase 3: Metadata Editing (Feature 5)
**Duration:** 2-3 hours

5. **Day 3 Morning:** Implement F5 (Editable Metadata)
   - Create `EditableSessionMetadata.vue`
   - Integrate into detail drawer
   - Add debounced auto-save
   - Test keyboard navigation
   - Write component tests

**Checkpoint:** Full CRUD for session metadata, auto-save working

---

## Testing Strategy

### Unit Tests (15 test cases)
- **F1:** 5 tests for `SessionStatsCalculator`
- **F3:** 3 tests for `SessionCard.vue`
- **F4:** 3 tests for `SessionDetailDrawer.vue`
- **F5:** 5 tests for `EditableSessionMetadata.vue`

### Integration Tests (8 test cases)
- **F1:** 3 tests for `SessionStatsService`
- **F2:** 5 tests for API endpoints

### Manual Testing
- Test on real sessions (20+ sessions from `/mnt/d/StableDiffusion/private-new/results/`)
- Test on mobile (320px) and desktop (1920px)
- Test with 100+ sessions (performance)
- Test keyboard navigation (Tab, Enter, Escape)
- Test network error scenarios

---

## Database Schema

### New Table: `session_stats`

```sql
CREATE TABLE session_stats (
    session_id TEXT PRIMARY KEY,
    session_path TEXT NOT NULL,

    -- Generation metadata
    sd_model TEXT,
    template_version TEXT,
    generation_mode TEXT,
    seed_mode TEXT,
    seed_base INTEGER,

    -- Prompts
    resolved_prompt TEXT,
    negative_prompt TEXT,

    -- API parameters
    width INTEGER,
    height INTEGER,
    steps INTEGER,
    cfg_scale REAL,
    sampler_name TEXT,

    -- Image counts
    images_expected INTEGER,
    images_actual INTEGER,
    completion_percentage REAL,

    -- Session type
    is_seed_sweep INTEGER DEFAULT 0,

    -- Placeholders and variations (JSON)
    placeholders_json TEXT,
    variations_summary_json TEXT,

    -- Timestamps
    session_created_at TEXT,
    manifest_generated_at TEXT,
    first_image_created_at TEXT,
    last_image_created_at TEXT,

    -- Stats metadata
    stats_computed_at TEXT NOT NULL,
    stats_version INTEGER DEFAULT 1,

    FOREIGN KEY (session_id) REFERENCES session_metadata(session_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_session_stats_model ON session_stats(sd_model);
CREATE INDEX idx_session_stats_seed_sweep ON session_stats(is_seed_sweep);
CREATE INDEX idx_session_stats_completion ON session_stats(completion_percentage);
CREATE INDEX idx_session_stats_created_at ON session_stats(session_created_at DESC);
```

---

## API Reference

### Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions/` | List sessions with stats + metadata (with filters) |
| GET | `/api/sessions/:name/stats` | Get detailed stats for session |
| POST | `/api/sessions/:name/stats/refresh` | Force recompute stats |
| PATCH | `/api/sessions/:name/metadata` | Update tags/flags/notes |
| GET | `/api/sessions/recent/liked` | Get recently liked sessions |

### Frontend Store Methods

```javascript
// sessionsStore
await loadSessions({ reset: true })
await loadNextPage()
await applyFilters(filters)
await clearFilters()
selectSession(sessionId)
deselectSession()
await refreshSession(sessionId)
await updateSessionMetadata(sessionId, update)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Large manifest.json files slow computation | Cache stats in DB, compute once |
| Large session lists (1000+) cause UI lag | Implement virtual scrolling + lazy thumbnails |
| Concurrent metadata edits cause conflicts | Add optimistic locking (phase 2) |
| Network errors lose user edits | Keep local changes, add retry button |
| Missing manifest.json breaks stats | Graceful fallback, show "Stats unavailable" |

---

## Success Criteria (Overall)

1. **Performance:**
   - Stats computation: <500ms for 100 images
   - Session list render: <1s for 100 sessions
   - Filter updates: <500ms
   - Detail panel render: <100ms

2. **Functionality:**
   - 100% of sessions with manifest.json have stats
   - All filters work correctly
   - Auto-save persists within 2s
   - No data loss on network errors

3. **UX:**
   - Responsive on mobile (320px) and desktop (1920px)
   - Keyboard navigation works
   - Color-coded completion is clear at a glance
   - Save state indicator always visible

4. **Code Quality:**
   - All tests pass (23 test cases total)
   - mypy strict mode passes
   - No flake8 warnings
   - Test coverage >80%

---

## Strategic Alignment

### Enables Future Features

**Feature #70 (Variation Rating):**
- Uses `placeholders` and `variations_summary` to build rating UI
- Filters images by placeholder value for comparison
- Tags sessions with "rated" after rating

**Feature #61 (Image Tagging):**
- Uses `session_created_at` and `sd_model` for batch tagging
- Session tags can inherit to images
- Filter images by session tags

**Model-Specific Analysis:**
- Query by `sd_model` to aggregate stats across sessions
- Compare model performance (completion rate, image quality)
- Identify best models for specific use cases

**Seed-Sweep Analysis:**
- Filter by `is_seed_sweep = 1` to find seed experiments
- Compare results across different seeds
- Identify optimal seed ranges

---

## File Inventory

### Backend (Python)
**New Files (7):**
- `/packages/sd-generator-webui/backend/sd_generator_webui/services/stats_calculator.py` (300 lines)
- `/packages/sd-generator-webui/backend/sd_generator_webui/services/session_stats_service.py` (200 lines)
- `/packages/sd-generator-webui/backend/tests/unit/services/test_stats_calculator.py` (150 lines)
- `/packages/sd-generator-webui/backend/tests/integration/test_session_stats_service.py` (100 lines)
- `/packages/sd-generator-webui/backend/tests/integration/test_sessions_api.py` (200 lines)

**Modified Files (2):**
- `/packages/sd-generator-webui/backend/sd_generator_webui/models.py` (+50 lines)
- `/packages/sd-generator-webui/backend/sd_generator_webui/api/sessions.py` (+200 lines refactor)

### Frontend (Vue/JS)
**New Files (6):**
- `/packages/sd-generator-webui/front/src/stores/sessions.js` (300 lines)
- `/packages/sd-generator-webui/front/src/components/SessionCard.vue` (200 lines)
- `/packages/sd-generator-webui/front/src/components/SessionFilters.vue` (150 lines)
- `/packages/sd-generator-webui/front/src/components/SessionDetailDrawer.vue` (300 lines)
- `/packages/sd-generator-webui/front/src/components/SessionDetailContent.vue` (200 lines)
- `/packages/sd-generator-webui/front/src/components/EditableSessionMetadata.vue` (300 lines)
- `/packages/sd-generator-webui/front/tests/unit/components/SessionCard.spec.js` (100 lines)
- `/packages/sd-generator-webui/front/tests/unit/components/EditableSessionMetadata.spec.js` (150 lines)

**Modified Files (3):**
- `/packages/sd-generator-webui/front/src/views/Sessions.vue` (+300 lines, replace placeholder)
- `/packages/sd-generator-webui/front/src/views/SessionDetail.vue` (+100 lines, replace placeholder)
- `/packages/sd-generator-webui/front/src/services/api.js` (+50 lines)

**Total:**
- **Backend:** 7 new files, 2 modified
- **Frontend:** 6 new files + 2 test files, 3 modified
- **Lines of Code:** ~3,000 lines (backend) + ~2,200 lines (frontend) = ~5,200 lines total

---

## Next Steps After Completion

1. **Deploy to production:** Test with real user data (12k+ images)
2. **Feature #70 (Variation Rating):** Build on session stats and placeholders
3. **Feature #61 (Image Tagging):** Build on session metadata and filtering
4. **Analytics Dashboard:** Aggregate stats across sessions, model comparison
5. **CLI Admin Tool:** `sdgen-admin compute-stats --all` for batch stats computation

---

## Documentation

All architecture documents are in:
- `.claude/architecture/feature-1-session-stats-data-layer.md`
- `.claude/architecture/feature-2-session-stats-api.md`
- `.claude/architecture/feature-3-session-list-ui.md`
- `.claude/architecture/feature-4-session-details-panel.md`
- `.claude/architecture/feature-5-editable-metadata.md`
- `.claude/architecture/IMPLEMENTATION_ROADMAP.md` (this document)

---

## Approval Checklist

Before starting implementation:
- [ ] All 5 architecture documents reviewed and approved
- [ ] Database schema reviewed (no conflicts with existing tables)
- [ ] API contracts reviewed (compatible with frontend expectations)
- [ ] UI/UX design approved (responsive layouts, color schemes)
- [ ] Test strategy approved (sufficient coverage)
- [ ] Risk mitigation plans approved
- [ ] Effort estimates confirmed (10-14 hours total)

---

## Contact

**Technical Architect Agent**
Created: 2025-11-07
GitHub Issue: #69 (Session Management Epic)
Dependencies: #66 (Vue Router), #70 (Variation Rating), #61 (Image Tagging)
