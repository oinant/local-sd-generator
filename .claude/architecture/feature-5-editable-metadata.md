# Technical Architecture Document: Feature 5 - Editable Session Metadata

**Feature ID:** F5-EDITABLE-METADATA
**Status:** Architecture Complete
**Created:** 2025-11-07
**Owner:** Technical Architect Agent
**Dependencies:** Feature 4 (Session Details Panel)
**Estimated Effort:** 2-3h

---

## 1. Overview

### 1.1 Problem Statement
Users need to **edit session metadata** (tags, flags, notes) directly from the UI, with **auto-save** to persist changes immediately. Current detail panel shows metadata read-only.

### 1.2 Goals
1. **Inline tag editor** - Combobox with autocomplete, create new tags on-the-fly
2. **Flag toggles** - Clickable chips for liked/test/complete flags
3. **Notes editor** - Expandable text area for user notes
4. **Auto-save** - Debounced PATCH requests on every change
5. **Visual feedback** - Show saving/saved states, error handling

### 1.3 Non-Goals
- Bulk metadata editing (select multiple sessions) - phase 2
- Tag management UI (rename/delete tags globally) - phase 2
- Collaborative editing (conflict resolution) - phase 2

---

## 2. UI/UX Design

### 2.1 Editable Metadata Section

```
┌──────────────────────────────────────┐
│ 🏷️ Metadata                         │
│ ─────────────────────────────────    │
│                                      │
│ Tags:                                │
│ ┌────────────────────────────────┐  │
│ │ [character-design] [lora] [×]  │  │  ← Editable combobox
│ │ Type to add tags...            │  │
│ └────────────────────────────────┘  │
│                                      │
│ Flags:                               │
│ [⭐ Liked]  [🧪 Test]  [✅ Complete]│  ← Toggleable chips
│  (active)    (inactive)  (active)   │
│                                      │
│ Notes:                               │
│ ┌────────────────────────────────┐  │
│ │ Best facial expressions so far │  │  ← Expandable textarea
│ │                                │  │
│ └────────────────────────────────┘  │
│                                      │
│ Rating:                              │
│ [👍 Like]  [👎 Dislike]            │  ← Toggle buttons
│  (active)   (inactive)              │
│                                      │
│ 💾 Saved 2 seconds ago              │  ← Auto-save indicator
└──────────────────────────────────────┘
```

**Interaction States:**

1. **Idle:** Shows current values, no indicator
2. **Editing:** User typing in tag input or notes
3. **Saving:** Shows spinner icon "💾 Saving..."
4. **Saved:** Shows checkmark "✓ Saved"
5. **Error:** Shows error icon "⚠️ Failed to save"

---

### 2.2 Tag Editor Interaction

**Combobox Features:**
- **Autocomplete:** Suggests existing tags from all sessions as user types
- **Create new:** Press Enter to create new tag not in autocomplete list
- **Remove:** Click [×] on tag chip to remove
- **Multiple:** Can add unlimited tags
- **Validation:** Tags must be 1-50 chars, alphanumeric + hyphens/underscores only

**Example Flow:**
```
1. User clicks tag input → input focuses
2. User types "char" → autocomplete shows ["character-design", "character-art"]
3. User selects "character-design" → added as chip
4. User types "new-tag" → no match in autocomplete
5. User presses Enter → "new-tag" added as chip, saved immediately
6. API: PATCH /api/sessions/:name/metadata { tags: ["character-design", "new-tag"] }
7. UI shows "✓ Saved" for 2 seconds
```

---

### 2.3 Flag Toggles

**Click Behavior:**
- **Liked:** Click to toggle `is_favorite` (true/false)
- **Test:** Click to toggle `is_test` (true/false)
- **Complete:** Click to toggle `is_complete` (true/false)

**Visual States:**
- **Active:** Filled chip with icon (e.g., ⭐ Liked in yellow)
- **Inactive:** Outlined chip, gray (e.g., ⭐ Liked)
- **Saving:** Disabled with spinner

**API Call:** Debounced PATCH on every toggle (500ms debounce)

---

### 2.4 Notes Editor

**Features:**
- **Expandable:** Single-line by default, expands to 5 lines when focused
- **Character limit:** 500 characters (optional, can be removed)
- **Auto-save:** Debounced PATCH after 1 second of no typing
- **Placeholder:** "Add notes about this session..."

