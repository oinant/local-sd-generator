# Technical Architecture Document: Feature 4 - Session Details Panel

**Feature ID:** F4-SESSION-DETAILS-PANEL
**Status:** Architecture Complete
**Created:** 2025-11-07
**Owner:** Technical Architect Agent
**Dependencies:** Feature 3 (Session List UI)
**Estimated Effort:** 2h

---

## 1. Overview

### 1.1 Problem Statement
When user clicks a session card, they need to see **detailed stats and metadata** in a clean, scannable format. Must work as both **desktop drawer** (master-detail) and **mobile full-page** (navigation).

### 1.2 Goals
1. **Comprehensive stats display** - All fields from `SessionStats` model
2. **Responsive layout** - Drawer on desktop (≥960px), full page on mobile
3. **Color-coded completion** - Visual indicators for completion status
4. **Placeholder expansion** - Show all placeholders and first N variations
5. **Metadata display** - Tags, flags, notes (read-only for now, Feature 5 adds editing)

### 1.3 Non-Goals
- Metadata editing (Feature 5)
- Image gallery within detail panel (use `/sessions/:name/images` route)
- Stats comparison between sessions (phase 2)

---

## 2. UI/UX Design

### 2.1 Desktop Drawer Layout

```
┌──────────────────────────────────────┐
│ [X] facial_expressions               │  ← Header with close button
├──────────────────────────────────────┤
│                                      │
│ 📊 Generation Stats                  │  ← Section: Generation
│ ───────────────────────────────────  │
│ Model:     illustriousXL_v01         │
│ Version:   Template 2.0              │
│ Mode:      Combinatorial             │
│ Seed:      Fixed (42)                │
│                                      │
│ 📸 Images                            │  ← Section: Images
│ ───────────────────────────────────  │
│ Expected:  50                        │
│ Actual:    50                        │
│ Complete:  ✅ 100%                   │
│ Created:   2025-11-07 12:00          │
│ Duration:  20 minutes                │
│                                      │
│ 🎲 API Parameters                    │  ← Section: API Params
│ ───────────────────────────────────  │
│ Size:      512×768                   │
│ Steps:     30                        │
│ CFG:       7.0                       │
│ Sampler:   DPM++ 2M Karras           │
│                                      │
│ 🧩 Placeholders (1)                  │  ← Section: Placeholders
│ ───────────────────────────────────  │
│ FacialExpression: 50 variations      │
│   [smile] [sad] [angry] [surprised]  │  ← First 10 variations as chips
│   [happy] [fear] [disgust] ...       │
│   + 40 more                          │
│                                      │
│ 🏷️ Metadata                         │  ← Section: Metadata
│ ───────────────────────────────────  │
│ Tags: [character-design] [lora]      │
│ Flags: ⭐ Liked  🧪 Test             │
│ Notes: Best expressions so far       │
│                                      │
│ [View Images →]                      │  ← Action button
└──────────────────────────────────────┘
```

### 2.2 Mobile Full-Page Layout

```
┌─────────────────────┐
│ [← Back] Session    │
│ facial_expressions  │
├─────────────────────┤
│ 📊 Generation Stats │
│ Model: illustrious  │
│ Mode:  Combinatorial│
│ Seed:  Fixed (42)   │
│                     │
│ 📸 Images           │
│ 50 / 50 (100% ✅)  │
│                     │
│ 🎲 API Parameters   │
│ 512×768 | 30 steps  │
│ CFG 7.0 | DPM++     │
│                     │
│ 🧩 Placeholders     │
│ FacialExpression:50 │
│ [smile] [sad] ...   │
│                     │
│ 🏷️ Metadata        │
│ [tags] [flags]      │
│                     │
│ [View Images →]     │
└─────────────────────┘
```

---

## 3. Component Implementation

### 3.1 Desktop Drawer Component

**File:** `/packages/sd-generator-webui/front/src/components/SessionDetailDrawer.vue`

