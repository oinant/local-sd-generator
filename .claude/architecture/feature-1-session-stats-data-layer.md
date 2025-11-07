# Technical Architecture Document: Feature 1 - Session Statistics Data Layer

**Feature ID:** F1-SESSION-STATS-DATA
**Status:** Architecture Complete
**Created:** 2025-11-07
**Owner:** Technical Architect Agent
**Dependencies:** None
**Estimated Effort:** 2-3h

---

## 1. Overview

### 1.1 Problem Statement
The current `session_metadata` table only stores user-editable metadata (tags, flags, ratings). We need to **auto-compute and cache comprehensive session statistics** (model info, image counts, placeholders, variations, timestamps, completion status) from `manifest.json` and filesystem data.

### 1.2 Goals
1. **Efficient stats computation** - Avoid re-parsing manifest.json on every API request
2. **Session type detection** - Distinguish normal sessions from seed-sweep sessions
3. **Completion tracking** - Calculate % completion based on expected vs actual image counts
4. **Strategic foundation** - Enable #70 (variation rating), #61 (image tagging), model-specific analysis

### 1.3 Non-Goals
- UI implementation (handled by Features 3-5)
- Real-time session monitoring during generation
- Stats for sessions without manifest.json (legacy support is phase 2)

---

## 2. Technical Design

### 2.1 Database Schema

#### 2.1.1 New Table: `session_stats`

```sql
CREATE TABLE session_stats (
    session_id TEXT PRIMARY KEY,                -- Session folder name (e.g., "20251014_173320-facial_expressions")
    session_path TEXT NOT NULL,                 -- Full absolute path to session folder

    -- Generation metadata (from manifest.json snapshot)
    sd_model TEXT,                              -- Model checkpoint name (e.g., "illustriousXL_v01.safetensors")
    template_version TEXT,                      -- Template system version (e.g., "2.0")
    generation_mode TEXT,                       -- "combinatorial" or "random"
    seed_mode TEXT,                             -- "fixed", "progressive", or "random"
    seed_base INTEGER,                          -- Base seed used

    -- Prompt information
    resolved_prompt TEXT,                       -- Full resolved prompt template (with placeholders)
    negative_prompt TEXT,                       -- Negative prompt used

    -- API parameters
    width INTEGER,
    height INTEGER,
    steps INTEGER,
    cfg_scale REAL,
    sampler_name TEXT,

    -- Image counts
    images_expected INTEGER,                    -- Expected images (from manifest.json max_images or computed)
    images_actual INTEGER,                      -- Actual images found in filesystem
    completion_percentage REAL,                 -- (images_actual / images_expected) * 100

    -- Session type detection
    is_seed_sweep INTEGER DEFAULT 0,            -- 1 if seed_mode = "progressive" + single placeholder variation

    -- Placeholders and variations
    placeholders_json TEXT,                     -- JSON: {"HairStyle": 15, "Expression": 20, ...}
    variations_summary_json TEXT,               -- JSON: {"HairStyle": ["bob", "ponytail", ...], ...} (first 10 per placeholder)

    -- Timestamps
    session_created_at TEXT,                    -- Parsed from folder name (YYYYMMDD_HHMMSS)
    manifest_generated_at TEXT,                 -- From manifest.json timestamp field
    first_image_created_at TEXT,                -- Filesystem mtime of first image
    last_image_created_at TEXT,                 -- Filesystem mtime of last image

    -- Stats cache metadata
    stats_computed_at TEXT NOT NULL,            -- When stats were last computed (ISO 8601)
    stats_version INTEGER DEFAULT 1,            -- Schema version for migrations

    FOREIGN KEY (session_id) REFERENCES session_metadata(session_id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX idx_session_stats_model ON session_stats(sd_model);
CREATE INDEX idx_session_stats_seed_sweep ON session_stats(is_seed_sweep);
CREATE INDEX idx_session_stats_completion ON session_stats(completion_percentage);
CREATE INDEX idx_session_stats_created_at ON session_stats(session_created_at DESC);
```