---

### 2.5 Rating Buttons

**Options:**
- 👍 Like (sets `user_rating: "like"`)
- 👎 Dislike (sets `user_rating: "dislike"`)
- Clear (sets `user_rating: null`)

**Behavior:** Radio button group, mutually exclusive

---

## 3. Component Implementation

### 3.1 Editable Metadata Component

**File:** `/packages/sd-generator-webui/front/src/components/EditableSessionMetadata.vue`

```vue
<template>
  <div class="editable-metadata">
    <!-- Section Header -->
    <div class="text-overline mb-2 d-flex align-center">
      <v-icon size="small" class="mr-1">mdi-tag-multiple</v-icon>
      Metadata
      <v-spacer></v-spacer>
      <!-- Save Indicator -->
      <v-chip
        v-if="saveState !== 'idle'"
        size="x-small"
        :color="saveStateColor"
        variant="flat"
      >
        <v-icon v-if="saveState === 'saving'" start size="x-small">mdi-loading mdi-spin</v-icon>
        <v-icon v-else-if="saveState === 'saved'" start size="x-small">mdi-check</v-icon>
        <v-icon v-else-if="saveState === 'error'" start size="x-small">mdi-alert</v-icon>
        {{ saveStateText }}
      </v-chip>
    </div>
    <v-divider class="mb-3"></v-divider>

    <!-- Tags Editor -->
    <div class="mb-3">
      <div class="text-caption text-medium-emphasis mb-1">Tags:</div>
      <v-combobox
        v-model="localMetadata.tags"
        :items="availableTags"
        chips
        closable-chips
        multiple
        variant="outlined"
        density="compact"
        placeholder="Type to add tags..."
        @update:model-value="debouncedSave"
      >
        <template #chip="{ item, props }">
          <v-chip
            v-bind="props"
            :text="item.raw"
            size="small"
            closable
          ></v-chip>
        </template>
      </v-combobox>
    </div>

    <!-- Flags -->
    <div class="mb-3">
      <div class="text-caption text-medium-emphasis mb-1">Flags:</div>
      <div class="d-flex flex-wrap gap-2">
        <v-chip
          :variant="localMetadata.is_favorite ? 'flat' : 'outlined'"
          :color="localMetadata.is_favorite ? 'yellow' : undefined"
          @click="toggleFlag('is_favorite')"
          :disabled="saveState === 'saving'"
        >
          <v-icon start size="small">mdi-star</v-icon>
          Liked
        </v-chip>

        <v-chip
          :variant="localMetadata.is_test ? 'flat' : 'outlined'"
          :color="localMetadata.is_test ? 'orange' : undefined"
          @click="toggleFlag('is_test')"
          :disabled="saveState === 'saving'"
        >
          <v-icon start size="small">mdi-flask</v-icon>
          Test
        </v-chip>

        <v-chip
          :variant="localMetadata.is_complete ? 'flat' : 'outlined'"
          :color="localMetadata.is_complete ? 'green' : undefined"
          @click="toggleFlag('is_complete')"
          :disabled="saveState === 'saving'"
        >
          <v-icon start size="small">mdi-check-circle</v-icon>
          Complete
        </v-chip>
      </div>
    </div>

    <!-- Notes -->
    <div class="mb-3">
      <div class="text-caption text-medium-emphasis mb-1">Notes:</div>
      <v-textarea
        v-model="localMetadata.user_note"
        variant="outlined"
        density="compact"
        placeholder="Add notes about this session..."
        rows="3"
        auto-grow
        max-rows="5"
        counter="500"
        maxlength="500"
        @update:model-value="debouncedSave"
      ></v-textarea>
    </div>

    <!-- Rating -->
    <div class="mb-3">
      <div class="text-caption text-medium-emphasis mb-1">Rating:</div>
      <v-btn-toggle
        v-model="localMetadata.user_rating"
        mandatory
        @update:model-value="debouncedSave"
        :disabled="saveState === 'saving'"
      >
        <v-btn value="like" size="small">
          <v-icon start>mdi-thumb-up</v-icon>
          Like
        </v-btn>
        <v-btn value="dislike" size="small">
          <v-icon start>mdi-thumb-down</v-icon>
          Dislike
        </v-btn>
        <v-btn value="null" size="small">
          Clear
        </v-btn>
      </v-btn-toggle>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useSessionsStore } from '@/stores/sessions'
import { useNotificationStore } from '@/stores/notification'
import { useDebounceFn } from '@vueuse/core'

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  },
  metadata: {
    type: Object,
    default: () => ({
      is_favorite: false,
      is_test: false,
      is_complete: true,
      user_rating: null,
      user_note: null,
      tags: []
    })
  }
})

const sessionsStore = useSessionsStore()
const notificationStore = useNotificationStore()

// State
const saveState = ref('idle')  // idle | saving | saved | error
const localMetadata = reactive({
  is_favorite: props.metadata.is_favorite ?? false,
  is_test: props.metadata.is_test ?? false,
  is_complete: props.metadata.is_complete ?? true,
  user_rating: props.metadata.user_rating ?? null,
  user_note: props.metadata.user_note ?? null,
  tags: props.metadata.tags ?? []
})

// Computed
const saveStateColor = computed(() => {
  if (saveState.value === 'saving') return 'primary'
  if (saveState.value === 'saved') return 'success'
  if (saveState.value === 'error') return 'error'
  return 'grey'
})

const saveStateText = computed(() => {
  if (saveState.value === 'saving') return 'Saving...'
  if (saveState.value === 'saved') return 'Saved'
  if (saveState.value === 'error') return 'Failed'
  return ''
})

const availableTags = computed(() => {
  // Get all unique tags from all sessions for autocomplete
  const allTags = new Set()
  sessionsStore.sessions.forEach(session => {
    session.metadata?.tags?.forEach(tag => allTags.add(tag))
  })
  return Array.from(allTags).sort()
})

// Watch props.metadata for external changes
watch(() => props.metadata, (newMetadata) => {
  Object.assign(localMetadata, newMetadata)
}, { deep: true })

// Methods
const saveMetadata = async () => {
  saveState.value = 'saving'

  try {
    // Convert "null" string to actual null for user_rating
    const updateData = {
      ...localMetadata,
      user_rating: localMetadata.user_rating === 'null' ? null : localMetadata.user_rating
    }

    await sessionsStore.updateSessionMetadata(props.sessionId, updateData)

    saveState.value = 'saved'

    // Reset to idle after 2 seconds
    setTimeout(() => {
      saveState.value = 'idle'
    }, 2000)

  } catch (error) {
    saveState.value = 'error'
    notificationStore.show({
      message: 'Failed to save metadata',
      color: 'error'
    })

    // Reset to idle after 3 seconds
    setTimeout(() => {
      saveState.value = 'idle'
    }, 3000)
  }
}

const debouncedSave = useDebounceFn(() => {
  saveMetadata()
}, 1000)  // 1 second debounce

const toggleFlag = (flagName) => {
  localMetadata[flagName] = !localMetadata[flagName]
  // Immediate save for flags (with 500ms debounce)
  useDebounceFn(saveMetadata, 500)()
}
</script>

<style scoped>
.editable-metadata {
  /* Add any custom styles */
}
</style>
```

