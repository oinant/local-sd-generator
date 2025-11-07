# Technical Architecture Document: Feature 3 - Session List with Stats UI

**Feature ID:** F3-SESSION-LIST-UI
**Status:** Architecture Complete
**Created:** 2025-11-07
**Owner:** Technical Architect Agent
**Dependencies:** Feature 2 (Session Stats API), #66 (Vue Router setup)
**Estimated Effort:** 2-3h

---

## 1. Overview

### 1.1 Problem Statement
Current `/sessions` route shows placeholder text. Need **master-list view** displaying all sessions with stats, metadata, and filters. Must be **responsive** (list on mobile, grid on desktop) and support **click-to-detail** interaction.

### 1.2 Goals
1. **Master list** - Display all sessions with thumbnails, stats, tags, completion badges
2. **Responsive layout** - Mobile: vertical list. Desktop: grid layout with detail drawer
3. **Filters** - Liked, test, seed-sweep, model, date range
4. **Click interaction** - Select session → show detail panel (Feature 4)
5. **Performance** - Lazy-load thumbnails, paginate sessions

### 1.3 Non-Goals
- Bulk operations (select multiple sessions) - phase 2
- Drag-and-drop session organization - phase 2
- Real-time session updates during generation - phase 2

---

## 2. UI/UX Design

### 2.1 Layout Structure

#### Desktop (≥960px)

```
┌──────────────────────────────────────────────────────────────┐
│  [Filters Bar]                                    [Search]   │
├──────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ │                        │
│ │ Session │ │ Session │ │ Session │ │  [Detail Drawer]       │
│ │ Card 1  │ │ Card 2  │ │ Card 3  │ │                        │
│ │ [thumb] │ │ [thumb] │ │ [thumb] │ │  Selected: Session 1   │
│ │ Model   │ │ Model   │ │ Model   │ │                        │
│ │ 50 imgs │ │ 100 imgs│ │ 25 imgs │ │  Stats, metadata, etc. │
│ │ [tags]  │ │ [tags]  │ │ [tags]  │ │                        │
│ │ 100%    │ │ 85%     │ │ 100%    │ │  (Feature 4)           │
│ └─────────┘ └─────────┘ └─────────┘ │                        │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ │                        │
│ │ Session │ │ Session │ │ Session │ │                        │
│ │ Card 4  │ │ Card 5  │ │ Card 6  │ │                        │
│ └─────────┘ └─────────┘ └─────────┘ │                        │
└──────────────────────────────────────────────────────────────┘
```

#### Mobile (<960px)

```
┌─────────────────────┐
│  [Filters]  [Search]│
├─────────────────────┤
│ ┌─────────────────┐ │
│ │ Session Card 1  │ │
│ │ [thumb] Model   │ │
│ │ 50 imgs  [tags] │ │
│ │ 100% ✓          │ │
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │ Session Card 2  │ │
│ │ [thumb] Model   │ │
│ │ 100 imgs [tags] │ │
│ │ 85% ⚠           │ │
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │ Session Card 3  │ │
│ └─────────────────┘ │
└─────────────────────┘
```

**Interaction:**
- **Desktop:** Click card → opens detail drawer on right (master-detail)
- **Mobile:** Click card → navigates to `/sessions/:name` (full-page detail)

---

### 2.2 Session Card Design

```vue
┌────────────────────────────────────┐
│ [🖼️ Thumbnail]                     │  ← First image from session
│                                     │
├────────────────────────────────────┤
│ facial_expressions                 │  ← Session name (truncated)
│ illustriousXL_v01                  │  ← Model name (truncated)
├────────────────────────────────────┤
│ 📸 50 images  ⏱️ 2025-11-07 12:00  │  ← Image count + date
│ 🎲 Combinatorial  ✅ 100%          │  ← Mode + completion badge
├────────────────────────────────────┤
│ [character-design] [lora-training] │  ← Tags (chips)
│ ⭐ (if is_favorite)                │  ← Star icon if liked
│ 🧪 (if is_test)                    │  ← Test icon if test session
└────────────────────────────────────┘
```

**Visual States:**
- **Selected:** Blue border + elevation shadow
- **Hover:** Slight elevation + cursor pointer
- **Incomplete:** Orange completion badge if <95%
- **Seed-sweep:** Special icon 🌱 if `is_seed_sweep=true`

---

### 2.3 Filters Bar