#### 2.1.2 Schema Rationale

**Why separate `session_stats` from `session_metadata`?**
- **Separation of concerns**: User data (metadata) vs computed data (stats)
- **Update frequency**: Metadata changes frequently (user edits), stats computed once/rarely
- **Performance**: Can cache stats independently of metadata writes
- **Foreign key cascade**: Deleting metadata auto-deletes stats

**Why JSON fields for placeholders/variations?**
- Flexible schema (placeholders vary per template)
- Efficient storage (one row per session, not N rows for N placeholders)
- Easy to query with SQLite JSON functions (`json_extract`)

**Why track both expected and actual image counts?**
- Detect incomplete sessions (generation interrupted)
- Calculate completion % for UI badges
- Support seed-sweep analysis (N seeds × M variations = expected)

---

### 2.2 Stats Calculation Logic

#### 2.2.1 StatsCalculator Class

**File:** `/packages/sd-generator-webui/backend/sd_generator_webui/services/stats_calculator.py`

```python
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import re

class SessionStatsCalculator:
    """Calculate comprehensive session statistics from manifest.json and filesystem."""

    def __init__(self, session_path: Path):
        self.session_path = session_path
        self.session_id = session_path.name
        self.manifest_path = session_path / "manifest.json"
        self.manifest_data: Optional[Dict[str, Any]] = None

    def compute_stats(self) -> Dict[str, Any]:
        """
        Compute all session statistics.

        Returns:
            Dict with all stats fields (matches session_stats table schema)

        Raises:
            FileNotFoundError: If manifest.json not found
            ValueError: If manifest.json is invalid
        """
        # 1. Load and validate manifest.json
        self._load_manifest()

        # 2. Extract metadata from manifest
        snapshot = self.manifest_data.get("snapshot", {})
        gen_params = snapshot.get("generation_params", {})
        api_params = snapshot.get("api_params", {})
        runtime_info = snapshot.get("runtime_info", {})
        variations = snapshot.get("variations", {})

        # 3. Count actual images in filesystem
        images_actual = self._count_images()

        # 4. Compute expected images
        images_expected = self._compute_expected_images(
            gen_params.get("mode"),
            gen_params.get("max_images"),
            variations
        )

        # 5. Detect session type
        is_seed_sweep = self._detect_seed_sweep(
            gen_params.get("seed_mode"),
            variations
        )

        # 6. Parse timestamps
        session_created_at = self._parse_session_datetime(self.session_id)
        first_image_ts, last_image_ts = self._get_image_timestamps()

        # 7. Extract placeholders and variations
        placeholders_json = json.dumps(self._extract_placeholder_counts(variations))
        variations_summary_json = json.dumps(self._extract_variations_summary(variations))

        # 8. Compute completion percentage
        completion_percentage = (images_actual / images_expected * 100.0) if images_expected > 0 else 0.0

        return {
            "session_id": self.session_id,
            "session_path": str(self.session_path),
            "sd_model": runtime_info.get("sd_model_checkpoint", "unknown"),
            "template_version": snapshot.get("version", "unknown"),
            "generation_mode": gen_params.get("mode", "unknown"),
            "seed_mode": gen_params.get("seed_mode", "unknown"),
            "seed_base": gen_params.get("seed_base", -1),
            "resolved_prompt": snapshot.get("resolved_template", {}).get("prompt", ""),
            "negative_prompt": snapshot.get("resolved_template", {}).get("negative", ""),
            "width": api_params.get("width"),
            "height": api_params.get("height"),
            "steps": api_params.get("steps"),
            "cfg_scale": api_params.get("cfg_scale"),
            "sampler_name": api_params.get("sampler_name"),
            "images_expected": images_expected,
            "images_actual": images_actual,
            "completion_percentage": round(completion_percentage, 2),
            "is_seed_sweep": 1 if is_seed_sweep else 0,
            "placeholders_json": placeholders_json,
            "variations_summary_json": variations_summary_json,
            "session_created_at": session_created_at.isoformat() if session_created_at else None,
            "manifest_generated_at": snapshot.get("timestamp"),
            "first_image_created_at": first_image_ts.isoformat() if first_image_ts else None,
            "last_image_created_at": last_image_ts.isoformat() if last_image_ts else None,
            "stats_computed_at": datetime.now().isoformat(),
            "stats_version": 1
        }

    def _load_manifest(self) -> None:
        """Load and validate manifest.json."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"manifest.json not found in {self.session_path}")

        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            self.manifest_data = json.load(f)

        if not self.manifest_data.get("snapshot"):
            raise ValueError("Invalid manifest.json: missing 'snapshot' field")

    def _count_images(self) -> int:
        """Count actual image files in session folder."""
        extensions = [".png", ".jpg", ".jpeg", ".webp"]
        count = 0
        for ext in extensions:
            count += len(list(self.session_path.glob(f"*{ext}")))
        return count

    def _compute_expected_images(
        self,
        mode: Optional[str],
        max_images: Optional[int],
        variations: Dict[str, Any]
    ) -> int:
        """
        Compute expected image count based on generation mode.

        - Combinatorial: product of all variation counts
        - Random: max_images from manifest
        """
        if mode == "combinatorial":
            # Compute product of all placeholder variation counts
            total = 1
            for placeholder, data in variations.items():
                used_count = len(data.get("used", []))
                if used_count > 0:
                    total *= used_count
            return total
        else:
            # Random mode: use max_images
            return max_images or 0

    def _detect_seed_sweep(
        self,
        seed_mode: Optional[str],
        variations: Dict[str, Any]
    ) -> bool:
        """
        Detect if session is a seed-sweep.

        Criteria:
        - seed_mode = "progressive"
        - Only 1 placeholder with multiple variations OR all placeholders have 1 variation
        """
        if seed_mode != "progressive":
            return False

        # Count placeholders with >1 variation
        multi_variation_placeholders = 0
        for data in variations.values():
            if len(data.get("used", [])) > 1:
                multi_variation_placeholders += 1

        # Seed sweep: either 1 multi-variation placeholder, or all single variations
        return multi_variation_placeholders <= 1

    def _parse_session_datetime(self, session_name: str) -> Optional[datetime]:
        """
        Parse datetime from session folder name.

        Supports formats:
        - Old: 2025-10-14_173320_name.prompt
        - New: 20251014_173320-name
        """
        # Try old format: YYYY-MM-DD_HHMMSS
        match = re.match(r'^(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})(\d{2})', session_name)
        if match:
            year, month, day, hour, minute, second = map(int, match.groups())
            try:
                return datetime(year, month, day, hour, minute, second)
            except ValueError:
                pass

        # Try new format: YYYYMMDD_HHMMSS
        match = re.match(r'^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', session_name)
        if match:
            year, month, day, hour, minute, second = map(int, match.groups())
            try:
                return datetime(year, month, day, hour, minute, second)
            except ValueError:
                pass

        return None

    def _get_image_timestamps(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """Get first and last image creation timestamps from filesystem."""
        image_files: List[Path] = []
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            image_files.extend(self.session_path.glob(f"*{ext}"))

        if not image_files:
            return None, None

        # Sort by mtime
        image_files.sort(key=lambda p: p.stat().st_mtime)

        first_ts = datetime.fromtimestamp(image_files[0].stat().st_mtime)
        last_ts = datetime.fromtimestamp(image_files[-1].stat().st_mtime)

        return first_ts, last_ts

    def _extract_placeholder_counts(self, variations: Dict[str, Any]) -> Dict[str, int]:
        """Extract placeholder names and their variation counts."""
        return {
            placeholder: len(data.get("used", []))
            for placeholder, data in variations.items()
        }

    def _extract_variations_summary(
        self,
        variations: Dict[str, Any],
        max_per_placeholder: int = 10
    ) -> Dict[str, List[str]]:
        """
        Extract first N variations per placeholder (for UI preview).

        Args:
            variations: Variations dict from manifest
            max_per_placeholder: Max variations to include per placeholder
        """
        summary = {}
        for placeholder, data in variations.items():
            used = data.get("used", [])
            summary[placeholder] = used[:max_per_placeholder]
        return summary
```