---

### 3.2 Integration into Detail Components

**Modify:** `/packages/sd-generator-webui/front/src/components/SessionDetailDrawer.vue`

```vue
<!-- Replace read-only metadata section with: -->
<div v-if="session" class="mb-4">
  <EditableSessionMetadata
    :session-id="session.session_id"
    :metadata="session.metadata"
  />
</div>
```

**Import:**
```javascript
import EditableSessionMetadata from '@/components/EditableSessionMetadata.vue'
```

---

## 4. Store Updates

**File:** `/packages/sd-generator-webui/front/src/stores/sessions.js` (already implemented in Feature 3)

```javascript
// Method already exists from Feature 3:
async updateSessionMetadata(sessionId, update) {
  try {
    const metadata = await ApiService.updateSessionMetadata(sessionId, update)

    // Update in store
    const session = this.sessions.find(s => s.session_id === sessionId)
    if (session) {
      session.metadata = metadata
    }

    return metadata
  } catch (error) {
    console.error(`Failed to update metadata for ${sessionId}:`, error)
    throw error
  }
}
```

---

## 5. Debouncing Strategy

### 5.1 Why Debounce?

**Problem:** Every keystroke triggers API call → 100 requests for "character-design" (15 chars)

**Solution:** Wait for user to stop typing before saving

### 5.2 Debounce Times