```vue
┌─────────────────────────────────────────────────────────────────┐
│ [❤️ Liked] [🧪 Test] [🌱 Seed Sweep] [📦 Complete]            │
│ [Model: ▼] [Date: ▼]                            [🔍 Search]    │
└─────────────────────────────────────────────────────────────────┘
```

**Filter Chips:**
- Toggleable (active = filled, inactive = outlined)
- Click to toggle filter on/off
- Active filters show count (e.g., "Liked (12)")

**Model Filter:**
- Dropdown with model names (extracted from session stats)
- Partial match search

**Date Filter:**
- Date range picker (from/to)
- Presets: Today, Last 7 days, Last 30 days, All time

---

## 3. Component Architecture

### 3.1 Component Tree

```
Sessions.vue (main view)
├── SessionFilters.vue (filter bar)
├── SessionList.vue (grid/list of cards)
│   └── SessionCard.vue (individual card) × N
└── SessionDetailDrawer.vue (Feature 4, desktop only)
```

---

### 3.2 Pinia Store

**File:** `/packages/sd-generator-webui/front/src/stores/sessions.js`

```javascript
import { defineStore } from 'pinia'
import ApiService from '@/services/api'
import { useNotificationStore } from './notification'

export const useSessionsStore = defineStore('sessions', {
  state: () => ({
    // Sessions data
    sessions: [],           // Array of SessionWithStatsAndMetadata
    totalCount: 0,
    loading: false,
    error: null,

    // Pagination
    currentPage: 1,
    pageSize: 50,           // Load 50 sessions at a time

    // Filters
    filters: {
      liked: null,          // null | true | false
      test: null,
      complete: null,
      seedSweep: null,
      model: null,          // string (partial match)
      fromDate: null,       // ISO 8601 string
      toDate: null,
      searchQuery: ''       // Client-side search (session name)
    },

    // Selection (for detail drawer)
    selectedSessionId: null
  }),

  getters: {
    selectedSession(state) {
      return state.sessions.find(s => s.session_id === state.selectedSessionId)
    },

    filteredSessions(state) {
      // Client-side search filter (on session name)
      if (!state.filters.searchQuery) {
        return state.sessions
      }

      const query = state.filters.searchQuery.toLowerCase()
      return state.sessions.filter(s =>
        s.session_id.toLowerCase().includes(query)
      )
    },

    activeFilterCount(state) {
      let count = 0
      if (state.filters.liked !== null) count++
      if (state.filters.test !== null) count++
      if (state.filters.complete !== null) count++
      if (state.filters.seedSweep !== null) count++
      if (state.filters.model !== null) count++
      if (state.filters.fromDate !== null) count++
      if (state.filters.toDate !== null) count++
      return count
    },

    availableModels(state) {
      // Extract unique model names from sessions (for filter dropdown)
      const models = new Set()
      state.sessions.forEach(s => {
        if (s.stats && s.stats.sd_model) {
          models.add(s.stats.sd_model)
        }
      })
      return Array.from(models).sort()
    }
  },

  actions: {
    async loadSessions({ reset = false } = {}) {
      const notifications = useNotificationStore()

      try {
        this.loading = true
        this.error = null

        if (reset) {
          this.currentPage = 1
          this.sessions = []
        }

        const offset = (this.currentPage - 1) * this.pageSize

        const response = await ApiService.getSessions({
          liked: this.filters.liked,
          test: this.filters.test,
          complete: this.filters.complete,
          seedSweep: this.filters.seedSweep,
          model: this.filters.model,
          fromDate: this.filters.fromDate,
          toDate: this.filters.toDate,
          limit: this.pageSize,
          offset
        })

        if (reset) {
          this.sessions = response.sessions
        } else {
          // Append for infinite scroll
          this.sessions.push(...response.sessions)
        }

        this.totalCount = response.total_count

      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to load sessions'
        notifications.show({
          message: this.error,
          color: 'error'
        })
      } finally {
        this.loading = false
      }
    },

    async loadNextPage() {
      if (this.loading) return
      if (this.sessions.length >= this.totalCount) return

      this.currentPage++
      await this.loadSessions({ reset: false })
    },

    async applyFilters(newFilters) {
      // Update filters and reload from page 1
      Object.assign(this.filters, newFilters)
      await this.loadSessions({ reset: true })
    },

    async clearFilters() {
      this.filters = {
        liked: null,
        test: null,
        complete: null,
        seedSweep: null,
        model: null,
        fromDate: null,
        toDate: null,
        searchQuery: ''
      }
      await this.loadSessions({ reset: true })
    },

    selectSession(sessionId) {
      this.selectedSessionId = sessionId
    },

    deselectSession() {
      this.selectedSessionId = null
    },

    async refreshSession(sessionId) {
      // Refresh stats for a specific session
      try {
        const stats = await ApiService.refreshSessionStats(sessionId)

        // Update in store
        const session = this.sessions.find(s => s.session_id === sessionId)
        if (session) {
          session.stats = stats
        }
      } catch (error) {
        console.error(`Failed to refresh session ${sessionId}:`, error)
      }
    },

    async updateSessionMetadata(sessionId, update) {
      // Update metadata and refresh in store
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
  }
})
```