---

#### 2.2.2 SessionStatsService Integration

**File:** `/packages/sd-generator-webui/backend/sd_generator_webui/services/session_stats_service.py`

```python
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from sd_generator_webui.config import METADATA_DIR, IMAGES_DIR
from sd_generator_webui.services.stats_calculator import SessionStatsCalculator


class SessionStatsService:
    """Service for managing session stats in SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = METADATA_DIR / "sessions.db"

        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Create session_stats table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_stats (
                    session_id TEXT PRIMARY KEY,
                    session_path TEXT NOT NULL,
                    sd_model TEXT,
                    template_version TEXT,
                    generation_mode TEXT,
                    seed_mode TEXT,
                    seed_base INTEGER,
                    resolved_prompt TEXT,
                    negative_prompt TEXT,
                    width INTEGER,
                    height INTEGER,
                    steps INTEGER,
                    cfg_scale REAL,
                    sampler_name TEXT,
                    images_expected INTEGER,
                    images_actual INTEGER,
                    completion_percentage REAL,
                    is_seed_sweep INTEGER DEFAULT 0,
                    placeholders_json TEXT,
                    variations_summary_json TEXT,
                    session_created_at TEXT,
                    manifest_generated_at TEXT,
                    first_image_created_at TEXT,
                    last_image_created_at TEXT,
                    stats_computed_at TEXT NOT NULL,
                    stats_version INTEGER DEFAULT 1,
                    FOREIGN KEY (session_id) REFERENCES session_metadata(session_id) ON DELETE CASCADE
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_stats_model ON session_stats(sd_model)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_stats_seed_sweep ON session_stats(is_seed_sweep)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_stats_completion ON session_stats(completion_percentage)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_stats_created_at ON session_stats(session_created_at DESC)")

            conn.commit()

    def compute_and_cache_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Compute stats for a session and cache them in database.

        Args:
            session_id: Session folder name

        Returns:
            Computed stats dict

        Raises:
            FileNotFoundError: If session or manifest not found
            ValueError: If manifest is invalid
        """
        session_path = IMAGES_DIR / session_id
        if not session_path.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        # Compute stats
        calculator = SessionStatsCalculator(session_path)
        stats = calculator.compute_stats()

        # Upsert into database
        self._upsert_stats(stats)

        return stats

    def get_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached stats for a session.

        Returns None if stats not cached.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM session_stats WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return dict(row)

    def get_or_compute_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get cached stats or compute if not cached.

        This is the main entry point for API endpoints.
        """
        stats = self.get_stats(session_id)
        if stats is None:
            stats = self.compute_and_cache_stats(session_id)
        return stats

    def refresh_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Force recompute stats (for POST /stats/refresh endpoint).
        """
        return self.compute_and_cache_stats(session_id)

    def list_all_stats(self) -> List[Dict[str, Any]]:
        """List all cached session stats."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM session_stats ORDER BY session_created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_stats(self, session_id: str) -> bool:
        """Delete cached stats for a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM session_stats WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def _upsert_stats(self, stats: Dict[str, Any]) -> None:
        """Insert or update stats in database."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if exists
            cursor = conn.execute(
                "SELECT session_id FROM session_stats WHERE session_id = ?",
                (stats["session_id"],)
            )
            exists = cursor.fetchone() is not None

            if exists:
                # Update
                conn.execute("""
                    UPDATE session_stats SET
                        session_path = ?,
                        sd_model = ?,
                        template_version = ?,
                        generation_mode = ?,
                        seed_mode = ?,
                        seed_base = ?,
                        resolved_prompt = ?,
                        negative_prompt = ?,
                        width = ?,
                        height = ?,
                        steps = ?,
                        cfg_scale = ?,
                        sampler_name = ?,
                        images_expected = ?,
                        images_actual = ?,
                        completion_percentage = ?,
                        is_seed_sweep = ?,
                        placeholders_json = ?,
                        variations_summary_json = ?,
                        session_created_at = ?,
                        manifest_generated_at = ?,
                        first_image_created_at = ?,
                        last_image_created_at = ?,
                        stats_computed_at = ?,
                        stats_version = ?
                    WHERE session_id = ?
                """, (
                    stats["session_path"],
                    stats["sd_model"],
                    stats["template_version"],
                    stats["generation_mode"],
                    stats["seed_mode"],
                    stats["seed_base"],
                    stats["resolved_prompt"],
                    stats["negative_prompt"],
                    stats["width"],
                    stats["height"],
                    stats["steps"],
                    stats["cfg_scale"],
                    stats["sampler_name"],
                    stats["images_expected"],
                    stats["images_actual"],
                    stats["completion_percentage"],
                    stats["is_seed_sweep"],
                    stats["placeholders_json"],
                    stats["variations_summary_json"],
                    stats["session_created_at"],
                    stats["manifest_generated_at"],
                    stats["first_image_created_at"],
                    stats["last_image_created_at"],
                    stats["stats_computed_at"],
                    stats["stats_version"],
                    stats["session_id"]
                ))
            else:
                # Insert
                conn.execute("""
                    INSERT INTO session_stats (
                        session_id, session_path, sd_model, template_version,
                        generation_mode, seed_mode, seed_base,
                        resolved_prompt, negative_prompt,
                        width, height, steps, cfg_scale, sampler_name,
                        images_expected, images_actual, completion_percentage,
                        is_seed_sweep, placeholders_json, variations_summary_json,
                        session_created_at, manifest_generated_at,
                        first_image_created_at, last_image_created_at,
                        stats_computed_at, stats_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stats["session_id"],
                    stats["session_path"],
                    stats["sd_model"],
                    stats["template_version"],
                    stats["generation_mode"],
                    stats["seed_mode"],
                    stats["seed_base"],
                    stats["resolved_prompt"],
                    stats["negative_prompt"],
                    stats["width"],
                    stats["height"],
                    stats["steps"],
                    stats["cfg_scale"],
                    stats["sampler_name"],
                    stats["images_expected"],
                    stats["images_actual"],
                    stats["completion_percentage"],
                    stats["is_seed_sweep"],
                    stats["placeholders_json"],
                    stats["variations_summary_json"],
                    stats["session_created_at"],
                    stats["manifest_generated_at"],
                    stats["first_image_created_at"],
                    stats["last_image_created_at"],
                    stats["stats_computed_at"],
                    stats["stats_version"]
                ))

            conn.commit()
```

