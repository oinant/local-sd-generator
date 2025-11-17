# Gallery Filtering Feature - Design Document

**Created:** 2025-11-14
**Status:** Design Phase
**Component:** WebUI - Gallery View

---

## Feature Overview

**User Story:**
> En tant qu'utilisateur, je veux filtrer les images d'une session par valeurs de placeholder pour retrouver rapidement des variants spécifiques et inspecter la cohérence des effets.

**Primary Use Case:**
- **Inspection d'effet cohérent** - "Est-ce que le terme 'smiling' génère des sourires cohérents ?"
- Parcourir un subset filtré (ex: 150/6000 images) pour validation visuelle
- Affiner avec combinaisons (ex: blonde + smiling)

---

## UI Design

### Filter Panel (Sidebar or Top Bar)

```
┌─────────────────────────────────────┐
│ Filters                   [×] Clear │
├─────────────────────────────────────┤
│ HairColor (12 variants)             │
│ ☐ blonde         ☐ brown            │
│ ☑ red            ☐ black            │
│ ☑ blue           ☐ green            │
│ ☐ pink           ☐ ...              │
│                                     │
│ Expression (8 variants)             │
│ ☑ smiling        ☐ sad              │
│ ☐ angry          ☐ neutral          │
│ ☐ ...                               │
│                                     │
│ Pose (15 variants)                  │
│ ☐ standing       ☐ sitting          │
│ ☐ lying          ☐ ...              │
│                                     │
│ Seed (special)                      │
│ ☐ 1000   ☐ 1001   ☐ 1002   ☐ ...   │
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ 📋 [Copy Filter]  📥 Paste Filter   │
│ [Clear Filters]                     │
│                                     │
│ Showing: 23 / 6,000 images          │
└─────────────────────────────────────┘
```

### Filter Logic

**Intra-placeholder (OR):**
- `HairColor = red OR blue`

**Inter-placeholder (AND):**
- `(HairColor = red OR blue) AND (Expression = smiling)`

**Seed as special placeholder:**
- Treated like any other placeholder
- OR logic within seeds

**SQL Equivalent:**
```sql
WHERE (hair_color IN ('red', 'blue'))
  AND (expression = 'smiling')
  AND (seed IN (1000, 1001))
```

---

## User Experience

### Gallery Behavior
1. **Filtered view** - Only matching thumbnails displayed
2. **Counter** - "Showing: 23 / 6,000 images"
3. **Empty state** - "No images match your filters" (if 0 results)

### Navigation
- **Prev/Next in popup** - Navigate ONLY within filtered subset
- **Fullscreen mode** - Same, navigation limited to filtered images
- **Keyboard shortcuts** - Arrow keys respect filter

### Filter State
- **URL-based** - Filters encoded in URL for sharing/bookmarking
  - Example: `?filters=HairColor:red,blue|Expression:smiling|Seed:1000`
- **Copy/Paste** - Quick filter sharing between users
  - Copy: Copies filter URL to clipboard
  - Paste: Input field to paste filter string

### Performance Considerations
- **Large sessions** - 6000 images × ~20KB thumbnail = ~120MB
- **Viewport optimization** - Only 18 thumbnails visible (6×3 grid)
- **Lazy loading challenge** - Filtering brings unloaded images into viewport
  - Must trigger thumbnail fetch for newly visible images

---

## Technical Decisions

### Decision 1: Frontend vs Backend Filtering

#### Option A: Frontend Filtering (JavaScript)

**Architecture:**
```
User selects filters
  ↓
Filter applied in-memory (JS)
  ↓
Gallery re-renders with filtered subset
  ↓
Lazy load thumbnails for newly visible images
```

**Pros:**
- ✅ No backend changes required
- ✅ Instant filtering (no network roundtrip)
- ✅ Works offline (if manifest cached)
- ✅ Simpler implementation (v1)
- ✅ No additional API endpoints

**Cons:**
- ⚠️ Must load entire manifest in memory (~1-2MB for 6000 images)
- ⚠️ Filtering 6000 items in JS may be slow on weak devices
- ⚠️ Complexity with lazy loading (filtered images may not be loaded yet)
- ⚠️ No pagination (all results shown at once)

**Performance Estimate:**
- Manifest size: ~300 bytes per image × 6000 = ~1.8MB
- Filter time: ~10-50ms for 6000 items (acceptable)
- Bottleneck: Lazy loading thumbnails when filter changes