---

### 3.3 Main View Component

**File:** `/packages/sd-generator-webui/front/src/views/Sessions.vue`

```vue
<template>
  <v-container fluid class="pa-4">
    <!-- Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-icon size="32" class="mr-2">mdi-folder-multiple</v-icon>
          <h1 class="text-h4">Sessions</h1>
          <v-spacer></v-spacer>
          <v-chip v-if="activeFilterCount > 0" color="primary" class="mr-2">
            {{ activeFilterCount }} filter(s) active
          </v-chip>
          <v-btn
            v-if="activeFilterCount > 0"
            icon="mdi-filter-off"
            variant="text"
            @click="clearFilters"
            title="Clear all filters"
          ></v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Filters -->
    <SessionFilters
      :filters="filters"
      :available-models="availableModels"
      @update:filters="applyFilters"
    />

    <!-- Session List/Grid -->
    <v-row>
      <!-- Session Cards (left side or full width on mobile) -->
      <v-col
        :cols="selectedSessionId ? 8 : 12"
        :md="selectedSessionId ? 8 : 12"
      >
        <!-- Loading State -->
        <v-progress-linear
          v-if="loading && sessions.length === 0"
          indeterminate
          color="primary"
        ></v-progress-linear>

        <!-- Empty State -->
        <v-alert
          v-if="!loading && sessions.length === 0"
          type="info"
          variant="tonal"
          class="my-4"
        >
          <template v-if="activeFilterCount > 0">
            No sessions match your filters. Try clearing some filters.
          </template>
          <template v-else>
            No sessions found. Generate some images to get started!
          </template>
        </v-alert>

        <!-- Session Grid -->
        <v-row v-if="filteredSessions.length > 0">
          <v-col
            v-for="session in filteredSessions"
            :key="session.session_id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <SessionCard
              :session="session"
              :selected="selectedSessionId === session.session_id"
              @click="selectSession(session.session_id)"
            />
          </v-col>
        </v-row>

        <!-- Infinite Scroll Trigger -->
        <v-row v-if="sessions.length < totalCount">
          <v-col cols="12" class="text-center">
            <v-btn
              @click="loadNextPage"
              :loading="loading"
              color="primary"
              variant="outlined"
            >
              Load More ({{ sessions.length }} / {{ totalCount }})
            </v-btn>
          </v-col>
        </v-row>
      </v-col>

      <!-- Detail Drawer (desktop only) -->
      <v-col
        v-if="selectedSessionId && $vuetify.display.mdAndUp"
        cols="4"
        md="4"
      >
        <SessionDetailDrawer
          :session-id="selectedSessionId"
          @close="deselectSession"
        />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionsStore } from '@/stores/sessions'
import SessionFilters from '@/components/SessionFilters.vue'
import SessionCard from '@/components/SessionCard.vue'
import SessionDetailDrawer from '@/components/SessionDetailDrawer.vue'

const router = useRouter()
const sessionsStore = useSessionsStore()

// Computed
const sessions = computed(() => sessionsStore.sessions)
const filteredSessions = computed(() => sessionsStore.filteredSessions)
const totalCount = computed(() => sessionsStore.totalCount)
const loading = computed(() => sessionsStore.loading)
const selectedSessionId = computed(() => sessionsStore.selectedSessionId)
const filters = computed(() => sessionsStore.filters)
const activeFilterCount = computed(() => sessionsStore.activeFilterCount)
const availableModels = computed(() => sessionsStore.availableModels)

// Methods
const selectSession = (sessionId) => {
  sessionsStore.selectSession(sessionId)

  // On mobile, navigate to detail page
  if (!window.matchMedia('(min-width: 960px)').matches) {
    router.push(`/sessions/${sessionId}`)
  }
}

const deselectSession = () => {
  sessionsStore.deselectSession()
}

const applyFilters = (newFilters) => {
  sessionsStore.applyFilters(newFilters)
}

const clearFilters = () => {
  sessionsStore.clearFilters()
}

const loadNextPage = () => {
  sessionsStore.loadNextPage()
}

// Lifecycle
onMounted(() => {
  // Load sessions on mount
  sessionsStore.loadSessions({ reset: true })
})
</script>

<style scoped>
/* Add any custom styles here */
</style>
```