```vue
<template>
  <v-navigation-drawer
    :model-value="true"
    location="right"
    permanent
    width="400"
    class="session-detail-drawer"
  >
    <!-- Header -->
    <template #prepend>
      <v-toolbar color="primary" density="compact">
        <v-toolbar-title class="text-truncate">
          {{ formatSessionName(session.session_id) }}
        </v-toolbar-title>
        <v-btn icon="mdi-close" @click="$emit('close')"></v-btn>
      </v-toolbar>
    </template>

    <!-- Loading State -->
    <v-progress-linear
      v-if="loading"
      indeterminate
      color="primary"
    ></v-progress-linear>

    <!-- Content -->
    <v-card v-if="session && stats" flat>
      <v-card-text>
        <!-- Generation Stats Section -->
        <div class="mb-4">
          <div class="text-overline mb-2">
            <v-icon size="small" class="mr-1">mdi-chart-box</v-icon>
            Generation Stats
          </div>
          <v-divider class="mb-2"></v-divider>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">Model:</span>
            <span class="text-caption">{{ stats.sd_model || 'Unknown' }}</span>
          </div>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">Version:</span>
            <span class="text-caption">Template {{ stats.template_version || 'Unknown' }}</span>
          </div>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">Mode:</span>
            <v-chip size="x-small" :color="modeColor">
              {{ stats.generation_mode || 'Unknown' }}
            </v-chip>
          </div>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">Seed:</span>
            <span class="text-caption">
              {{ formatSeedMode(stats.seed_mode, stats.seed_base) }}
            </span>
          </div>

          <!-- Seed Sweep Badge -->
          <v-chip
            v-if="stats.is_seed_sweep"
            size="small"
            color="green"
            class="mt-2"
          >
            <v-icon start size="small">mdi-seed</v-icon>
            Seed Sweep Session
          </v-chip>
        </div>

        <!-- Images Section -->
        <div class="mb-4">
          <div class="text-overline mb-2">
            <v-icon size="small" class="mr-1">mdi-image-multiple</v-icon>
            Images
          </div>
          <v-divider class="mb-2"></v-divider>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">Expected:</span>
            <span class="text-caption">{{ stats.images_expected }}</span>
          </div>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">Actual:</span>
            <span class="text-caption">{{ stats.images_actual }}</span>
          </div>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">Completion:</span>
            <v-chip
              size="x-small"
              :color="completionColor"
            >
              {{ stats.completion_percentage?.toFixed(0) }}%
            </v-chip>
          </div>

          <div v-if="stats.session_created_at" class="detail-row">
            <span class="text-caption text-medium-emphasis">Created:</span>
            <span class="text-caption">{{ formatDateTime(stats.session_created_at) }}</span>
          </div>

          <div v-if="duration" class="detail-row">
            <span class="text-caption text-medium-emphasis">Duration:</span>
            <span class="text-caption">{{ duration }}</span>
          </div>
        </div>

        <!-- API Parameters Section -->
        <div class="mb-4">
          <div class="text-overline mb-2">
            <v-icon size="small" class="mr-1">mdi-cog</v-icon>
            API Parameters
          </div>
          <v-divider class="mb-2"></v-divider>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">Size:</span>
            <span class="text-caption">{{ stats.width }}×{{ stats.height }}</span>
          </div>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">Steps:</span>
            <span class="text-caption">{{ stats.steps }}</span>
          </div>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">CFG Scale:</span>
            <span class="text-caption">{{ stats.cfg_scale }}</span>
          </div>

          <div class="detail-row">
            <span class="text-caption text-medium-emphasis">Sampler:</span>
            <span class="text-caption">{{ stats.sampler_name }}</span>
          </div>
        </div>

        <!-- Placeholders Section -->
        <div v-if="hasPlaceholders" class="mb-4">
          <div class="text-overline mb-2">
            <v-icon size="small" class="mr-1">mdi-puzzle</v-icon>
            Placeholders ({{ placeholderCount }})
          </div>
          <v-divider class="mb-2"></v-divider>

          <div
            v-for="(count, placeholder) in stats.placeholders"
            :key="placeholder"
            class="mb-3"
          >
            <div class="text-caption font-weight-bold mb-1">
              {{ placeholder }}: {{ count }} variation{{ count > 1 ? 's' : '' }}
            </div>

            <!-- Variation chips (first 10) -->
            <div class="d-flex flex-wrap gap-1">
              <v-chip
                v-for="variation in getVariationsForPlaceholder(placeholder)"
                :key="variation"
                size="x-small"
                variant="outlined"
              >
                {{ variation }}
              </v-chip>

              <!-- More indicator -->
              <v-chip
                v-if="getRemainingCount(placeholder) > 0"
                size="x-small"
                variant="text"
              >
                +{{ getRemainingCount(placeholder) }} more
              </v-chip>
            </div>
          </div>
        </div>

        <!-- Metadata Section -->
        <div v-if="session.metadata" class="mb-4">
          <div class="text-overline mb-2">
            <v-icon size="small" class="mr-1">mdi-tag-multiple</v-icon>
            Metadata
          </div>
          <v-divider class="mb-2"></v-divider>

          <!-- Tags -->
          <div v-if="session.metadata.tags?.length > 0" class="mb-2">
            <div class="text-caption text-medium-emphasis mb-1">Tags:</div>
            <v-chip
              v-for="tag in session.metadata.tags"
              :key="tag"
              size="small"
              class="mr-1 mb-1"
            >
              {{ tag }}
            </v-chip>
          </div>

          <!-- Flags -->
          <div class="mb-2">
            <div class="text-caption text-medium-emphasis mb-1">Flags:</div>
            <v-chip
              v-if="session.metadata.is_favorite"
              size="small"
              color="yellow"
              class="mr-1"
            >
              <v-icon start size="small">mdi-star</v-icon>
              Liked
            </v-chip>
            <v-chip
              v-if="session.metadata.is_test"
              size="small"
              color="orange"
              class="mr-1"
            >
              <v-icon start size="small">mdi-flask</v-icon>
              Test
            </v-chip>
            <v-chip
              v-if="!session.metadata.is_complete"
              size="small"
              color="red"
              class="mr-1"
            >
              <v-icon start size="small">mdi-alert</v-icon>
              Incomplete
            </v-chip>
          </div>

          <!-- User Note -->
          <div v-if="session.metadata.user_note" class="mb-2">
            <div class="text-caption text-medium-emphasis mb-1">Notes:</div>
            <div class="text-caption">{{ session.metadata.user_note }}</div>
          </div>

          <!-- Rating -->
          <div v-if="session.metadata.user_rating" class="mb-2">
            <div class="text-caption text-medium-emphasis mb-1">Rating:</div>
            <v-chip
              size="small"
              :color="session.metadata.user_rating === 'like' ? 'green' : 'red'"
            >
              <v-icon start size="small">
                {{ session.metadata.user_rating === 'like' ? 'mdi-thumb-up' : 'mdi-thumb-down' }}
              </v-icon>
              {{ session.metadata.user_rating }}
            </v-chip>
          </div>
        </div>
      </v-card-text>

      <!-- Actions -->
      <v-card-actions>
        <v-btn
          color="primary"
          variant="outlined"
          block
          :to="`/sessions/${session.session_id}/images`"
        >
          View Images
          <v-icon end>mdi-arrow-right</v-icon>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-navigation-drawer>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useSessionsStore } from '@/stores/sessions'
import ApiService from '@/services/api'

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  }
})

defineEmits(['close'])

const sessionsStore = useSessionsStore()
const loading = ref(false)
const stats = ref(null)

// Get session from store
const session = computed(() => {
  return sessionsStore.sessions.find(s => s.session_id === props.sessionId)
})

// Computed properties
const completionColor = computed(() => {
  const pct = stats.value?.completion_percentage || 0
  if (pct >= 95) return 'success'
  if (pct >= 75) return 'warning'
  return 'error'
})

const modeColor = computed(() => {
  const mode = stats.value?.generation_mode
  return mode === 'combinatorial' ? 'primary' : 'secondary'
})

const hasPlaceholders = computed(() => {
  return stats.value?.placeholders && Object.keys(stats.value.placeholders).length > 0
})

const placeholderCount = computed(() => {
  return hasPlaceholders.value ? Object.keys(stats.value.placeholders).length : 0
})

const duration = computed(() => {
  if (!stats.value?.first_image_created_at || !stats.value?.last_image_created_at) {
    return null
  }

  const start = new Date(stats.value.first_image_created_at)
  const end = new Date(stats.value.last_image_created_at)
  const diffMs = end - start
  const diffMins = Math.round(diffMs / 60000)

  if (diffMins < 1) return '< 1 minute'
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''}`
  const hours = Math.floor(diffMins / 60)
  const mins = diffMins % 60
  return `${hours}h ${mins}m`
})

