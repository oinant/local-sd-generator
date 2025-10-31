# UX Analysis: Session Date Display & Sorting

**Date:** 2025-11-01
**Status:** In Progress
**Component:** WebUI - Session List

## Problem Statement

User confusion about session date display and sorting:
> "impossible de retrouver les sessions par veritables dates, dans ce cas, et impossible de les trier"

### Root Causes

1. **Date removed from display name** - Shows "hassaku_actualportrait" instead of full folder name
2. **No visual date grouping** - 460 sessions in flat list, hard to navigate
3. **No sort controls** - Implicit sorting, no UI indication of how it works
4. **Filesystem metadata misleading** - Modification dates from manifest migration don't match generation dates
5. **No date search/filter** - Can't jump to specific time periods

## Current Implementation

**Backend (Working Correctly):**
```python
def parse_session_datetime(session_name: str) -> Optional[datetime]:
    """Parse datetime from session folder name."""
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})(\d{2})', session_name)
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        return datetime(year, month, day, hour, minute, second)
    return None

sessions.sort(key=lambda x: x.created_at, reverse=True)
```

**Frontend (Causes Confusion):**
```javascript
formatSessionName(sessionName) {
  // Format: 2025-10-14_163854_hassaku_actualportrait.prompt
  const parts = sessionName.split('_')
  if (parts.length >= 3) {
    return parts.slice(2).join('_').replace('.prompt', '')  // Returns "hassaku_actualportrait"
  }
  return sessionName
}
```

## Recommended Solutions

### Priority 1: Quick Wins (1-2h implementation)

#### 1. Show Date in Session Name
**Impact:** High
**Effort:** Low
**Location:** `SessionCard.vue:164-172`

```vue
computed: {
  displayName() {
    const parts = this.session.name.split('_')
    if (parts.length >= 3) {
      // Include date prefix for easier scanning
      return `${parts[0]} ${parts[1]} · ${parts.slice(2).join('_').replace('.prompt', '')}`
    }
    return this.session.name
  }
}

// Display: "2025-10-14 163854 · hassaku_actualportrait"
// Or more readable: "2025-10-14 · hassaku_actualportrait"
```

#### 2. Add Tooltip with Full Folder Name
**Impact:** Medium
**Effort:** Trivial
**Location:** `SessionCard.vue:2-6`

```vue
<v-list-item
  :active="isSelected"
  @click="$emit('select', session.name)"
  class="session-card"
  :title="session.name"  <!-- Shows full folder name on hover -->
>
```

#### 3. Add Sort Indicator + Controls
**Impact:** High
**Effort:** Medium
**Location:** `Images.vue:7-20`

```vue
<v-card-title class="pb-2 d-flex justify-space-between align-center">
  <span>
    <v-icon class="mr-2">mdi-folder-multiple</v-icon>
    Sessions
    <v-chip size="x-small" variant="text" class="ml-2">
      <v-icon size="x-small">mdi-sort-clock-descending</v-icon>
      Par date ↓
    </v-chip>
  </span>
  <div class="d-flex gap-1">
    <v-btn icon size="small" variant="text" @click="toggleSortOrder">
      <v-icon>{{ sortDescending ? 'mdi-sort-descending' : 'mdi-sort-ascending' }}</v-icon>
    </v-btn>
    <v-btn icon size="small" variant="text" @click="filtersDrawer = !filtersDrawer">
      <v-icon>mdi-filter-variant</v-icon>
    </v-btn>
  </div>
</v-card-title>
```

### Priority 2: Medium Effort (3-4h)

#### 4. Add Date Range Filter to SessionFilters
**Impact:** High
**Effort:** Medium

```vue
<v-card-title>Date Range</v-card-title>
<v-chip-group v-model="localFilters.dateRange" mandatory>
  <v-chip value="all">Toutes</v-chip>
  <v-chip value="today">Aujourd'hui</v-chip>
  <v-chip value="week">7 derniers jours</v-chip>
  <v-chip value="month">30 derniers jours</v-chip>
  <v-chip value="custom">Personnalisé</v-chip>
</v-chip-group>
```