---

### 3.4 Session Card Component

**File:** `/packages/sd-generator-webui/front/src/components/SessionCard.vue`

```vue
<template>
  <v-card
    :class="['session-card', { selected: selected }]"
    :elevation="selected ? 8 : hover ? 4 : 2"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
    @click="$emit('click')"
  >
    <!-- Thumbnail -->
    <v-img
      :src="thumbnailUrl"
      :aspect-ratio="1"
      cover
      class="session-thumbnail"
    >
      <!-- Badges overlay -->
      <div class="badges-overlay">
        <v-chip
          v-if="session.metadata?.is_favorite"
          size="small"
          color="yellow"
          class="mr-1"
        >
          <v-icon start>mdi-star</v-icon>
          Liked
        </v-chip>

        <v-chip
          v-if="session.metadata?.is_test"
          size="small"
          color="orange"
        >
          <v-icon start>mdi-flask</v-icon>
          Test
        </v-chip>

        <v-chip
          v-if="session.stats?.is_seed_sweep"
          size="small"
          color="green"
        >
          <v-icon start>mdi-seed</v-icon>
          Seed Sweep
        </v-chip>
      </div>
    </v-img>

    <!-- Content -->
    <v-card-text>
      <!-- Session Name -->
      <div class="text-subtitle-1 font-weight-bold text-truncate" :title="session.session_id">
        {{ formatSessionName(session.session_id) }}
      </div>

      <!-- Model Name -->
      <div class="text-caption text-truncate text-medium-emphasis" :title="session.stats?.sd_model">
        {{ session.stats?.sd_model || 'Unknown model' }}
      </div>

      <!-- Stats Row -->
      <div class="d-flex align-center mt-2">
        <v-icon size="small" class="mr-1">mdi-image-multiple</v-icon>
        <span class="text-caption mr-3">{{ session.stats?.images_actual || 0 }}</span>

        <v-icon size="small" class="mr-1">mdi-calendar</v-icon>
        <span class="text-caption">{{ formatDate(session.created_at) }}</span>
      </div>

      <!-- Generation Info -->
      <div class="d-flex align-center mt-1">
        <v-icon size="small" class="mr-1">mdi-auto-fix</v-icon>
        <span class="text-caption mr-3">{{ session.stats?.generation_mode || 'unknown' }}</span>

        <!-- Completion Badge -->
        <v-chip
          :color="completionColor"
          size="x-small"
          class="ml-auto"
        >
          {{ session.stats?.completion_percentage?.toFixed(0) || 0 }}%
        </v-chip>
      </div>

      <!-- Tags -->
      <div v-if="session.metadata?.tags?.length > 0" class="mt-2">
        <v-chip
          v-for="tag in session.metadata.tags.slice(0, 2)"
          :key="tag"
          size="x-small"
          class="mr-1"
          variant="outlined"
        >
          {{ tag }}
        </v-chip>
        <v-chip
          v-if="session.metadata.tags.length > 2"
          size="x-small"
          variant="text"
        >
          +{{ session.metadata.tags.length - 2 }}
        </v-chip>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import ApiService from '@/services/api'

const props = defineProps({
  session: {
    type: Object,
    required: true
  },
  selected: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

const hover = ref(false)

const thumbnailUrl = computed(() => {
  // TODO: Get first image from session for thumbnail
  // For now, use placeholder
  return `${ApiService.baseURL}/api/files/serve/${props.session.session_path}/.thumbnails/001.jpg`
})

const completionColor = computed(() => {
  const pct = props.session.stats?.completion_percentage || 0
  if (pct >= 95) return 'success'
  if (pct >= 75) return 'warning'
  return 'error'
})

const formatSessionName = (sessionId) => {
  // Remove timestamp prefix: 20251107_120000-name → name
  const match = sessionId.match(/^\d{8}_\d{6}-(.+)$/)
  return match ? match[1] : sessionId
}

const formatDate = (isoDate) => {
  const date = new Date(isoDate)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<style scoped>
.session-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.session-card.selected {
  border: 2px solid rgb(var(--v-theme-primary));
}

.session-thumbnail {
  position: relative;
}

.badges-overlay {
  position: absolute;
  top: 8px;
  left: 8px;
  display: flex;
  gap: 4px;
}
</style>
```