---

## 3. Data Models (Pydantic)

**File:** `/packages/sd-generator-webui/backend/sd_generator_webui/models.py` (additions)

```python
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class SessionStats(BaseModel):
    """Computed session statistics."""
    session_id: str
    session_path: str

    # Generation metadata
    sd_model: Optional[str] = None
    template_version: Optional[str] = None
    generation_mode: Optional[str] = None
    seed_mode: Optional[str] = None
    seed_base: Optional[int] = None

    # Prompts
    resolved_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None

    # API parameters
    width: Optional[int] = None
    height: Optional[int] = None
    steps: Optional[int] = None
    cfg_scale: Optional[float] = None
    sampler_name: Optional[str] = None

    # Image counts
    images_expected: int
    images_actual: int
    completion_percentage: float

    # Session type
    is_seed_sweep: bool = False

    # Placeholders and variations
    placeholders: Dict[str, int] = Field(default_factory=dict)  # {"HairStyle": 15, ...}
    variations_summary: Dict[str, List[str]] = Field(default_factory=dict)  # {"HairStyle": ["bob", ...], ...}

    # Timestamps
    session_created_at: Optional[str] = None
    manifest_generated_at: Optional[str] = None
    first_image_created_at: Optional[str] = None
    last_image_created_at: Optional[str] = None

    # Stats metadata
    stats_computed_at: str
    stats_version: int = 1
```