// Methods
const formatSessionName = (sessionId) => {
  const match = sessionId.match(/^\d{8}_\d{6}-(.+)$/)
  return match ? match[1] : sessionId
}

const formatSeedMode = (mode, base) => {
  if (!mode) return 'Unknown'
  if (mode === 'fixed') return `Fixed (${base})`
  if (mode === 'progressive') return `Progressive (${base}+)`
  return 'Random'
}

const formatDateTime = (isoDate) => {
  const date = new Date(isoDate)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getVariationsForPlaceholder = (placeholder) => {
  const summary = stats.value?.variations_summary || {}
  return (summary[placeholder] || []).slice(0, 10)
}

const getRemainingCount = (placeholder) => {
  const total = stats.value?.placeholders[placeholder] || 0
  const shown = getVariationsForPlaceholder(placeholder).length
  return Math.max(0, total - shown)
}

const loadStats = async () => {
  if (!props.sessionId) return

  loading.value = true
  try {
    const response = await ApiService.getSessionStats(props.sessionId)
    stats.value = response
  } catch (error) {
    console.error('Failed to load session stats:', error)
  } finally {
    loading.value = false
  }
}

// Watch sessionId changes
watch(() => props.sessionId, () => {
  loadStats()
}, { immediate: true })

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.session-detail-drawer {
  border-left: 1px solid rgba(0, 0, 0, 0.12);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.detail-row span:first-child {
  flex: 0 0 auto;
  margin-right: 16px;
}

.detail-row span:last-child {
  flex: 1 1 auto;
  text-align: right;
}
</style>
```

---

### 3.2 Mobile Full-Page Component

**File:** `/packages/sd-generator-webui/front/src/views/SessionDetail.vue`

```vue
<template>
  <v-container fluid class="pa-4">
    <!-- Header with back button -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-btn
            icon="mdi-arrow-left"
            variant="text"
            @click="$router.back()"
          ></v-btn>
          <h1 class="text-h5 ml-2">{{ formatSessionName(sessionId) }}</h1>
        </div>
      </v-col>
    </v-row>

    <!-- Use same content as drawer, but in full-page layout -->
    <v-row>
      <v-col cols="12">
        <!-- Reuse drawer component's content structure -->
        <!-- (Copy from SessionDetailDrawer.vue, adjust styling for full-page) -->
        <SessionDetailContent :session-id="sessionId" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import SessionDetailContent from '@/components/SessionDetailContent.vue'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.name

const formatSessionName = (sessionId) => {
  const match = sessionId.match(/^\d{8}_\d{6}-(.+)$/)
  return match ? match[1] : sessionId
}
</script>
```

**Note:** Extract drawer content into shared `SessionDetailContent.vue` component to avoid duplication.

---

## 4. Testing Strategy

### 4.1 Component Tests

```javascript
describe('SessionDetailDrawer', () => {
  it('displays all session stats', () => {
    const wrapper = mount(SessionDetailDrawer, {
      props: {
        sessionId: '20251107_120000-test'
      }
    })

    expect(wrapper.text()).toContain('Model')
    expect(wrapper.text()).toContain('Images')
    expect(wrapper.text()).toContain('API Parameters')
  })

  it('shows completion badge with correct color', () => {
    // Test green for 100%, orange for 85%, red for 50%
  })

  it('expands placeholders with variations', () => {
    // Test placeholder chips render correctly
  })
})
```

---

## 5. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Large variation lists** (100+ variations) overflow UI | Low | Low | Show first 10, collapse rest with "+N more" chip. Add "Show all" expansion (phase 2). |
| **Missing stats** break rendering | Low | Medium | Graceful fallback: show "Stats not available" message. Link to refresh stats. |
| **Drawer width** too narrow for long model names | Medium | Low | Use text truncation with tooltip on hover. |

---

## 6. Success Criteria

1. **Completeness:** Display all 20+ stats fields from `SessionStats`
2. **Responsiveness:** Drawer works on desktop, full-page on mobile
3. **Performance:** Renders stats in <100ms after API response
4. **Visual clarity:** Color-coded badges make completion status obvious at a glance
5. **Accessibility:** Screen reader announces all stats correctly

---

## 7. Implementation Checklist

- [ ] Create `SessionDetailDrawer.vue` component
- [ ] Create `SessionDetail.vue` mobile view
- [ ] Extract shared logic into `SessionDetailContent.vue`
- [ ] Add completion color coding (green/yellow/red)
- [ ] Implement placeholder expansion (first 10 + more)
- [ ] Add "View Images" action button
- [ ] Test on desktop drawer layout
- [ ] Test on mobile full-page layout
- [ ] Write component unit tests
- [ ] Add loading/error states

---

## 8. Files to Create/Modify

### New Files
- `/packages/sd-generator-webui/front/src/components/SessionDetailDrawer.vue` (300 lines)
- `/packages/sd-generator-webui/front/src/components/SessionDetailContent.vue` (200 lines, shared)

### Modified Files
- `/packages/sd-generator-webui/front/src/views/SessionDetail.vue` (replace placeholder, +100 lines)

---

## 9. Next Steps

After this feature:
1. **Feature 5** can add editing UI for tags/flags/notes
2. **Images route** can be enhanced with stats context
3. **Analytics** can aggregate stats across sessions