---

### 3.5 Filters Component

**File:** `/packages/sd-generator-webui/front/src/components/SessionFilters.vue`

```vue
<template>
  <v-card class="mb-4">
    <v-card-text>
      <!-- Filter Chips Row -->
      <div class="d-flex flex-wrap align-center mb-2">
        <v-chip
          :variant="localFilters.liked === true ? 'flat' : 'outlined'"
          :color="localFilters.liked === true ? 'primary' : undefined"
          class="mr-2 mb-2"
          @click="toggleFilter('liked')"
        >
          <v-icon start>mdi-heart</v-icon>
          Liked
        </v-chip>

        <v-chip
          :variant="localFilters.test === true ? 'flat' : 'outlined'"
          :color="localFilters.test === true ? 'primary' : undefined"
          class="mr-2 mb-2"
          @click="toggleFilter('test')"
        >
          <v-icon start>mdi-flask</v-icon>
          Test
        </v-chip>

        <v-chip
          :variant="localFilters.seedSweep === true ? 'flat' : 'outlined'"
          :color="localFilters.seedSweep === true ? 'primary' : undefined"
          class="mr-2 mb-2"
          @click="toggleFilter('seedSweep')"
        >
          <v-icon start>mdi-seed</v-icon>
          Seed Sweep
        </v-chip>

        <v-chip
          :variant="localFilters.complete === true ? 'flat' : 'outlined'"
          :color="localFilters.complete === true ? 'primary' : undefined"
          class="mr-2 mb-2"
          @click="toggleFilter('complete')"
        >
          <v-icon start>mdi-check-circle</v-icon>
          Complete
        </v-chip>
      </div>

      <!-- Advanced Filters Row -->
      <v-row>
        <!-- Model Filter -->
        <v-col cols="12" sm="4">
          <v-select
            v-model="localFilters.model"
            :items="availableModels"
            label="Model"
            clearable
            density="compact"
            @update:model-value="emitFilters"
          >
            <template #prepend-inner>
              <v-icon size="small">mdi-package-variant</v-icon>
            </template>
          </v-select>
        </v-col>

        <!-- Date Range (simplified) -->
        <v-col cols="12" sm="4">
          <v-select
            v-model="dateRangePreset"
            :items="dateRangePresets"
            label="Date Range"
            density="compact"
            @update:model-value="applyDateRangePreset"
          >
            <template #prepend-inner>
              <v-icon size="small">mdi-calendar</v-icon>
            </template>
          </v-select>
        </v-col>

        <!-- Search -->
        <v-col cols="12" sm="4">
          <v-text-field
            v-model="localFilters.searchQuery"
            label="Search sessions"
            density="compact"
            clearable
            @update:model-value="emitFilters"
          >
            <template #prepend-inner>
              <v-icon size="small">mdi-magnify</v-icon>
            </template>
          </v-text-field>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  filters: {
    type: Object,
    required: true
  },
  availableModels: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:filters'])

// Local copy of filters
const localFilters = ref({ ...props.filters })

const dateRangePreset = ref('all')
const dateRangePresets = [
  { title: 'All Time', value: 'all' },
  { title: 'Today', value: 'today' },
  { title: 'Last 7 Days', value: '7d' },
  { title: 'Last 30 Days', value: '30d' }
]

// Watch props.filters for external changes
watch(() => props.filters, (newFilters) => {
  localFilters.value = { ...newFilters }
}, { deep: true })

const toggleFilter = (filterName) => {
  const current = localFilters.value[filterName]
  localFilters.value[filterName] = current === true ? null : true
  emitFilters()
}

const applyDateRangePreset = () => {
  const now = new Date()

  switch (dateRangePreset.value) {
    case 'today':
      localFilters.value.fromDate = now.toISOString().split('T')[0]
      localFilters.value.toDate = null
      break
    case '7d':
      now.setDate(now.getDate() - 7)
      localFilters.value.fromDate = now.toISOString().split('T')[0]
      localFilters.value.toDate = null
      break
    case '30d':
      now.setDate(now.getDate() - 30)
      localFilters.value.fromDate = now.toISOString().split('T')[0]
      localFilters.value.toDate = null
      break
    case 'all':
    default:
      localFilters.value.fromDate = null
      localFilters.value.toDate = null
      break
  }

  emitFilters()
}

const emitFilters = () => {
  emit('update:filters', { ...localFilters.value })
}
</script>
```