---

#### Option B: Backend Filtering (API)

**Architecture:**
```
User selects filters
  ↓
API request: GET /api/sessions/:id/images?filters=...
  ↓
Backend filters manifest + returns paginated results
  ↓
Gallery renders page 1
  ↓
User scrolls → Fetch page 2
```

**Pros:**
- ✅ Handles massive sessions (10,000+ images)
- ✅ Pagination built-in (load 50 images at a time)
- ✅ Thumbnails loaded on-demand (no lazy loading complexity)
- ✅ Lower memory footprint on frontend
- ✅ Can add sorting (by seed, by filename, etc.)
- ✅ Future-proof for advanced features (search, date filters, etc.)

**Cons:**
- ⚠️ Requires new API endpoint
- ⚠️ Network latency on each filter change (~100-200ms)
- ⚠️ Doesn't work offline
- ⚠️ More complex implementation
- ⚠️ Backend must parse manifest for each request (caching needed)

**Performance Estimate:**
- API response time: ~50-100ms (manifest in memory)
- Pagination: 50 images per page = ~15KB response
- Filter change: ~150ms total (API + render)

---

#### Option C: Hybrid Approach

**Architecture:**
```
Load manifest in frontend (1.8MB)
  ↓
Filter in JS (instant)
  ↓
Request thumbnails for visible filtered images only
```

**Pros:**
- ✅ Instant filtering (no API call)
- ✅ Thumbnails fetched on-demand
- ✅ No backend changes for filtering logic
- ✅ Works for most sessions (<10,000 images)

**Cons:**
- ⚠️ Manifest loaded in full (memory usage)
- ⚠️ Complex lazy loading logic
- ⚠️ Doesn't scale to 50,000+ images

---

### Recommendation: Start with Option A (Frontend), Plan for Option B

**Rationale:**
1. **v1 (MVP)** - Frontend filtering for simplicity
   - Target: Sessions < 10,000 images
   - Acceptable performance on modern browsers
   - Fast iteration

2. **v2 (Scale)** - Backend API if performance issues arise
   - Add pagination
   - Optimize for 50,000+ images

**Migration path:**
- Keep filter logic in shared module
- Swap implementation (frontend → API) without changing UI

---

## Implementation Plan

### Phase 1: Data Extraction (Backend)

**Ensure manifest contains all needed data:**
```json
{
  "images": [
    {
      "filename": "image_0001.png",
      "seed": 1000,
      "applied_variations": {
        "HairColor": "red",
        "Expression": "smiling",
        "Pose": "standing"
      }
    }
  ]
}
```

**Task:** Validate manifest structure (already done in new arch)

---

### Phase 2: Filter State Management (Frontend)

**Components:**
1. **FilterState** (Vuex store or Pinia)
   ```typescript
   interface FilterState {
     filters: {
       [placeholder: string]: string[]  // Selected values
     }
     availablePlaceholders: {
       [placeholder: string]: string[]  // All possible values
     }
     filteredImages: Image[]
   }
   ```

2. **URL Sync**
   ```typescript
   // Encode filters in URL
   ?filters=HairColor:red,blue|Expression:smiling|Seed:1000

   // Decode on page load
   parseFiltersFromURL(queryString): FilterState
   ```

3. **Filter Logic**
   ```typescript
   function applyFilters(images: Image[], filters: FilterState): Image[] {
     return images.filter(img => {
       // For each placeholder filter
       for (const [placeholder, selectedValues] of Object.entries(filters)) {
         if (selectedValues.length === 0) continue  // No filter

         // OR logic within placeholder
         const imgValue = img.applied_variations[placeholder]
         if (!selectedValues.includes(imgValue)) {
           return false  // AND logic: must match ALL placeholders
         }
       }
       return true
     })
   }
   ```

---

### Phase 3: Filter Panel UI (Vue Component)