| Field | Debounce Time | Reason |
|-------|--------------|--------|
| Tags | 1000ms (1s) | User may type multiple tags quickly |
| Notes | 1000ms (1s) | User may type sentences |
| Flags | 500ms (0.5s) | Immediate feedback expected |
| Rating | 500ms (0.5s) | Immediate feedback expected |

### 5.3 Implementation

Using `@vueuse/core` for debouncing:

```javascript
import { useDebounceFn } from '@vueuse/core'

const debouncedSave = useDebounceFn(() => {
  saveMetadata()
}, 1000)
```

**Behavior:**
1. User types in notes → debounce timer starts
2. User continues typing → timer resets on each keystroke
3. User stops typing for 1 second → `saveMetadata()` called
4. API: PATCH /api/sessions/:name/metadata

---

## 6. Error Handling

### 6.1 Network Errors

**Scenario:** API call fails (network error, 500 error, etc.)

**Handling:**
1. Set `saveState = 'error'`
2. Show red chip "⚠️ Failed"
3. Show toast notification: "Failed to save metadata"
4. Keep local changes in UI (user can try again)
5. Add "Retry" button in error chip (optional)

### 6.2 Validation Errors

**Scenario:** Backend rejects tag (e.g., too long, invalid chars)

**Handling:**
1. API returns 400 with validation error message
2. Show toast: "Invalid tag: must be 1-50 chars, alphanumeric only"
3. Revert local change (remove invalid tag from UI)

### 6.3 Concurrent Edits

**Scenario:** User edits in two tabs simultaneously

**Current:** Last write wins (no conflict resolution)

**Phase 2:** Add optimistic locking with `updated_at` timestamp comparison

---

## 7. Testing Strategy

### 7.1 Component Tests

```javascript
describe('EditableSessionMetadata', () => {
  it('allows adding and removing tags', async () => {
    const wrapper = mount(EditableSessionMetadata, {
      props: {
        sessionId: 'test',
        metadata: { tags: ['existing'] }
      }
    })

    // Add tag
    await wrapper.find('input').setValue('new-tag')
    await wrapper.find('input').trigger('keydown.enter')
    expect(wrapper.vm.localMetadata.tags).toContain('new-tag')

    // Remove tag
    await wrapper.find('.v-chip__close').trigger('click')
    expect(wrapper.vm.localMetadata.tags).not.toContain('new-tag')
  })

  it('toggles flags correctly', async () => {
    const wrapper = mount(EditableSessionMetadata, {
      props: {
        sessionId: 'test',
        metadata: { is_favorite: false }
      }
    })

    // Toggle liked flag
    await wrapper.findAll('.v-chip')[0].trigger('click')
    expect(wrapper.vm.localMetadata.is_favorite).toBe(true)
  })

  it('debounces save calls', async () => {
    const saveSpy = vi.spyOn(ApiService, 'updateSessionMetadata')

    const wrapper = mount(EditableSessionMetadata, {
      props: { sessionId: 'test', metadata: {} }
    })

    // Type in notes
    await wrapper.find('textarea').setValue('Test note 1')
    await wrapper.find('textarea').setValue('Test note 2')
    await wrapper.find('textarea').setValue('Test note 3')

    // Should only call once after debounce
    await new Promise(resolve => setTimeout(resolve, 1100))
    expect(saveSpy).toHaveBeenCalledTimes(1)
  })

  it('shows save state indicator', async () => {
    const wrapper = mount(EditableSessionMetadata, {
      props: { sessionId: 'test', metadata: {} }
    })

    // Trigger save
    await wrapper.find('textarea').setValue('Note')

    // Should show "Saving..."
    expect(wrapper.text()).toContain('Saving...')

    // Wait for save to complete
    await new Promise(resolve => setTimeout(resolve, 1100))

    // Should show "Saved"
    expect(wrapper.text()).toContain('Saved')
  })
})
```

---

## 8. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Rapid edits** cause API rate limiting | Low | Low | Use debouncing. Add client-side queue to batch updates (phase 2). |
| **Large tag lists** (50+ tags) overflow UI | Low | Low | Add scrollable tag container with max-height. Show only first 10, "+ N more" expansion. |
| **Concurrent edits** cause data loss | Low | Medium | Add optimistic locking (check `updated_at` timestamp). Show conflict resolution UI (phase 2). |
| **Network errors** lose user edits | Low | Medium | Keep local changes in UI. Add "Retry" button. Store unsaved changes in localStorage (phase 2). |