---

## 4. Testing Strategy

### 4.1 Unit Tests

**File:** `/packages/sd-generator-webui/backend/tests/unit/services/test_stats_calculator.py`

```python
import pytest
from pathlib import Path
from sd_generator_webui.services.stats_calculator import SessionStatsCalculator

def test_compute_stats_combinatorial(tmp_path):
    """Test stats computation for combinatorial session."""
    # Setup: Create mock session with manifest
    session_path = tmp_path / "20251107_120000-test_session"
    session_path.mkdir()

    manifest = {
        "snapshot": {
            "version": "2.0",
            "timestamp": "2025-11-07T12:00:00",
            "runtime_info": {"sd_model_checkpoint": "test_model.safetensors"},
            "generation_params": {
                "mode": "combinatorial",
                "seed_mode": "progressive",
                "seed_base": 42,
                "max_images": 100
            },
            "api_params": {
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.0,
                "sampler_name": "DPM++ 2M"
            },
            "resolved_template": {
                "prompt": "test prompt {Hair} {Expression}",
                "negative": "test negative"
            },
            "variations": {
                "Hair": {"used": ["bob", "ponytail", "braid"]},
                "Expression": {"used": ["smile", "sad"]}
            }
        },
        "images": []
    }

    import json
    (session_path / "manifest.json").write_text(json.dumps(manifest))

    # Create 6 dummy images (3 hair × 2 expressions = 6 expected)
    for i in range(6):
        (session_path / f"image_{i:03d}.png").touch()

    # Test
    calculator = SessionStatsCalculator(session_path)
    stats = calculator.compute_stats()

    assert stats["session_id"] == "20251107_120000-test_session"
    assert stats["sd_model"] == "test_model.safetensors"
    assert stats["generation_mode"] == "combinatorial"
    assert stats["images_expected"] == 6  # 3 × 2
    assert stats["images_actual"] == 6
    assert stats["completion_percentage"] == 100.0
    assert stats["is_seed_sweep"] == 0  # Multiple placeholders
    assert json.loads(stats["placeholders_json"]) == {"Hair": 3, "Expression": 2}


def test_detect_seed_sweep(tmp_path):
    """Test seed-sweep detection."""
    session_path = tmp_path / "20251107_120000-seed_sweep"
    session_path.mkdir()

    manifest = {
        "snapshot": {
            "version": "2.0",
            "timestamp": "2025-11-07T12:00:00",
            "runtime_info": {"sd_model_checkpoint": "test.safetensors"},
            "generation_params": {
                "mode": "random",
                "seed_mode": "progressive",  # Key: progressive seed
                "seed_base": 42,
                "max_images": 50
            },
            "api_params": {"width": 512, "height": 512, "steps": 20},
            "resolved_template": {"prompt": "test", "negative": ""},
            "variations": {
                "HairStyle": {"used": ["bob"]}  # Single variation
            }
        },
        "images": []
    }

    import json
    (session_path / "manifest.json").write_text(json.dumps(manifest))

    calculator = SessionStatsCalculator(session_path)
    stats = calculator.compute_stats()

    assert stats["is_seed_sweep"] == 1  # Progressive seed + 1 placeholder
```