---

## 4. Testing Strategy

### 4.1 Component Unit Tests

**File:** `/packages/sd-generator-webui/front/tests/unit/components/SessionCard.spec.js`

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SessionCard from '@/components/SessionCard.vue'

describe('SessionCard', () => {
  it('renders session name and stats', () => {
    const wrapper = mount(SessionCard, {
      props: {
        session: {
          session_id: '20251107_120000-test_session',
          created_at: '2025-11-07T12:00:00',
          stats: {
            sd_model: 'test_model.safetensors',
            images_actual: 50,
            completion_percentage: 100,
            generation_mode: 'combinatorial'
          },
          metadata: null
        }
      }
    })

    expect(wrapper.text()).toContain('test_session')
    expect(wrapper.text()).toContain('test_model.safetensors')
    expect(wrapper.text()).toContain('50')
    expect(wrapper.text()).toContain('100%')
  })

  it('shows liked badge when is_favorite=true', () => {
    const wrapper = mount(SessionCard, {
      props: {
        session: {
          session_id: '20251107_120000-test',
          stats: {},
          metadata: { is_favorite: true }
        }
      }
    })

    expect(wrapper.text()).toContain('Liked')
  })

  it('emits click event', async () => {
    const wrapper = mount(SessionCard, {
      props: {
        session: { session_id: 'test', stats: {}, metadata: null }
      }
    })

    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
```

---

## 5. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Large session lists** (1000+ sessions) cause UI lag | Medium | Medium | Implement virtual scrolling with `vue-virtual-scroller`. Lazy-load thumbnails with Intersection Observer. |
| **Thumbnail loading** slows page render | High | Medium | Use lazy loading (`v-lazy`) + placeholder images. Generate thumbnail URLs in backend. |
| **Filter state lost** on page refresh | Low | Low | Persist filters in URL query params (`?liked=true&model=X`). Use Vue Router query sync. |
| **Mobile detail drawer** breaks layout | Low | Medium | Use responsive navigation: drawer on desktop, full-page route on mobile. Test on multiple screen sizes. |

---

## 6. Strategic Alignment

### 6.1 Enables Future Features

**Feature #70 (Variation Rating):**
- Click session → see variations → rate variations
- Session list shows which sessions have been rated

**Feature #61 (Image Tagging):**
- Batch tag all images in session from session card
- Filter sessions by image tags (phase 2)

**Model Analysis:**
- Filter by model → see all sessions with that model
- Aggregate stats per model

---

## 7. Success Criteria

1. **Performance:** Renders 100 sessions in <1s
2. **Responsiveness:** Works on mobile (320px) and desktop (1920px)
3. **Interaction:** Click session → detail drawer opens in <100ms
4. **Filters:** Apply filters → results update in <500ms
5. **Accessibility:** Keyboard navigation works (Tab, Enter, Escape)

---

## 8. Implementation Checklist

- [ ] Create Pinia `sessionsStore`
- [ ] Implement `Sessions.vue` main view
- [ ] Implement `SessionCard.vue` component
- [ ] Implement `SessionFilters.vue` component
- [ ] Add responsive layout (desktop grid, mobile list)
- [ ] Add infinite scroll / pagination
- [ ] Implement thumbnail lazy loading
- [ ] Add keyboard navigation (Tab, Enter, Escape)
- [ ] Write component unit tests (3 test cases)
- [ ] Test on mobile (320px) and desktop (1920px)
- [ ] Test with 100+ sessions (performance)

---

## 9. Files to Create/Modify

### New Files
- `/packages/sd-generator-webui/front/src/stores/sessions.js` (300 lines)
- `/packages/sd-generator-webui/front/src/components/SessionCard.vue` (200 lines)
- `/packages/sd-generator-webui/front/src/components/SessionFilters.vue` (150 lines)
- `/packages/sd-generator-webui/front/tests/unit/components/SessionCard.spec.js` (100 lines)

### Modified Files
- `/packages/sd-generator-webui/front/src/views/Sessions.vue` (replace placeholder, +300 lines)

---

## 10. Next Steps

After this feature is complete:
1. **Feature 4** can be integrated as `SessionDetailDrawer.vue` component
2. **Feature 5** can add metadata editing to session cards
3. **Thumbnail generation** can be added to backend (Feature 6, future)