#### 5. Implement Date Filtering Logic
**Location:** `Images.vue - filteredSessions computed`

```javascript
// Filter by date range
if (this.filters.dateRange !== 'all') {
  const now = new Date()
  let startDate = null

  switch (this.filters.dateRange) {
    case 'today':
      startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      break
    case 'week':
      startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      break
    case 'month':
      startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      break
    case 'custom':
      // Custom date range logic
      break
  }

  if (startDate) {
    filtered = filtered.filter(session => session.date >= startDate)
  }
}
```

### Priority 3: Higher Effort (1-2 days)

#### 6. Add Visual Date Grouping (Group by Month/Week)
**Impact:** Very High
**Effort:** High

Group sessions visually by month with collapsible headers:

```
▼ Octobre 2025 (127)
  📁 2025-10-29 · emma_fullbody_variation   32
  📁 2025-10-14 · hassaku_actualportrait    50

▼ Septembre 2025 (89)
  📁 2025-09-28 · ...
```

#### 7. Add "Jump to Date" Quick Action
**Impact:** Medium
**Effort:** Medium

Date picker dialog to quickly navigate to specific dates.

## Mockup Comparison

### BEFORE (Current)
```
Sessions                                [Filter Icon]
─────────────────────────────────────────
📁 hassaku_actualportrait               50
   14 oct. 2025 16:38

📁 emma_fullbody_variation              32
   29 oct. 2025 15:50
```

### AFTER (Priority 1)
```
Sessions    [Sort ↓] [Filter]    📅 Par date (plus récent)
─────────────────────────────────────────
📁 2025-10-29 · emma_fullbody_variation     32
   💬 Hover tooltip: "2025-10-29_155046_emma_fullbody_variation.prompt"

📁 2025-10-14 · hassaku_actualportrait      50
```

### AFTER (Priority 3 - Full)
```
Sessions    [Sort ↓] [Filter] [📅 Aller à une date]
─────────────────────────────────────────
▼ Octobre 2025 (127)
  📁 2025-10-29 · emma_fullbody_variation   32
  📁 2025-10-14 · hassaku_actualportrait    50

▼ Septembre 2025 (89)
  📁 2025-09-28 · ...
```

## Implementation Timeline

**Phase 1 (Priority 1 - Now):**
- [x] Save UX analysis to documentation
- [ ] Add tooltip with full folder name
- [ ] Update displayName to include date prefix
- [ ] Add sort direction indicator
- [ ] Add sort toggle functionality
- [ ] Test in browser

**Phase 2 (Priority 2 - Next sprint):**
- [ ] Add date range filter component
- [ ] Implement date filtering logic
- [ ] Add quick date presets

**Phase 3 (Priority 3 - Future):**
- [ ] Implement date grouping
- [ ] Add virtual scrolling for performance
- [ ] Add "Jump to date" quick action

## Technical Notes

### Session Date Source
**CRITICAL:** Session dates come from folder names, NOT filesystem metadata.

- **Format:** `YYYY-MM-DD_HHMMSS_name.prompt`
- **Example:** `2025-10-14_163854_hassaku_actualportrait.prompt`
- **Parsed to:** `datetime(2025, 10, 14, 16, 38, 54)`

Filesystem modification dates may differ (e.g., from manifest migrations) and should be ignored for display purposes.

### Sorting Behavior
- Sessions are sorted by generation date (parsed from folder name)
- Default: Newest first (`reverse=True`)
- Sorting is stable across backend restarts (embedded in folder names)

## Related Issues
- Performance fix: Disabled file tree cache warming (58s → <1s load time)
- Phase 1 session rating system: Successfully implemented with SQLite backend

## References
- `packages/sd-generator-webui/backend/sd_generator_webui/api/sessions.py:25-39` - Date parsing
- `packages/sd-generator-webui/front/src/components/SessionCard.vue:164-172` - Display name formatting
- `packages/sd-generator-webui/front/src/views/Images.vue:614-623` - Session name formatting