### 4.2 Integration Tests

**File:** `/packages/sd-generator-webui/backend/tests/integration/test_session_stats_service.py`

```python
import pytest
from pathlib import Path
from sd_generator_webui.services.session_stats_service import SessionStatsService

def test_compute_and_cache_stats(tmp_path):
    """Test full compute-and-cache workflow."""
    # Setup database and session
    db_path = tmp_path / "test.db"
    service = SessionStatsService(db_path)

    # ... (setup mock session with manifest) ...

    # Compute and cache
    stats = service.compute_and_cache_stats("20251107_120000-test")

    # Verify cached
    cached_stats = service.get_stats("20251107_120000-test")
    assert cached_stats is not None
    assert cached_stats["session_id"] == "20251107_120000-test"
    assert cached_stats["completion_percentage"] == 100.0
```

---

## 5. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Large manifest.json files** (100k+ images) slow computation | Medium | Medium | Cache stats in DB, compute once. Add `--force-refresh` CLI tool for manual recompute. |
| **Incomplete sessions** (missing manifest.json) break stats | Low | High | Gracefully handle missing manifest: return partial stats (filesystem-only). Phase 2: infer stats from PNG metadata. |
| **Schema changes** break cached stats | Medium | Low | Use `stats_version` field for migrations. Drop and recompute stats on schema change. |
| **Foreign key constraint** blocks session deletion | Low | Medium | Use `ON DELETE CASCADE` to auto-delete stats when metadata is deleted. |

