# Technical Architecture Document: Feature 2 - Session Statistics API

**Feature ID:** F2-SESSION-STATS-API
**Status:** Architecture Complete
**Created:** 2025-11-07
**Owner:** Technical Architect Agent
**Dependencies:** Feature 1 (Session Stats Data Layer)
**Estimated Effort:** 2-3h

---

## 1. Overview

### 1.1 Problem Statement
Frontend needs **RESTful API endpoints** to access session statistics, update metadata, and filter sessions by various criteria (liked, seed-sweep, model, etc.). Current `/api/sessions/` endpoint only returns basic session info without stats.

### 1.2 Goals
1. **Unified session list** - Return sessions with stats and metadata in one call
2. **Lazy stats computation** - Compute stats on-demand, cache in database
3. **Flexible filtering** - Support filtering by flags, model, date range, completion status
4. **Metadata updates** - PATCH endpoint for tags/flags with auto-save
5. **Stats refresh** - Manual stats recomputation for sessions

### 1.3 Non-Goals
- Real-time session monitoring (WebSocket support is phase 2)
- Bulk operations (bulk delete, bulk tag) - phase 2
- Advanced analytics (aggregation, charts) - separate analytics API later

---

## 2. API Specification

### 2.1 Endpoint Overview

| Method | Endpoint | Description | Returns |
|--------|----------|-------------|---------|
| GET | `/api/sessions/` | List all sessions with stats + metadata | `SessionListResponse` |
| GET | `/api/sessions/:name/stats` | Get detailed stats for session | `SessionStats` |
| PATCH | `/api/sessions/:name/metadata` | Update tags/flags | `SessionMetadata` |
| POST | `/api/sessions/:name/stats/refresh` | Force recompute stats | `SessionStats` |
| GET | `/api/sessions/recent/liked` | Get recently liked sessions | `SessionListResponse` |

---

### 2.2 GET /api/sessions/

**List all sessions with stats and metadata**

#### Request

```http
GET /api/sessions/?liked=true&seed_sweep=false&model=illustriousXL&limit=50&offset=0
Authorization: Bearer {token}
```

**Query Parameters:**
- `liked` (optional, boolean): Filter by `is_favorite` flag
- `test` (optional, boolean): Filter by `is_test` flag
- `complete` (optional, boolean): Filter by completion status (`completion_percentage >= 95`)
- `seed_sweep` (optional, boolean): Filter by `is_seed_sweep` flag
- `model` (optional, string): Filter by `sd_model` (partial match)
- `from_date` (optional, ISO 8601): Filter sessions created after date
- `to_date` (optional, ISO 8601): Filter sessions created before date
- `limit` (optional, int, default=100): Max sessions to return
- `offset` (optional, int, default=0): Pagination offset

#### Response