**Component: `FilterPanel.vue`**
```vue
<template>
  <div class="filter-panel">
    <div class="filter-header">
      <h3>Filters</h3>
      <button @click="clearFilters">Clear</button>
    </div>

    <!-- For each placeholder -->
    <div
      v-for="(values, placeholder) in availablePlaceholders"
      :key="placeholder"
      class="filter-group"
    >
      <h4>{{ placeholder }} ({{ values.length }} variants)</h4>

      <!-- Checkboxes for each value -->
      <div class="filter-values">
        <label
          v-for="value in values"
          :key="value"
          class="filter-checkbox"
        >
          <input
            type="checkbox"
            :checked="isSelected(placeholder, value)"
            @change="toggleFilter(placeholder, value)"
          />
          {{ value }}
        </label>
      </div>
    </div>

    <!-- Filter actions -->
    <div class="filter-actions">
      <button @click="copyFilter">📋 Copy Filter</button>
      <input
        v-model="pasteInput"
        placeholder="Paste filter here"
        @change="applyPastedFilter"
      />
    </div>

    <!-- Result counter -->
    <div class="filter-stats">
      Showing: {{ filteredCount }} / {{ totalCount }} images
    </div>
  </div>
</template>
```

---

### Phase 4: Gallery Integration

**Modify `SessionGallery.vue`:**
```typescript
// Computed property for filtered images
const filteredImages = computed(() => {
  return applyFilters(allImages.value, filterState.value)
})

// Update navigation to use filtered subset
function nextImage() {
  const currentIndex = filteredImages.value.indexOf(currentImage)
  if (currentIndex < filteredImages.value.length - 1) {
    currentImage.value = filteredImages.value[currentIndex + 1]
  }
}
```

---

### Phase 5: Lazy Loading Fix

**Challenge:** Filtered images may not have thumbnails loaded yet

**Solution:**
```typescript
// When filter changes, check which images are now visible
watchEffect(() => {
  const visibleImages = getVisibleImages(filteredImages.value)

  visibleImages.forEach(img => {
    if (!img.thumbnailLoaded) {
      fetchThumbnail(img.filename)
    }
  })
})
```

---

## Performance Benchmarks

### Target Performance
- **Filter change** - < 100ms for 6000 images
- **Gallery render** - < 200ms for filtered subset
- **Thumbnail load** - < 500ms for newly visible images

### Profiling Points
1. Manifest parsing time
2. Filter application time
3. Gallery re-render time
4. Thumbnail fetch time

---

## Future Enhancements

### v2 Features
- **Text search** - Search in prompt text
- **Date filters** - Filter by generation date
- **Sorting** - By seed, filename, timestamp
- **Save filters** - Named filter presets
- **Batch actions** - Delete/export filtered images

### v3 Features
- **Advanced filters** - Numeric ranges (seed 1000-2000)
- **Regex support** - Pattern matching in values
- **Filter builder UI** - Visual query builder

---

## Testing Strategy

### Unit Tests
- `applyFilters()` logic
- URL encoding/decoding
- Filter state management

### Integration Tests
- Filter panel + gallery interaction
- Navigation in filtered mode
- Copy/paste filters

### Performance Tests
- Filter 6000 images (target < 100ms)
- Lazy load 50 thumbnails (target < 2s)
- Memory usage with large sessions

---

## Decisions Made

1. **Filtering approach: Option C (Hybrid) ✅**
   - Frontend filtering for instant response
   - Smart thumbnail batching for filtered results
   - Pre-fetch visible + next 20 in background
   - Migration path to backend if needed (v2)

2. **Filter panel placement: Right drawer ✅**
   - Slides from right side
   - Overlay with backdrop
   - Toggle button in top-right corner
   - Can be dismissed with ESC or backdrop click

3. **URL format: Standard URL query params ✅**
   - Format: `?HairColor=red,blue&Expression=smiling&Seed=1000,1001`
   - Benefits:
     - Browser-native (no custom encoding)
     - Copy URL = share filter
     - Bookmarkable
     - Compatible with standard routing libraries
   - Example: `/sessions/abc123?HairColor=red,blue&Expression=smiling`

4. **Empty state: Helpful message ✅**
   - "No images match your filters (0/6,000)"
   - Suggestion: "Try removing some filters or broadening your selection"
   - Button: "Clear all filters"

---

## Next Steps

1. ✅ Create design document (this file)
2. ✅ Decide: Hybrid frontend filtering
3. ✅ Decide: Right drawer placement
4. ✅ Decide: Standard URL query params
5. ⏸️ Create UI mockup (Figma or hand-drawn)
6. ⏸️ Implement FilterState management (Pinia store)
7. ⏸️ Implement FilterDrawer component
8. ⏸️ Implement filter logic + smart thumbnail batching
9. ⏸️ Integrate with SessionGallery
10. ⏸️ Test with large session (6000 images)
11. ⏸️ Optimize performance if needed
