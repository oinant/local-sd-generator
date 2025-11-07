# Architecture Documents

**Project:** SD Image Generator WebUI - Session Management
**Created:** 2025-11-07
**Status:** Architecture Phase Complete

---

## Overview

This directory contains **complete Technical Architecture Documents** for the Session Statistics & Metadata Management epic (GitHub Issue #69).

The epic has been broken down into **5 implementable features** with clear dependencies, effort estimates, and success criteria.

---

## Documents

### Implementation Guide
- **[IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)** - Start here! Complete implementation guide with timeline, testing strategy, and success criteria

### Feature Architecture Documents
1. **[feature-1-session-stats-data-layer.md](./feature-1-session-stats-data-layer.md)** - Database schema and stats calculation logic
2. **[feature-2-session-stats-api.md](./feature-2-session-stats-api.md)** - RESTful API endpoints for session stats
3. **[feature-3-session-list-ui.md](./feature-3-session-list-ui.md)** - Master list view with filters
4. **[feature-4-session-details-panel.md](./feature-4-session-details-panel.md)** - Detailed stats display panel
5. **[feature-5-editable-metadata.md](./feature-5-editable-metadata.md)** - Inline metadata editing with auto-save

---

## Quick Reference

### Dependency Chain
```
F1 (Data Layer) → F2 (API) → F3 (Session List) → F4 (Details Panel) → F5 (Editable Metadata)
```

### Estimated Effort
- **Total:** 10-14 hours
- **Phase 1 (Backend):** 4-6 hours (F1 + F2)
- **Phase 2 (Frontend UI):** 4-5 hours (F3 + F4)
- **Phase 3 (Metadata Editing):** 2-3 hours (F5)

### Key Technologies
- **Backend:** Python 3.11+, FastAPI, SQLite, Pydantic
- **Frontend:** Vue 3, Vuetify 3, Pinia, @vueuse/core
- **Testing:** pytest (backend), vitest (frontend)

---

## Database Schema

### New Table: `session_stats`
25 fields tracking generation metadata, API parameters, image counts, placeholders, and timestamps.

**Indexes:**
- `sd_model` - For model-specific analysis
- `is_seed_sweep` - For seed experiment filtering
- `completion_percentage` - For incomplete session detection
- `session_created_at` - For date range filtering

See Feature 1 architecture for full schema.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions/` | List sessions with stats + metadata (with filters) |
| GET | `/api/sessions/:name/stats` | Get detailed stats for session |
| POST | `/api/sessions/:name/stats/refresh` | Force recompute stats |
| PATCH | `/api/sessions/:name/metadata` | Update tags/flags/notes |
| GET | `/api/sessions/recent/liked` | Get recently liked sessions |

See Feature 2 architecture for detailed API specs.

---

## UI Components

### New Components (6)
- `SessionCard.vue` - Session card with thumbnail, stats, tags
- `SessionFilters.vue` - Filter bar with toggleable chips
- `SessionDetailDrawer.vue` - Desktop detail drawer
- `SessionDetailContent.vue` - Shared detail content
- `EditableSessionMetadata.vue` - Metadata editor with auto-save
- `sessionsStore.js` - Pinia store for session state

See Features 3-5 for detailed component specs.

---

## Strategic Goals

### Enables Future Features

**Feature #70 (Variation Rating):**
- Uses `placeholders` and `variations_summary` to build rating UI
- Filters images by placeholder value for side-by-side comparison

**Feature #61 (Image Tagging):**
- Uses `session_created_at` and `sd_model` for batch tagging workflows
- Session tags can propagate to images

**Model Analysis:**
- Query by `sd_model` to aggregate stats across sessions
- Compare model performance, identify optimal models

**Seed-Sweep Analysis:**
- Filter by `is_seed_sweep = 1` to find seed experiments
- Analyze seed impact on generation quality

---

## Success Criteria (Overall)

### Performance
- ✅ Stats computation: <500ms for 100 images
- ✅ Session list render: <1s for 100 sessions
- ✅ Filter updates: <500ms
- ✅ Detail panel render: <100ms
- ✅ Auto-save: within 2s of user action

### Functionality
- ✅ 100% coverage for sessions with manifest.json
- ✅ All filters work correctly
- ✅ No data loss on network errors
- ✅ Responsive on mobile (320px) and desktop (1920px)

### Code Quality
- ✅ All tests pass (23 test cases)
- ✅ mypy strict mode passes
- ✅ Test coverage >80%
- ✅ Zero flake8 warnings

---

## Implementation Phases

### Phase 1: Backend Foundation (4-6h)
**Day 1:**
- Morning: Implement F1 (Stats Calculator + Service)
- Afternoon: Implement F2 (API Endpoints)
- **Checkpoint:** Backend ready, testable via Swagger UI

### Phase 2: Frontend UI (4-5h)
**Day 2:**
- Morning: Implement F3 (Session List)
- Afternoon: Implement F4 (Detail Panel)
- **Checkpoint:** Users can browse sessions and view details

### Phase 3: Metadata Editing (2-3h)
**Day 3:**
- Morning: Implement F5 (Editable Metadata)
- **Checkpoint:** Full CRUD for metadata with auto-save

---

## Testing Strategy

### Unit Tests (15 cases)
- F1: 5 tests for `SessionStatsCalculator`
- F3: 3 tests for `SessionCard.vue`
- F4: 3 tests for `SessionDetailDrawer.vue`
- F5: 5 tests for `EditableSessionMetadata.vue`

### Integration Tests (8 cases)
- F1: 3 tests for `SessionStatsService`
- F2: 5 tests for API endpoints

### Manual Testing
- Real sessions (20+ from production)
- Mobile (320px) and desktop (1920px)
- Performance with 100+ sessions
- Keyboard navigation
- Network error scenarios

---

## File Inventory

### Backend (Python)
**New Files:** 7 files (~1,000 lines)
- Stats calculator, service, and tests
- API integration tests

**Modified Files:** 2 files (~250 lines)
- `models.py` - Add SessionStats model
- `api/sessions.py` - Refactor with filters

### Frontend (Vue/JS)
**New Files:** 8 files (~1,850 lines)
- Pinia store, components, and tests

**Modified Files:** 3 files (~450 lines)
- `Sessions.vue`, `SessionDetail.vue`, `api.js`

**Total:** ~5,200 lines of code across 20 files

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Large manifest.json files | Cache stats in DB, compute once |
| UI lag with 1000+ sessions | Virtual scrolling + lazy thumbnails |
| Concurrent edit conflicts | Optimistic locking (phase 2) |
| Network errors lose edits | Keep local changes, retry button |
| Missing manifest.json | Graceful fallback, partial stats |

---

## Next Steps After Completion

1. **Deploy to production** - Test with 12k+ real images
2. **Feature #70** - Variation Rating (depends on placeholders)
3. **Feature #61** - Image Tagging (depends on metadata)
4. **Analytics Dashboard** - Aggregate stats across sessions
5. **CLI Admin Tool** - `sdgen-admin compute-stats --all`

---

## How to Use These Documents

### For Implementation
1. Read `IMPLEMENTATION_ROADMAP.md` first
2. Implement features in order (F1 → F2 → F3 → F4 → F5)
3. Refer to individual feature documents for detailed specs
4. Run tests after each feature

### For Review
1. Check database schema in F1 for conflicts
2. Verify API contracts in F2 match frontend needs
3. Review UI/UX designs in F3-F5 for usability
4. Validate test coverage and success criteria

### For Maintenance
- Each document has "Risks and Mitigations" section
- See "Future Enhancements (Phase 2)" for planned improvements
- Check "Strategic Alignment" for feature dependencies

---

## Document Status

- ✅ **F1 Architecture:** Complete (2025-11-07)
- ✅ **F2 Architecture:** Complete (2025-11-07)
- ✅ **F3 Architecture:** Complete (2025-11-07)
- ✅ **F4 Architecture:** Complete (2025-11-07)
- ✅ **F5 Architecture:** Complete (2025-11-07)
- ✅ **Implementation Roadmap:** Complete (2025-11-07)

**Next:** Ready for implementation

---

## Contact & References

**GitHub Issue:** #69 (Session Management Epic)
**Related Issues:** #66 (Vue Router), #70 (Variation Rating), #61 (Image Tagging)
**Project:** `/mnt/d/StableDiffusion/local-sd-generator`
**Backend:** `packages/sd-generator-webui/backend/`
**Frontend:** `packages/sd-generator-webui/front/`
**Database:** `/mnt/d/St/private-new/metadata/sessions.db`

---

## Architecture Principles

1. **Separation of Concerns:** Stats (computed) vs Metadata (user-editable)
2. **Lazy Loading:** Compute stats on first access, cache in DB
3. **Responsive Design:** Desktop drawer, mobile full-page
4. **Auto-Save:** Debounced updates, no explicit save button
5. **Graceful Degradation:** Missing data doesn't break UI
6. **Strategic Alignment:** Every feature enables future work

---

**Architecture Phase Complete - Ready for Implementation**