```json
{
  "sessions": [
    {
      "session_id": "20251107_120000-facial_expressions",
      "session_path": "/mnt/d/StableDiffusion/apioutput/20251107_120000-facial_expressions",
      "created_at": "2025-11-07T12:00:00",

      "stats": {
        "sd_model": "illustriousXL_v01.safetensors",
        "template_version": "2.0",
        "generation_mode": "combinatorial",
        "seed_mode": "fixed",
        "seed_base": 42,
        "images_expected": 50,
        "images_actual": 50,
        "completion_percentage": 100.0,
        "is_seed_sweep": false,
        "placeholders": {
          "FacialExpression": 50
        },
        "variations_summary": {
          "FacialExpression": ["smile", "sad", "angry", "..."]
        },
        "width": 512,
        "height": 768,
        "steps": 30,
        "cfg_scale": 7.0,
        "sampler_name": "DPM++ 2M Karras",
        "session_created_at": "2025-11-07T12:00:00",
        "manifest_generated_at": "2025-11-07T12:05:23",
        "first_image_created_at": "2025-11-07T12:05:30",
        "last_image_created_at": "2025-11-07T12:25:45",
        "stats_computed_at": "2025-11-07T12:30:00"
      },

      "metadata": {
        "is_test": false,
        "is_complete": true,
        "is_favorite": true,
        "user_rating": "like",
        "user_note": "Best facial expressions so far",
        "tags": ["character-design", "lora-training"],
        "created_at": "2025-11-07T12:30:00",
        "updated_at": "2025-11-07T14:00:00"
      }
    }
  ],
  "total_count": 1,
  "limit": 100,
  "offset": 0
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Invalid token
- `500 Internal Server Error` - Database error

**Performance Notes:**
- Stats are lazy-loaded: computed on first access, cached in DB
- Query uses indexes on `session_created_at`, `sd_model`, `is_seed_sweep`, `completion_percentage`
- Limit to 100 sessions per request to avoid timeouts

---

### 2.3 GET /api/sessions/:name/stats

**Get detailed stats for a specific session**

#### Request

```http
GET /api/sessions/20251107_120000-facial_expressions/stats
Authorization: Bearer {token}
```

#### Response

```json
{
  "session_id": "20251107_120000-facial_expressions",
  "session_path": "/mnt/d/StableDiffusion/apioutput/20251107_120000-facial_expressions",
  "sd_model": "illustriousXL_v01.safetensors",
  "template_version": "2.0",
  "generation_mode": "combinatorial",
  "seed_mode": "fixed",
  "seed_base": 42,
  "resolved_prompt": "masterpiece, {FacialExpression}, beautiful girl",
  "negative_prompt": "low quality, blurry",
  "width": 512,
  "height": 768,
  "steps": 30,
  "cfg_scale": 7.0,
  "sampler_name": "DPM++ 2M Karras",
  "images_expected": 50,
  "images_actual": 50,
  "completion_percentage": 100.0,
  "is_seed_sweep": false,
  "placeholders": {
    "FacialExpression": 50
  },
  "variations_summary": {
    "FacialExpression": ["smile", "sad", "angry", "surprised", "..."]
  },
  "session_created_at": "2025-11-07T12:00:00",
  "manifest_generated_at": "2025-11-07T12:05:23",
  "first_image_created_at": "2025-11-07T12:05:30",
  "last_image_created_at": "2025-11-07T12:25:45",
  "stats_computed_at": "2025-11-07T12:30:00",
  "stats_version": 1
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Session doesn't exist or has no manifest.json
- `401 Unauthorized` - Invalid token
- `500 Internal Server Error` - Stats computation error

**Behavior:**
- If stats cached → return immediately
- If not cached → compute, cache, return (may take 1-2s for large sessions)

---

### 2.4 PATCH /api/sessions/:name/metadata

**Update tags and flags for a session**

#### Request

```http
PATCH /api/sessions/20251107_120000-facial_expressions/metadata
Authorization: Bearer {token}
Content-Type: application/json

{
  "is_favorite": true,
  "user_rating": "like",
  "tags": ["character-design", "lora-training", "facial-expressions"]
}
```

**Body Schema:** `SessionMetadataUpdate` (from Feature 1)
- All fields optional
- Only provided fields are updated
- Tags replace entire array (not append/remove)

#### Response

```json
{
  "session_id": "20251107_120000-facial_expressions",
  "session_path": "/mnt/d/StableDiffusion/apioutput/20251107_120000-facial_expressions",
  "is_test": false,
  "is_complete": true,
  "is_favorite": true,
  "user_rating": "like",
  "user_note": null,
  "tags": ["character-design", "lora-training", "facial-expressions"],
  "auto_metadata": null,
  "created_at": "2025-11-07T12:30:00",
  "updated_at": "2025-11-07T14:15:23"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Session doesn't exist
- `400 Bad Request` - Invalid request body
- `401 Unauthorized` - Invalid token

**Notes:**
- Creates metadata row if doesn't exist (auto-insert on first PATCH)
- Frontend can call this on every tag edit (debounced) for auto-save

---

### 2.5 POST /api/sessions/:name/stats/refresh

**Force recompute stats (manual refresh)**

#### Request

```http
POST /api/sessions/20251107_120000-facial_expressions/stats/refresh
Authorization: Bearer {token}
```

#### Response

```json
{
  "session_id": "20251107_120000-facial_expressions",
  "stats": { ... },
  "message": "Stats recomputed successfully"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Session doesn't exist
- `500 Internal Server Error` - Computation error

**Use Cases:**
- Session modified after stats cached (images added/removed)
- Manifest.json updated manually
- Stats computation failed previously (error recovery)

---

### 2.6 GET /api/sessions/recent/liked

**Get recently liked sessions (shortcut endpoint)**

#### Request

```http
GET /api/sessions/recent/liked?limit=10
Authorization: Bearer {token}
```

**Equivalent to:** `GET /api/sessions/?liked=true&limit=10&offset=0`

#### Response

Same as `GET /api/sessions/` but filtered by `is_favorite=true`, sorted by `updated_at DESC`.

**Use Case:** "Recently Liked" widget on homepage.

---

## 3. Backend Implementation

### 3.1 FastAPI Router

**File:** `/packages/sd-generator-webui/backend/sd_generator_webui/api/sessions.py` (major refactor)

```python
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from sd_generator_webui.auth import AuthService
from sd_generator_webui.config import IMAGES_DIR
from sd_generator_webui.services.session_metadata import SessionMetadataService
from sd_generator_webui.services.session_stats_service import SessionStatsService
from sd_generator_webui.models import (
    SessionMetadata,
    SessionMetadataUpdate,
    SessionStats
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Singletons
_metadata_service: Optional[SessionMetadataService] = None
_stats_service: Optional[SessionStatsService] = None


def get_metadata_service() -> SessionMetadataService:
    global _metadata_service
    if _metadata_service is None:
        _metadata_service = SessionMetadataService()
    return _metadata_service


def get_stats_service() -> SessionStatsService:
    global _stats_service
    if _stats_service is None:
        _stats_service = SessionStatsService()
    return _stats_service


# Response models
class SessionWithStatsAndMetadata(BaseModel):
    """Combined session info with stats and metadata."""
    session_id: str
    session_path: str
    created_at: str  # ISO 8601

    stats: Optional[SessionStats] = None
    metadata: Optional[SessionMetadata] = None


class SessionListResponse(BaseModel):
    sessions: List[SessionWithStatsAndMetadata]
    total_count: int
    limit: int
    offset: int


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    liked: Optional[bool] = Query(None, description="Filter by is_favorite"),
    test: Optional[bool] = Query(None, description="Filter by is_test"),
    complete: Optional[bool] = Query(None, description="Filter by completion >= 95%"),
    seed_sweep: Optional[bool] = Query(None, description="Filter by is_seed_sweep"),
    model: Optional[str] = Query(None, description="Filter by sd_model (partial match)"),
    from_date: Optional[str] = Query(None, description="Filter sessions after date (ISO 8601)"),
    to_date: Optional[str] = Query(None, description="Filter sessions before date (ISO 8601)"),
    limit: int = Query(100, ge=1, le=500, description="Max sessions to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    List all sessions with stats and metadata.

    Applies filters and returns paginated results.
    Stats are lazy-loaded (computed on first access, cached).
    """
    metadata_service = get_metadata_service()
    stats_service = get_stats_service()

    # Step 1: Get all session folders from filesystem
    all_sessions: List[SessionWithStatsAndMetadata] = []

    for session_dir in IMAGES_DIR.iterdir():
        if not session_dir.is_dir():
            continue

        session_id = session_dir.name

        # Parse created_at from folder name
        from sd_generator_webui.api.sessions import parse_session_datetime
        created_at = parse_session_datetime(session_id)
        if not created_at:
            continue  # Skip invalid session names

        # Step 2: Get or compute stats
        try:
            stats = stats_service.get_or_compute_stats(session_id)
            stats_obj = SessionStats(**stats)
        except Exception as e:
            # Log error but don't fail entire request
            print(f"[ERROR] Failed to get stats for {session_id}: {e}")
            stats_obj = None

        # Step 3: Get metadata (may not exist)
        metadata_obj = metadata_service.get_metadata(session_id)

        all_sessions.append(SessionWithStatsAndMetadata(
            session_id=session_id,
            session_path=str(session_dir),
            created_at=created_at.isoformat(),
            stats=stats_obj,
            metadata=metadata_obj
        ))

    # Step 4: Apply filters
    filtered_sessions = all_sessions

    if liked is not None:
        filtered_sessions = [
            s for s in filtered_sessions
            if s.metadata and s.metadata.is_favorite == liked
        ]

    if test is not None:
        filtered_sessions = [
            s for s in filtered_sessions
            if s.metadata and s.metadata.is_test == test
        ]

    if complete is not None:
        filtered_sessions = [
            s for s in filtered_sessions
            if s.stats and (s.stats.completion_percentage >= 95.0) == complete
        ]

    if seed_sweep is not None:
        filtered_sessions = [
            s for s in filtered_sessions
            if s.stats and s.stats.is_seed_sweep == seed_sweep
        ]

    if model is not None:
        model_lower = model.lower()
        filtered_sessions = [
            s for s in filtered_sessions
            if s.stats and s.stats.sd_model and model_lower in s.stats.sd_model.lower()
        ]

    if from_date is not None:
        filtered_sessions = [
            s for s in filtered_sessions
            if s.created_at >= from_date
        ]

    if to_date is not None:
        filtered_sessions = [
            s for s in filtered_sessions
            if s.created_at <= to_date
        ]

    # Step 5: Sort by created_at DESC
    filtered_sessions.sort(key=lambda s: s.created_at, reverse=True)

    # Step 6: Paginate
    total_count = len(filtered_sessions)
    paginated_sessions = filtered_sessions[offset:offset + limit]

    return SessionListResponse(
        sessions=paginated_sessions,
        total_count=total_count,
        limit=limit,
        offset=offset
    )


@router.get("/{session_name}/stats", response_model=SessionStats)
async def get_session_stats(
    session_name: str,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Get detailed stats for a specific session.

    If stats not cached, computes and caches them.
    """
    session_path = IMAGES_DIR / session_name

    if not session_path.exists() or not session_path.is_dir():
        raise HTTPException(status_code=404, detail="Session not found")

    stats_service = get_stats_service()

    try:
        stats = stats_service.get_or_compute_stats(session_name)
        return SessionStats(**stats)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="manifest.json not found")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Invalid manifest: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute stats: {str(e)}")


@router.post("/{session_name}/stats/refresh", response_model=SessionStats)
async def refresh_session_stats(
    session_name: str,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Force recompute stats for a session.

    Use when manifest.json or images have been modified.
    """
    session_path = IMAGES_DIR / session_name

    if not session_path.exists() or not session_path.is_dir():
        raise HTTPException(status_code=404, detail="Session not found")

    stats_service = get_stats_service()

    try:
        stats = stats_service.refresh_stats(session_name)
        return SessionStats(**stats)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="manifest.json not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recompute stats: {str(e)}")


@router.patch("/{session_name}/metadata", response_model=SessionMetadata)
async def update_session_metadata(
    session_name: str,
    update: SessionMetadataUpdate,
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Update metadata for a session.

    Creates metadata row if doesn't exist.
    """
    session_path = IMAGES_DIR / session_name

    if not session_path.exists() or not session_path.is_dir():
        raise HTTPException(status_code=404, detail="Session not found")

    metadata_service = get_metadata_service()
    metadata = metadata_service.upsert_metadata(
        session_id=session_name,
        session_path=str(session_path),
        update=update
    )

    return metadata


@router.get("/recent/liked", response_model=SessionListResponse)
async def get_recent_liked_sessions(
    limit: int = Query(10, ge=1, le=100),
    user_guid: str = Depends(AuthService.validate_guid)
):
    """
    Get recently liked sessions (shortcut).

    Equivalent to GET /sessions/?liked=true&limit={limit}
    """
    return await list_sessions(
        liked=True,
        limit=limit,
        offset=0,
        user_guid=user_guid
    )
```

---

### 3.2 Service Layer Updates

**No changes needed** - Feature 1 services (`SessionStatsService`, `SessionMetadataService`) already provide all necessary methods.

---

## 4. Frontend API Client

**File:** `/packages/sd-generator-webui/front/src/services/api.js` (additions)

```javascript
// Session stats endpoints
async getSessionStats(sessionName) {
  const response = await this.client.get(`/api/sessions/${sessionName}/stats`)
  return response.data
}

async refreshSessionStats(sessionName) {
  const response = await this.client.post(`/api/sessions/${sessionName}/stats/refresh`)
  return response.data
}

async getRecentLikedSessions(limit = 10) {
  const response = await this.client.get('/api/sessions/recent/liked', {
    params: { limit }
  })
  return response.data
}

// Enhanced getSessions with filters
async getSessions({
  liked = null,
  test = null,
  complete = null,
  seedSweep = null,
  model = null,
  fromDate = null,
  toDate = null,
  limit = 100,
  offset = 0
} = {}) {
  const params = { limit, offset }
  if (liked !== null) params.liked = liked
  if (test !== null) params.test = test
  if (complete !== null) params.complete = complete
  if (seedSweep !== null) params.seed_sweep = seedSweep
  if (model !== null) params.model = model
  if (fromDate !== null) params.from_date = fromDate
  if (toDate !== null) params.to_date = toDate

  const response = await this.client.get('/api/sessions/', { params })
  return response.data
}
```

---

## 5. Testing Strategy

### 5.1 API Integration Tests

**File:** `/packages/sd-generator-webui/backend/tests/integration/test_sessions_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from sd_generator_webui.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer valid-test-token"}

def test_list_sessions_with_filters(client, auth_headers):
    """Test GET /api/sessions/ with filters."""
    response = client.get(
        "/api/sessions/",
        params={"liked": True, "limit": 10},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "total_count" in data
    assert data["limit"] == 10

    # Verify all returned sessions have is_favorite=true
    for session in data["sessions"]:
        if session["metadata"]:
            assert session["metadata"]["is_favorite"] == True


def test_get_session_stats(client, auth_headers):
    """Test GET /api/sessions/:name/stats."""
    response = client.get(
        "/api/sessions/20251107_120000-test/stats",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "20251107_120000-test"
    assert "sd_model" in data
    assert "completion_percentage" in data


def test_update_metadata(client, auth_headers):
    """Test PATCH /api/sessions/:name/metadata."""
    response = client.patch(
        "/api/sessions/20251107_120000-test/metadata",
        json={"is_favorite": True, "tags": ["test", "demo"]},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_favorite"] == True
    assert data["tags"] == ["test", "demo"]


def test_refresh_stats(client, auth_headers):
    """Test POST /api/sessions/:name/stats/refresh."""
    response = client.post(
        "/api/sessions/20251107_120000-test/stats/refresh",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "stats_computed_at" in data
```

### 5.2 Performance Tests

```python
def test_list_sessions_performance(client, auth_headers):
    """Test that listing 100 sessions completes in <2s."""
    import time
    start = time.time()

    response = client.get(
        "/api/sessions/",
        params={"limit": 100},
        headers=auth_headers
    )

    elapsed = time.time() - start
    assert response.status_code == 200
    assert elapsed < 2.0  # Must complete in under 2 seconds
```

---

## 6. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Slow stats computation** blocks API response | Medium | High | Lazy-load stats in background. Return session list immediately, compute stats on-demand. Add loading state in UI. |
| **Large session lists** (1000+ sessions) timeout | Medium | Medium | Implement pagination (limit/offset). Add server-side caching with Redis (phase 2). |
| **Filters on uncached stats** are slow | Low | Medium | Compute stats for all sessions on startup (background task). Add CLI tool: `sdgen-admin warm-stats-cache`. |
| **Concurrent metadata updates** cause race conditions | Low | Low | SQLite handles ACID transactions. Use row-level locking (default in SQLite). |

---

## 7. Strategic Alignment

### 7.1 Enables Frontend Features

**Feature 3 (Session List):**
- Uses `GET /api/sessions/` with filters
- Displays stats in session cards (model, image count, completion badge)
- Filters by liked/test/seed-sweep flags

**Feature 4 (Session Details Panel):**
- Uses `GET /api/sessions/:name/stats` for full stats
- Displays placeholders, variations, API params

**Feature 5 (Editable Metadata):**
- Uses `PATCH /api/sessions/:name/metadata` for auto-save
- Debounces tag edits to avoid excessive API calls

---

## 8. Success Criteria

1. **Performance:** `GET /api/sessions/` returns 100 sessions in <2s
2. **Correctness:** Filters return accurate results (tested on 50 sessions)
3. **Reliability:** Stats computation errors don't break session list (graceful degradation)
4. **Caching:** Second call to `GET /api/sessions/:name/stats` returns instantly (<50ms)
5. **Type safety:** All endpoints have Pydantic models with mypy validation

---

## 9. Implementation Checklist

- [ ] Refactor `/api/sessions/` endpoint with filters
- [ ] Add `GET /api/sessions/:name/stats` endpoint
- [ ] Add `POST /api/sessions/:name/stats/refresh` endpoint
- [ ] Update `PATCH /api/sessions/:name/metadata` (already exists, verify behavior)
- [ ] Add `GET /api/sessions/recent/liked` shortcut
- [ ] Update `api.js` frontend client with new methods
- [ ] Add Pydantic response models (`SessionWithStatsAndMetadata`, `SessionListResponse`)
- [ ] Write API integration tests (5 test cases)
- [ ] Test filters with real data (20 sessions)
- [ ] Add logging for errors (stats computation failures)
- [ ] Verify mypy strict mode passes

---

## 10. Files to Create/Modify

### Modified Files
- `/packages/sd-generator-webui/backend/sd_generator_webui/api/sessions.py` (major refactor, +200 lines)
- `/packages/sd-generator-webui/front/src/services/api.js` (+50 lines)

### New Files
- `/packages/sd-generator-webui/backend/tests/integration/test_sessions_api.py` (200 lines)

---

## 11. Next Steps

After this feature is complete:
1. **Feature 3** can fetch sessions via `GET /api/sessions/` and render session list
2. **Feature 4** can fetch detailed stats via `GET /api/sessions/:name/stats`
3. **Feature 5** can update metadata via `PATCH /api/sessions/:name/metadata` with auto-save