---

## 6. Strategic Alignment

### 6.1 Enables Future Features

**Feature #70 (Variation Rating):**
- Uses `placeholders` and `variations_summary` to build rating UI
- Filters images by placeholder value for side-by-side comparison
- Example: "Rate all HairStyle=bob variations" → query by `variations_summary.HairStyle`

**Feature #61 (Image Tagging):**
- Uses `session_created_at` and `sd_model` for batch tagging workflows
- Example: "Tag all images from model X generated after date Y"

**Model-Specific Analysis:**
- Query by `sd_model` to aggregate stats across sessions
- Example: "Show all sessions using model XYZ, average completion rate"
- Index on `sd_model` makes this efficient

**Seed-Sweep Analysis:**
- Filter by `is_seed_sweep = 1` to find seed experiments
- Compare `seed_base` across sessions to track seed performance

---

## 7. Success Criteria

1. **Performance:** Stats computation takes <500ms for sessions with 100 images, <2s for 1000 images
2. **Accuracy:** Completion percentage matches manual count (tested on 20 real sessions)
3. **Coverage:** Stats available for 100% of sessions with valid manifest.json
4. **Type detection:** Seed-sweep detection accuracy >95% (tested on 50 sessions)
5. **Database:** SQLite queries with indexes return stats in <50ms

---

## 8. Implementation Checklist

- [ ] Create `session_stats` table with indexes
- [ ] Implement `SessionStatsCalculator` class
- [ ] Implement `SessionStatsService` class
- [ ] Add Pydantic `SessionStats` model
- [ ] Write unit tests for calculator (5 test cases)
- [ ] Write integration tests for service (3 test cases)
- [ ] Add mypy type hints (strict mode)
- [ ] Test on 20 real sessions from `/mnt/d/StableDiffusion/private-new/results/`
- [ ] Document edge cases (missing manifest, incomplete sessions)
- [ ] Add logging for stats computation errors

---

## 9. Files to Create/Modify

### New Files
- `/packages/sd-generator-webui/backend/sd_generator_webui/services/stats_calculator.py` (300 lines)
- `/packages/sd-generator-webui/backend/sd_generator_webui/services/session_stats_service.py` (200 lines)
- `/packages/sd-generator-webui/backend/tests/unit/services/test_stats_calculator.py` (150 lines)
- `/packages/sd-generator-webui/backend/tests/integration/test_session_stats_service.py` (100 lines)

### Modified Files
- `/packages/sd-generator-webui/backend/sd_generator_webui/models.py` (add `SessionStats` model)
- `/packages/sd-generator-webui/backend/sd_generator_webui/services/session_metadata.py` (add foreign key to metadata table)

---

## 10. Next Steps

After this feature is complete:
1. **Feature 2** can implement API endpoints that use `SessionStatsService`
2. **Feature 3** can fetch stats via API and display in session list
3. **CLI tool** can be added for batch stats computation: `sdgen-admin compute-stats --all`