---

## 9. Accessibility

1. **Keyboard Navigation:**
   - Tab through tag input, flag chips, notes, rating buttons
   - Enter to add tag, Space to toggle flags
   - Escape to cancel tag input

2. **Screen Reader:**
   - Announce save state changes ("Saving metadata", "Metadata saved")
   - Label all form fields ("Tags", "Flags", "Notes", "Rating")
   - Announce flag toggles ("Liked flag enabled")

3. **Focus Management:**
   - Keep focus on input after adding tag
   - Return focus to toggle after flag change

---

## 10. Strategic Alignment

### 10.1 Enables Future Features

**Feature #70 (Variation Rating):**
- Tag sessions with "rated" after variation rating
- Filter sessions by "rated" tag

**Feature #61 (Image Tagging):**
- Session tags inherit to images (optional)
- Batch tag images in session based on session tags

**Analytics:**
- Aggregate sessions by tags
- Track most-used tags
- Analyze liked vs disliked session patterns

---

## 11. Success Criteria

1. **Auto-save:** Changes persist within 2 seconds of user stopping typing
2. **Performance:** Debounced saves prevent >1 API call per second
3. **UX:** Save state indicator always visible, clear success/error feedback
4. **Reliability:** 0 data loss on network errors (keep local changes)
5. **Accessibility:** Full keyboard navigation works

---

## 12. Implementation Checklist

- [ ] Create `EditableSessionMetadata.vue` component
- [ ] Implement tag combobox with autocomplete
- [ ] Implement flag toggle chips
- [ ] Implement notes textarea with auto-expand
- [ ] Implement rating toggle buttons
- [ ] Add debounced save (1s for tags/notes, 500ms for flags)
- [ ] Add save state indicator (saving/saved/error)
- [ ] Integrate into `SessionDetailDrawer.vue`
- [ ] Add error handling (network errors, validation)
- [ ] Write component unit tests (5 test cases)
- [ ] Test keyboard navigation
- [ ] Test screen reader announcements
- [ ] Test on mobile (touch interaction)

---

## 13. Files to Create/Modify

### New Files
- `/packages/sd-generator-webui/front/src/components/EditableSessionMetadata.vue` (300 lines)
- `/packages/sd-generator-webui/front/tests/unit/components/EditableSessionMetadata.spec.js` (150 lines)

### Modified Files
- `/packages/sd-generator-webui/front/src/components/SessionDetailDrawer.vue` (replace read-only metadata section)
- `/packages/sd-generator-webui/front/src/views/SessionDetail.vue` (same replacement)

---

## 14. Performance Optimizations

### 14.1 Autocomplete Tag Loading

**Problem:** Loading 10,000 unique tags for autocomplete is slow

**Solution:**
- Load top 100 most-used tags for autocomplete
- Add search endpoint: `GET /api/tags?q=char` (phase 2)
- Cache autocomplete results in Pinia store

### 14.2 Debounce Queue

**Current:** Each field debounces independently → 3 API calls if user edits tags + notes + flags

**Phase 2 Optimization:** Single debounced save that batches all pending changes

```javascript
// Collect all pending changes
const pendingChanges = {
  tags: localMetadata.tags,
  is_favorite: localMetadata.is_favorite,
  user_note: localMetadata.user_note
}

// Single PATCH with all fields
await ApiService.updateSessionMetadata(sessionId, pendingChanges)
```

---

## 15. Future Enhancements (Phase 2)

1. **Tag Management UI:**
   - Rename tags globally
   - Merge duplicate tags
   - Delete unused tags
   - View tag usage statistics

2. **Bulk Operations:**
   - Select multiple sessions
   - Apply tags to all selected
   - Bulk flag toggles

3. **Tag Suggestions:**
   - AI-powered tag suggestions based on session content
   - "Sessions like this are tagged with: [X, Y, Z]"

4. **Change History:**
   - Show metadata edit history
   - Undo/redo metadata changes
   - Audit log for collaborative workflows

---

## 16. Next Steps

After this feature:
1. **Session List** shows editable metadata in cards (inline editing)
2. **Variation Rating** (#70) can use tags to organize rated sessions
3. **Analytics** can aggregate by tags, flags, ratings
