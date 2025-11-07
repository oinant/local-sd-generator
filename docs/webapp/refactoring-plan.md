# Frontend Refactoring Plan - Detailed Implementation

**Date:** 2025-11-07
**Context:** Suite à l'audit architecture (`frontend-architecture-audit.md`)
**Objectif:** Guide pratique avec exemples de code pour chaque phase

---

## Phase 1: Quick Wins (1-2 jours, ~10h)

### 1.1 Extraire Formatters dans Utils

**Fichiers créés:**
- `src/utils/session-formatter.js`
- `src/utils/date-formatter.js`

**Code:**

```javascript
// src/utils/session-formatter.js
/**
 * Formate le nom d'une session pour l'affichage
 * Supporte les formats:
 * - Old: 2025-10-14_163854_hassaku_actualportrait.prompt
 * - New: 20251014_163854-Hassaku-fantasy-default
 * @param {string} sessionName - Nom brut de la session
 * @returns {string} Nom formaté "YYYY-MM-DD · Name"
 */
export function formatSessionName(sessionName) {
  // Try old format (YYYY-MM-DD_HHMMSS_name)
  const oldMatch = sessionName.match(/^(\d{4}-\d{2}-\d{2})_\d{6}_(.+)/)
  if (oldMatch) {
    const date = oldMatch[1]
    const name = oldMatch[2].replace('.prompt', '')
    return `${date} · ${name}`
  }

  // Try new format (YYYYMMDD_HHMMSS-name)
  const newMatch = sessionName.match(/^(\d{4})(\d{2})(\d{2})_\d{6}-(.+)/)
  if (newMatch) {
    const date = `${newMatch[1]}-${newMatch[2]}-${newMatch[3]}`
    const name = newMatch[4].replace(/-/g, ' ')
    return `${date} · ${name}`
  }

  return sessionName
}
```

```javascript
// src/utils/date-formatter.js
/**
 * Formate une date pour l'affichage
 * @param {Date} date - Date à formatter
 * @returns {string} Date formatée "2 nov. 2025, 13:05"
 */
export function formatDate(date) {
  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}
```

**Tests:**

```javascript
// tests/unit/utils/session-formatter.spec.js
import { describe, test, expect } from 'vitest'
import { formatSessionName } from '@/utils/session-formatter'

describe('formatSessionName', () => {
  test('formats old format sessions', () => {
    const input = '2025-10-14_163854_hassaku_actualportrait.prompt'
    const output = formatSessionName(input)
    expect(output).toBe('2025-10-14 · hassaku_actualportrait')
  })

  test('formats new format sessions', () => {
    const input = '20251014_163854-Hassaku-fantasy-default'
    const output = formatSessionName(input)
    expect(output).toBe('2025-10-14 · Hassaku fantasy default')
  })

  test('returns original name if no match', () => {
    const input = 'custom-session-name'
    const output = formatSessionName(input)
    expect(output).toBe('custom-session-name')
  })
})
```

**Fichiers à modifier:**
```javascript
// Images.vue
import { formatSessionName } from '@/utils/session-formatter'
import { formatDate } from '@/utils/date-formatter'

// Supprimer les méthodes formatSessionName() et formatDate()
// Utiliser directement les fonctions importées
```

```javascript
// SessionCard.vue
import { formatSessionName } from '@/utils/session-formatter'
import { formatDate } from '@/utils/date-formatter'

// Remplacer le computed displayName() par:
computed: {
  displayName() {
    return formatSessionName(this.session.name)
  }
}
```

---

### 1.2 Migrer Vuex → Pinia

**Installation:**
```bash
npm install pinia
```

**Setup:**
```javascript
// src/main.js
import { createPinia } from 'pinia'

const app = createApp(App)
app.use(createPinia())  // Avant createApp
app.use(router)
app.use(vuetify)
app.mount('#app')
```

**Stores Pinia:**

```javascript
// src/stores/auth.js
import { defineStore } from 'pinia'
import ApiService from '@/services/api'
import { useUiStore } from './ui'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false
  }),

  getters: {
    canGenerate: (state) => state.user?.can_generate || false,
    isAdmin: (state) => state.user?.is_admin || false
  },

  actions: {
    async login(token) {
      this.loading = true
      const uiStore = useUiStore()

      try {
        ApiService.setToken(token)
        this.user = await ApiService.getCurrentUser()
        this.isAuthenticated = true

        uiStore.showSnackbar('Connexion réussie', 'success')
        return true
      } catch (error) {
        uiStore.showSnackbar('Token invalide', 'error')
        return false
      } finally {
        this.loading = false
      }
    },

    logout() {
      ApiService.clearAuth()
      this.user = null
      this.isAuthenticated = false

      const uiStore = useUiStore()
      uiStore.showSnackbar('Déconnexion réussie', 'info')
    }
  }
})
```

```javascript
// src/stores/ui.js
import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', {
  state: () => ({
    loading: false,
    snackbar: {
      show: false,
      message: '',
      color: 'info'
    }
  }),

  actions: {
    showSnackbar(message, color = 'info') {
      this.snackbar = {
        show: true,
        message,
        color
      }
    },

    hideSnackbar() {
      this.snackbar.show = false
    },

    setLoading(loading) {
      this.loading = loading
    }
  }
})
```

**Migration des composants:**

```javascript
// Avant (Vuex)
import { mapGetters, mapActions } from 'vuex'

export default {
  computed: {
    ...mapGetters(['isAuthenticated', 'user'])
  },
  methods: {
    ...mapActions(['login', 'logout'])
  }
}

// Après (Pinia)
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

export default {
  setup() {
    const authStore = useAuthStore()
    const { isAuthenticated, user } = storeToRefs(authStore)
    const { login, logout } = authStore

    return {
      isAuthenticated,
      user,
      login,
      logout
    }
  }
}
```

**Ou avec Composition API:**
```javascript
<script setup>
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { isAuthenticated, user } = storeToRefs(authStore)
</script>
```

---

### 1.3 Ajouter Virtual Scrolling

**Installation:**
```bash
npm install vue-virtual-scroller
```

**Setup global:**
```javascript
// src/main.js
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import VueVirtualScroller from 'vue-virtual-scroller'

app.use(VueVirtualScroller)
```

**Refactor ImageGrid:**

```vue
<!-- Images.vue (avant) -->
<v-container fluid>
  <v-row>
    <v-col
      v-for="image in filteredImages"
      :key="image.id"
      cols="12" sm="6" md="4" lg="3" xl="2"
    >
      <v-card class="image-card">
        <v-img :src="image.thumbnail" />
      </v-card>
    </v-col>
  </v-row>
</v-container>

<!-- Images.vue (après) -->
<RecycleScroller
  :items="filteredImages"
  :item-size="220"
  key-field="id"
  class="image-grid-scroller"
  v-slot="{ item: image }"
>
  <v-card class="image-card">
    <v-img :src="image.thumbnail" @click="openImageDialog(image)" />
  </v-card>
</RecycleScroller>

<style scoped>
.image-grid-scroller {
  height: calc(100vh - 80px);
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  padding: 16px;
}
</style>
```

**Benchmark Performance:**
```javascript
// tests/performance/virtual-scroll.bench.js
import { bench, describe } from 'vitest'

describe('Virtual Scroll Performance', () => {
  bench('Render 1000 images (before)', () => {
    // Mesurer temps de render sans virtual scroll
  })

  bench('Render 1000 images (after)', () => {
    // Mesurer temps de render avec virtual scroll
  })
})
```

---

### 1.4 Setup ESLint + Prettier

**Installation:**
```bash
npm install -D eslint prettier eslint-plugin-vue @vue/eslint-config-prettier
```

**Configuration:**

```javascript
// .eslintrc.cjs
module.exports = {
  root: true,
  env: {
    node: true,
    browser: true
  },
  extends: [
    'plugin:vue/vue3-recommended',
    'eslint:recommended',
    '@vue/prettier'
  ],
  parserOptions: {
    ecmaVersion: 2022
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'vue/multi-word-component-names': 'off'
  }
}
```

```json
// .prettierrc.json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "none",
  "printWidth": 100,
  "tabWidth": 2,
  "arrowParens": "always"
}
```

**Scripts package.json:**
```json
{
  "scripts": {
    "lint": "eslint --ext .js,.vue src",
    "lint:fix": "eslint --ext .js,.vue src --fix",
    "format": "prettier --write \"src/**/*.{js,vue,css,md}\""
  }
}
```

---

### 1.5 Setup Vitest

**Installation:**
```bash
npm install -D vitest @vue/test-utils happy-dom
```

**Configuration:**
```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'happy-dom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'tests/']
    }
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
```

**Scripts package.json:**
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

**Premier test:**
```javascript
// tests/unit/utils/session-formatter.spec.js
import { describe, test, expect } from 'vitest'
import { formatSessionName } from '@/utils/session-formatter'

describe('formatSessionName', () => {
  test('works', () => {
    expect(formatSessionName('2025-10-14_163854_test.prompt')).toBe('2025-10-14 · test')
  })
})
```

---

## Phase 2: Composables Extraction (3-5 jours, ~17h)

### 2.1 useSessionPolling()

**Fichier:** `src/composables/useSessionPolling.js`

```javascript
import { ref, onMounted, onBeforeUnmount } from 'vue'
import ApiService from '@/services/api'
import { formatSessionName } from '@/utils/session-formatter'
import { useUiStore } from '@/stores/ui'

/**
 * Composable pour gérer le chargement et le polling des sessions
 * @param {Object} options - Options de polling
 * @param {number} options.pollInterval - Intervalle de polling en ms (défaut: 60000)
 * @param {boolean} options.autoRefresh - Activer l'auto-refresh (défaut: false)
 * @returns {Object} État et actions des sessions
 */
export function useSessionPolling(options = {}) {
  const { pollInterval = 60000, autoRefresh = false } = options

  const sessions = ref([])
  const selectedSession = ref(null)
  const loading = ref(false)
  const autoRefreshEnabled = ref(autoRefresh)
  let intervalId = null

  const uiStore = useUiStore()

  /**
   * Charge toutes les sessions depuis l'API
   */
  async function loadSessions() {
    try {
      loading.value = true
      const response = await ApiService.getSessions()

      sessions.value = response.sessions.map((session) => ({
        name: session.name,
        displayName: formatSessionName(session.name),
        date: new Date(session.created_at),
        count: null,
        countLoading: false
      }))
    } catch (error) {
      console.error('Erreur chargement sessions:', error)
      uiStore.showSnackbar('Erreur lors du chargement des sessions', 'error')
    } finally {
      loading.value = false
    }
  }

  /**
   * Charge le count d'une session spécifique
   * @param {Object} session - Session à charger
   */
  async function loadSessionCount(session) {
    if (session.countLoading || session.count !== null) return

    session.countLoading = true
    try {
      const response = await ApiService.getSessionCount(session.name)
      session.count = response.count
    } catch (error) {
      console.error(`Erreur chargement count ${session.name}:`, error)
      session.count = 0
    } finally {
      session.countLoading = false
    }
  }

  /**
   * Rafraîchit la liste des sessions (détecte nouvelles sessions)
   */
  async function refreshSessions() {
    try {
      const response = await ApiService.getSessions()

      const allSessions = response.sessions.map((session) => ({
        name: session.name,
        displayName: formatSessionName(session.name),
        date: new Date(session.created_at),
        count: null,
        countLoading: false
      }))

      const mostRecent = sessions.value.length > 0 ? sessions.value[0] : null

      if (mostRecent) {
        const newSessions = allSessions.filter((s) => s.date > mostRecent.date)

        if (newSessions.length > 0) {
          sessions.value.unshift(...newSessions)
          uiStore.showSnackbar(
            `${newSessions.length} nouvelle${newSessions.length > 1 ? 's' : ''} session${newSessions.length > 1 ? 's' : ''} détectée${newSessions.length > 1 ? 's' : ''}`,
            'info'
          )
        }

        // Refresh count de la session la plus récente
        const updatedMostRecent = allSessions.find((s) => s.name === mostRecent.name)
        if (updatedMostRecent) {
          await loadSessionCount(mostRecent)
        }
      } else {
        sessions.value = allSessions
      }
    } catch (error) {
      console.error('Erreur refresh sessions:', error)
    }
  }

  /**
   * Active/désactive l'auto-refresh
   */
  function toggleAutoRefresh() {
    autoRefreshEnabled.value = !autoRefreshEnabled.value

    if (autoRefreshEnabled.value) {
      intervalId = setInterval(refreshSessions, pollInterval)
      uiStore.showSnackbar('Auto-refresh activé (1 minute)', 'info')
    } else {
      if (intervalId) {
        clearInterval(intervalId)
        intervalId = null
      }
      uiStore.showSnackbar('Auto-refresh désactivé', 'info')
    }
  }

  /**
   * Sélectionne une session
   * @param {string} sessionName - Nom de la session
   */
  function selectSession(sessionName) {
    selectedSession.value = sessionName
  }

  // Auto-load au mount
  onMounted(() => {
    loadSessions()
  })

  // Cleanup au unmount
  onBeforeUnmount(() => {
    if (intervalId) {
      clearInterval(intervalId)
    }
  })

  return {
    // State
    sessions,
    selectedSession,
    loading,
    autoRefreshEnabled,

    // Actions
    loadSessions,
    loadSessionCount,
    refreshSessions,
    toggleAutoRefresh,
    selectSession
  }
}
```

**Tests:**

```javascript
// tests/unit/composables/useSessionPolling.spec.js
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { useSessionPolling } from '@/composables/useSessionPolling'
import ApiService from '@/services/api'

// Mock API Service
vi.mock('@/services/api', () => ({
  default: {
    getSessions: vi.fn(),
    getSessionCount: vi.fn()
  }
}))

describe('useSessionPolling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test('loadSessions fetches and formats sessions', async () => {
    ApiService.getSessions.mockResolvedValue({
      sessions: [
        { name: '2025-10-14_163854_test.prompt', created_at: '2025-10-14T16:38:54' }
      ]
    })

    const { sessions, loadSessions } = useSessionPolling()
    await loadSessions()

    expect(sessions.value).toHaveLength(1)
    expect(sessions.value[0]).toMatchObject({
      name: '2025-10-14_163854_test.prompt',
      displayName: '2025-10-14 · test',
      count: null
    })
  })

  test('loadSessionCount updates session count', async () => {
    ApiService.getSessionCount.mockResolvedValue({ count: 42 })

    const { loadSessionCount } = useSessionPolling()
    const session = { name: 'test', count: null, countLoading: false }

    await loadSessionCount(session)

    expect(session.count).toBe(42)
    expect(ApiService.getSessionCount).toHaveBeenCalledWith('test')
  })

  test('toggleAutoRefresh starts and stops polling', async () => {
    vi.useFakeTimers()

    const { autoRefreshEnabled, toggleAutoRefresh } = useSessionPolling()

    expect(autoRefreshEnabled.value).toBe(false)

    toggleAutoRefresh()
    expect(autoRefreshEnabled.value).toBe(true)

    toggleAutoRefresh()
    expect(autoRefreshEnabled.value).toBe(false)

    vi.useRealTimers()
  })
})
```

---

### 2.2 useImagePolling()

**Fichier:** `src/composables/useImagePolling.js`

```javascript
import { ref, watch, onBeforeUnmount } from 'vue'
import ApiService from '@/services/api'
import { useUiStore } from '@/stores/ui'

/**
 * Composable pour gérer le chargement et le polling des images d'une session
 * @param {import('vue').Ref<string|null>} sessionName - Nom de la session (ref)
 * @param {Object} options - Options de polling
 * @param {number} options.pollInterval - Intervalle de polling en ms (défaut: 5000)
 * @returns {Object} État et actions des images
 */
export function useImagePolling(sessionName, options = {}) {
  const { pollInterval = 5000 } = options

  const images = ref([])
  const loading = ref(false)
  const lastImageIndex = ref(-1)
  let intervalId = null

  const uiStore = useUiStore()

  /**
   * Charge toutes les images d'une session
   * @param {string} session - Nom de la session
   */
  async function loadImages(session) {
    try {
      loading.value = true
      const response = await ApiService.getSessionImages(session)

      images.value = response.images.map((image) => ({
        id: image.path,
        name: image.filename,
        path: image.path,
        session,
        url: null,
        thumbnail: null,
        thumbnailLoading: false,
        created: new Date(image.created_at)
      }))

      lastImageIndex.value = images.value.length - 1
    } catch (error) {
      console.error(`Erreur chargement images session ${session}:`, error)
      uiStore.showSnackbar('Erreur lors du chargement des images', 'error')
    } finally {
      loading.value = false
    }
  }

  /**
   * Rafraîchit les images (détecte nouvelles images)
   * @param {string} session - Nom de la session
   */
  async function refreshImages(session) {
    try {
      const response = await ApiService.getSessionImages(session, lastImageIndex.value)

      if (response.images.length === 0) return

      const newImages = response.images.map((image) => ({
        id: image.path,
        name: image.filename,
        path: image.path,
        session,
        url: null,
        thumbnail: null,
        thumbnailLoading: false,
        created: new Date(image.created_at)
      }))

      images.value.push(...newImages)
      lastImageIndex.value = images.value.length - 1

      uiStore.showSnackbar(
        `${newImages.length} nouvelle${newImages.length > 1 ? 's' : ''} image${newImages.length > 1 ? 's' : ''} détectée${newImages.length > 1 ? 's' : ''}`,
        'info'
      )
    } catch (error) {
      console.error(`Erreur refresh images session ${session}:`, error)
    }
  }

  /**
   * Démarre le polling des images
   * @param {string} session - Nom de la session
   */
  function startPolling(session) {
    stopPolling()
    intervalId = setInterval(() => {
      refreshImages(session)
    }, pollInterval)
  }

  /**
   * Arrête le polling des images
   */
  function stopPolling() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  // Watch sessionName pour charger automatiquement
  watch(
    sessionName,
    async (newSession, oldSession) => {
      if (newSession !== oldSession) {
        stopPolling()
        images.value = []
        lastImageIndex.value = -1

        if (newSession) {
          await loadImages(newSession)
          startPolling(newSession)
        }
      }
    },
    { immediate: true }
  )

  // Cleanup au unmount
  onBeforeUnmount(() => {
    stopPolling()
  })

  return {
    images,
    loading,
    loadImages,
    refreshImages,
    startPolling,
    stopPolling
  }
}
```

**Tests:**

```javascript
// tests/unit/composables/useImagePolling.spec.js
import { describe, test, expect, vi } from 'vitest'
import { ref } from 'vue'
import { useImagePolling } from '@/composables/useImagePolling'
import ApiService from '@/services/api'

vi.mock('@/services/api', () => ({
  default: {
    getSessionImages: vi.fn()
  }
}))

describe('useImagePolling', () => {
  test('loads images when session changes', async () => {
    ApiService.getSessionImages.mockResolvedValue({
      images: [{ path: 'img1.png', filename: 'img1.png', created_at: '2025-01-01' }]
    })

    const sessionName = ref('session1')
    const { images } = useImagePolling(sessionName)

    await new Promise((resolve) => setTimeout(resolve, 100)) // Wait for watch

    expect(images.value).toHaveLength(1)
    expect(ApiService.getSessionImages).toHaveBeenCalledWith('session1')
  })

  test('refreshImages detects new images', async () => {
    ApiService.getSessionImages
      .mockResolvedValueOnce({ images: [{ path: 'img1.png', filename: 'img1.png', created_at: '2025-01-01' }] })
      .mockResolvedValueOnce({ images: [{ path: 'img2.png', filename: 'img2.png', created_at: '2025-01-02' }] })

    const sessionName = ref('session1')
    const { images, refreshImages } = useImagePolling(sessionName)

    await new Promise((resolve) => setTimeout(resolve, 100))
    await refreshImages('session1')

    expect(images.value).toHaveLength(2)
  })
})
```

---

### 2.3 useImageLazyLoad()

**Fichier:** `src/composables/useImageLazyLoad.js`

```javascript
import { ref, onMounted, onBeforeUnmount } from 'vue'
import ApiService from '@/services/api'

/**
 * Composable pour lazy loading des thumbnails via IntersectionObserver
 * @param {Object} options - Options d'IntersectionObserver
 * @param {string} options.rootMargin - Marge avant intersection (défaut: '100px')
 * @param {number} options.threshold - Seuil de détection (défaut: 0.01)
 * @returns {Object} Actions de lazy loading
 */
export function useImageLazyLoad(options = {}) {
  const { rootMargin = '100px', threshold = 0.01 } = options

  const observer = ref(null)

  /**
   * Charge le thumbnail d'une image
   * @param {Object} image - Image à charger
   */
  async function loadThumbnail(image) {
    if (image.thumbnail || image.thumbnailLoading) return

    image.thumbnailLoading = true
    try {
      image.thumbnail = await ApiService.getImageAsBlob(image.path, true)
    } catch (error) {
      console.error(`Erreur chargement thumbnail ${image.path}:`, error)
    } finally {
      image.thumbnailLoading = false
    }
  }

  /**
   * Initialise l'IntersectionObserver
   */
  function setupObserver() {
    observer.value = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const imagePath = entry.target.dataset.imagePath
            const image = findImageByPath(imagePath)

            if (image) {
              loadThumbnail(image)
              observer.value.unobserve(entry.target)
            }
          }
        })
      },
      { root: null, rootMargin, threshold }
    )
  }

  /**
   * Observe un élément pour lazy loading
   * @param {HTMLElement} element - Élément à observer
   */
  function observe(element) {
    if (observer.value && element) {
      observer.value.observe(element)
    }
  }

  /**
   * Cesse d'observer un élément
   * @param {HTMLElement} element - Élément à ne plus observer
   */
  function unobserve(element) {
    if (observer.value && element) {
      observer.value.unobserve(element)
    }
  }

  /**
   * Trouve une image par son path (helper interne)
   * Note: Cette fonction doit être fournie par le composant parent
   * ou via un store partagé
   */
  function findImageByPath(path) {
    // À implémenter selon le contexte
    console.warn('findImageByPath not implemented')
    return null
  }

  onMounted(() => {
    setupObserver()
  })

  onBeforeUnmount(() => {
    if (observer.value) {
      observer.value.disconnect()
    }
  })

  return {
    observe,
    unobserve,
    loadThumbnail
  }
}
```

---

### 2.4 useSessionFilters()

**Fichier:** `src/composables/useSessionFilters.js`

```javascript
import { ref, computed } from 'vue'

/**
 * Composable pour filtrer les sessions
 * @param {import('vue').Ref<Array>} sessions - Sessions à filtrer (ref)
 * @param {import('vue').Ref<Object>} sessionMetadata - Métadonnées des sessions (ref)
 * @returns {Object} État et actions des filtres
 */
export function useSessionFilters(sessions, sessionMetadata) {
  const filters = ref({
    rating: 'all',
    flags: [],
    minImages: 0,
    maxImages: 1000,
    dateRange: 'all',
    dateStart: null,
    dateEnd: null,
    search: ''
  })

  const sortDescending = ref(true)

  /**
   * Sessions filtrées selon les critères actifs
   */
  const filteredSessions = computed(() => {
    let filtered = [...sessions.value]

    // Filter by rating
    if (filters.value.rating !== 'all') {
      filtered = filtered.filter((session) => {
        const metadata = sessionMetadata.value[session.name]
        if (filters.value.rating === 'unrated') {
          return !metadata || !metadata.user_rating
        }
        return metadata && metadata.user_rating === filters.value.rating
      })
    }

    // Filter by flags
    if (filters.value.flags.length > 0) {
      filtered = filtered.filter((session) => {
        const metadata = sessionMetadata.value[session.name]
        if (!metadata) return false

        return filters.value.flags.every((flag) => {
          if (flag === 'favorite') return metadata.is_favorite
          if (flag === 'test') return metadata.is_test
          if (flag === 'complete') return metadata.is_complete
          return false
        })
      })
    }

    // Filter by image count
    filtered = filtered.filter((session) => {
      const count = session.count ?? 0
      return count >= filters.value.minImages && count <= filters.value.maxImages
    })

    // Filter by search
    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      filtered = filtered.filter((session) =>
        session.displayName.toLowerCase().includes(search)
      )
    }

    // Filter by date range
    if (filters.value.dateRange !== 'all') {
      const now = new Date()
      let startDate = null
      let endDate = null

      switch (filters.value.dateRange) {
        case 'today':
          startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0)
          break
        case 'week':
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
          break
        case 'month':
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
          break
        case 'custom':
          if (filters.value.dateStart) {
            startDate = new Date(filters.value.dateStart)
          }
          if (filters.value.dateEnd) {
            endDate = new Date(filters.value.dateEnd)
            endDate.setHours(23, 59, 59, 999)
          }
          break
      }

      if (startDate || endDate) {
        filtered = filtered.filter((session) => {
          const sessionDate = session.date
          if (startDate && sessionDate < startDate) return false
          if (endDate && sessionDate > endDate) return false
          return true
        })
      }
    }

    // Sort by date
    filtered.sort((a, b) => {
      const timeA = a.date.getTime()
      const timeB = b.date.getTime()
      return sortDescending.value ? timeB - timeA : timeA - timeB
    })

    return filtered
  })

  /**
   * Réinitialise tous les filtres
   */
  function resetFilters() {
    filters.value = {
      rating: 'all',
      flags: [],
      minImages: 0,
      maxImages: 1000,
      dateRange: 'all',
      dateStart: null,
      dateEnd: null,
      search: ''
    }
  }

  /**
   * Inverse l'ordre de tri
   */
  function toggleSortOrder() {
    sortDescending.value = !sortDescending.value
  }

  return {
    filters,
    sortDescending,
    filteredSessions,
    resetFilters,
    toggleSortOrder
  }
}
```

---

### 2.5 useKeyboardNav()

**Fichier:** `src/composables/useKeyboardNav.js`

```javascript
import { onMounted, onBeforeUnmount } from 'vue'

/**
 * Composable pour gérer la navigation au clavier
 * @param {Object} handlers - Handlers pour les touches
 * @param {Function} handlers.onLeft - Handler pour flèche gauche
 * @param {Function} handlers.onRight - Handler pour flèche droite
 * @param {Function} handlers.onEscape - Handler pour échap
 * @returns {Object} Actions de navigation
 */
export function useKeyboardNav(handlers = {}) {
  const { onLeft, onRight, onEscape } = handlers

  /**
   * Handler global des événements clavier
   * @param {KeyboardEvent} event - Événement clavier
   */
  function handleKeyDown(event) {
    switch (event.key) {
      case 'ArrowLeft':
        if (onLeft) onLeft()
        break
      case 'ArrowRight':
        if (onRight) onRight()
        break
      case 'Escape':
        if (onEscape) onEscape()
        break
    }
  }

  /**
   * Active la navigation clavier
   */
  function enable() {
    window.addEventListener('keydown', handleKeyDown)
  }

  /**
   * Désactive la navigation clavier
   */
  function disable() {
    window.removeEventListener('keydown', handleKeyDown)
  }

  // Auto-cleanup au unmount
  onBeforeUnmount(() => {
    disable()
  })

  return {
    enable,
    disable
  }
}
```

---

### 2.6 useImageDialog()

**Fichier:** `src/composables/useImageDialog.js`

```javascript
import { ref, computed, watch } from 'vue'
import ApiService from '@/services/api'

/**
 * Composable pour gérer le dialog d'image et le mode fullscreen
 * @param {import('vue').Ref<Array>} images - Liste des images (ref)
 * @returns {Object} État et actions du dialog
 */
export function useImageDialog(images) {
  const dialogOpen = ref(false)
  const fullscreenOpen = ref(false)
  const selectedImage = ref(null)
  const imageMetadata = ref(null)
  const loadingMetadata = ref(false)

  /**
   * Index de l'image courante dans la liste
   */
  const currentImageIndex = computed(() => {
    if (!selectedImage.value || !images.value) return -1
    return images.value.findIndex((img) => img.id === selectedImage.value.id)
  })

  /**
   * Y a-t-il une image précédente ?
   */
  const hasPreviousImage = computed(() => currentImageIndex.value > 0)

  /**
   * Y a-t-il une image suivante ?
   */
  const hasNextImage = computed(() => {
    return currentImageIndex.value >= 0 && currentImageIndex.value < images.value.length - 1
  })

  /**
   * Ouvre le dialog pour une image
   * @param {Object} image - Image à afficher
   */
  async function openDialog(image) {
    selectedImage.value = image
    dialogOpen.value = true
    imageMetadata.value = null
    loadingMetadata.value = true

    // Charger l'image full size si pas déjà chargée
    if (!image.url) {
      try {
        image.url = await ApiService.getImageAsBlob(image.path, false)
      } catch (error) {
        console.error('Erreur chargement image:', error)
      }
    }

    // Charger les métadonnées
    try {
      imageMetadata.value = await ApiService.getImageMetadata(image.path)
    } catch (error) {
      console.error('Erreur chargement metadata:', error)
    } finally {
      loadingMetadata.value = false
    }
  }

  /**
   * Ferme le dialog
   */
  function closeDialog() {
    dialogOpen.value = false
    fullscreenOpen.value = false
  }

  /**
   * Ouvre le mode fullscreen
   */
  function openFullscreen() {
    fullscreenOpen.value = true
  }

  /**
   * Ferme le mode fullscreen
   */
  function closeFullscreen() {
    fullscreenOpen.value = false
  }

  /**
   * Affiche l'image précédente
   */
  function showPreviousImage() {
    if (hasPreviousImage.value) {
      const prevImage = images.value[currentImageIndex.value - 1]
      openDialog(prevImage)
    }
  }

  /**
   * Affiche l'image suivante
   */
  function showNextImage() {
    if (hasNextImage.value) {
      const nextImage = images.value[currentImageIndex.value + 1]
      openDialog(nextImage)
    }
  }

  // Fermer fullscreen si dialog se ferme
  watch(dialogOpen, (isOpen) => {
    if (!isOpen) {
      fullscreenOpen.value = false
    }
  })

  return {
    dialogOpen,
    fullscreenOpen,
    selectedImage,
    imageMetadata,
    loadingMetadata,
    currentImageIndex,
    hasPreviousImage,
    hasNextImage,
    openDialog,
    closeDialog,
    openFullscreen,
    closeFullscreen,
    showPreviousImage,
    showNextImage
  }
}
```

---

## Phase 3: Component Splitting (5-7 jours, ~21h)

### 3.1 SessionList.vue

**Fichier:** `src/components/sessions/SessionList.vue`

```vue
<template>
  <v-card flat height="100vh" class="d-flex flex-column">
    <session-header
      :loading="loading"
      :sort-descending="sortDescending"
      :auto-refresh="autoRefresh"
      @refresh="emit('refresh')"
      @toggle-auto-refresh="emit('toggle-auto-refresh')"
      @toggle-sort="emit('toggle-sort')"
      @toggle-filters="emit('toggle-filters')"
    />

    <v-divider />

    <v-card-text class="flex-grow-1 overflow-auto pa-0">
      <v-progress-linear v-if="loading" indeterminate />

      <v-list density="compact" class="pa-0">
        <session-card
          v-for="session in sessions"
          :key="session.name"
          :session="session"
          :is-selected="selectedSession === session.name"
          :metadata="metadata[session.name]"
          @select="emit('select', $event)"
          @update-metadata="emit('update-metadata', $event)"
          @add-note="emit('add-note', $event)"
          ref="sessionRefs"
          :data-session-name="session.name"
        />
      </v-list>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'
import SessionHeader from './SessionHeader.vue'
import SessionCard from './SessionCard.vue'

const props = defineProps({
  sessions: { type: Array, required: true },
  selectedSession: { type: String, default: null },
  metadata: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false },
  sortDescending: { type: Boolean, default: true },
  autoRefresh: { type: Boolean, default: false }
})

const emit = defineEmits([
  'select',
  'refresh',
  'toggle-auto-refresh',
  'toggle-sort',
  'toggle-filters',
  'update-metadata',
  'add-note'
])

const sessionRefs = ref([])
</script>
```

---

### 3.2 ImageGrid.vue

**Fichier:** `src/components/images/ImageGrid.vue`

```vue
<template>
  <v-card flat height="100vh" class="d-flex flex-column">
    <image-grid-header
      :session="session"
      :image-count="images.length"
      :tags="currentTags"
      @update:tags="emit('update:tags', $event)"
    />

    <v-divider />

    <v-card-text class="flex-grow-1 overflow-auto">
      <!-- Empty states -->
      <div v-if="!session && !loading" class="text-center py-16">
        <v-icon size="64" color="grey-lighten-2">mdi-folder-outline</v-icon>
        <p class="text-h6 text-grey mt-4">
          Sélectionnez une session dans la liste de gauche
        </p>
      </div>

      <div v-else-if="session && images.length === 0 && !loading" class="text-center py-16">
        <v-icon size="64" color="grey-lighten-2">mdi-image-off-outline</v-icon>
        <p class="text-h6 text-grey mt-4">Aucune image dans cette session</p>
      </div>

      <!-- Image grid with virtual scrolling -->
      <RecycleScroller
        v-else-if="session && images.length > 0"
        :items="images"
        :item-size="220"
        key-field="id"
        class="image-scroller"
        v-slot="{ item: image }"
      >
        <image-card
          :image="image"
          @click="emit('image-click', image)"
        />
      </RecycleScroller>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'
import ImageGridHeader from './ImageGridHeader.vue'
import ImageCard from './ImageCard.vue'

const props = defineProps({
  session: { type: String, default: null },
  images: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  tags: { type: Array, default: () => [] }
})

const emit = defineEmits(['image-click', 'update:tags'])

const currentTags = computed(() => props.tags)
</script>

<style scoped>
.image-scroller {
  height: calc(100vh - 120px);
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  padding: 16px;
}
</style>
```

---

### 3.3 ImageDialog.vue

**Fichier:** `src/components/images/ImageDialog.vue`

```vue
<template>
  <v-dialog v-model="show" max-width="95vw">
    <v-card v-if="image">
      <v-card-title class="d-flex justify-space-between align-center">
        <span>{{ image.name }}</span>
        <v-btn icon variant="text" @click="close">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-4">
        <v-row>
          <!-- Image column with navigation -->
          <v-col cols="12" md="8" class="position-relative">
            <!-- Previous button -->
            <v-btn
              v-if="hasPrevious"
              icon
              variant="elevated"
              color="primary"
              class="nav-button nav-button-left"
              @click="emit('previous')"
            >
              <v-icon>mdi-chevron-left</v-icon>
            </v-btn>

            <!-- Image (click for fullscreen) -->
            <v-img
              :src="image.url"
              contain
              max-height="75vh"
              @click="emit('open-fullscreen')"
              class="cursor-pointer"
              title="Cliquer pour afficher en plein écran"
            />

            <!-- Next button -->
            <v-btn
              v-if="hasNext"
              icon
              variant="elevated"
              color="primary"
              class="nav-button nav-button-right"
              @click="emit('next')"
            >
              <v-icon>mdi-chevron-right</v-icon>
            </v-btn>

            <div class="mt-2 d-flex gap-2">
              <v-chip size="small" color="info">{{ image.session }}</v-chip>
              <v-chip size="small" color="success">{{ formatDate(image.created) }}</v-chip>
              <v-chip size="small" color="grey" variant="outlined">
                {{ currentIndex + 1 }} / {{ totalImages }}
              </v-chip>
            </div>
          </v-col>

          <!-- Metadata column -->
          <v-col cols="12" md="4">
            <image-metadata
              :metadata="metadata"
              :loading="loadingMetadata"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed } from 'vue'
import ImageMetadata from './ImageMetadata.vue'
import { formatDate } from '@/utils/date-formatter'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  image: { type: Object, default: null },
  metadata: { type: Object, default: null },
  loadingMetadata: { type: Boolean, default: false },
  hasPrevious: { type: Boolean, default: false },
  hasNext: { type: Boolean, default: false },
  currentIndex: { type: Number, default: 0 },
  totalImages: { type: Number, default: 0 }
})

const emit = defineEmits([
  'update:modelValue',
  'previous',
  'next',
  'open-fullscreen'
])

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

function close() {
  show.value = false
}
</script>

<style scoped>
.position-relative {
  position: relative;
}

.nav-button {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
}

.nav-button-left {
  left: 10px;
}

.nav-button-right {
  right: 10px;
}

.cursor-pointer {
  cursor: pointer;
}
</style>
```

---

## Phase 4: Store Refactoring (2-3 jours, ~9h)

### 4.1 stores/sessions.js

**Fichier:** `src/stores/sessions.js`

```javascript
import { defineStore } from 'pinia'
import ApiService from '@/services/api'
import { formatSessionName } from '@/utils/session-formatter'
import { useUiStore } from './ui'

export const useSessionStore = defineStore('sessions', {
  state: () => ({
    sessions: [],
    selectedSession: null,
    metadata: {}, // sessionName → metadata
    loading: false
  }),

  getters: {
    selectedSessionMetadata: (state) => {
      return state.selectedSession ? state.metadata[state.selectedSession] : null
    },

    sessionByName: (state) => (name) => {
      return state.sessions.find((s) => s.name === name)
    }
  },

  actions: {
    async loadSessions() {
      this.loading = true
      const uiStore = useUiStore()

      try {
        const response = await ApiService.getSessions()

        this.sessions = response.sessions.map((session) => ({
          name: session.name,
          displayName: formatSessionName(session.name),
          date: new Date(session.created_at),
          count: null,
          countLoading: false
        }))
      } catch (error) {
        console.error('Erreur chargement sessions:', error)
        uiStore.showSnackbar('Erreur lors du chargement des sessions', 'error')
      } finally {
        this.loading = false
      }
    },

    async loadSessionCount(sessionName) {
      const session = this.sessionByName(sessionName)
      if (!session || session.countLoading || session.count !== null) return

      session.countLoading = true
      try {
        const response = await ApiService.getSessionCount(sessionName)
        session.count = response.count
      } catch (error) {
        console.error(`Erreur chargement count ${sessionName}:`, error)
        session.count = 0
      } finally {
        session.countLoading = false
      }
    },

    async loadMetadata(sessionName) {
      try {
        const metadata = await ApiService.getSessionMetadata(sessionName)
        this.metadata[sessionName] = metadata
      } catch (error) {
        if (error.response?.status !== 404) {
          console.error(`Erreur chargement metadata ${sessionName}:`, error)
        }
      }
    },

    async updateMetadata(sessionName, update) {
      const uiStore = useUiStore()

      try {
        const metadata = await ApiService.updateSessionMetadata(sessionName, update)
        this.metadata[sessionName] = metadata

        uiStore.showSnackbar('Metadata mise à jour', 'success')
      } catch (error) {
        console.error('Erreur mise à jour metadata:', error)
        uiStore.showSnackbar('Erreur lors de la mise à jour', 'error')
      }
    },

    selectSession(sessionName) {
      this.selectedSession = sessionName
    }
  }
})
```

---

### 4.2 stores/images.js

**Fichier:** `src/stores/images.js`

```javascript
import { defineStore } from 'pinia'
import ApiService from '@/services/api'
import { useUiStore } from './ui'

export const useImageStore = defineStore('images', {
  state: () => ({
    images: [],
    selectedImage: null,
    loading: false,
    lastIndex: -1
  }),

  getters: {
    imageByPath: (state) => (path) => {
      return state.images.find((img) => img.path === path)
    }
  },

  actions: {
    async loadImages(sessionName) {
      this.loading = true
      const uiStore = useUiStore()

      try {
        const response = await ApiService.getSessionImages(sessionName)

        this.images = response.images.map((image) => ({
          id: image.path,
          name: image.filename,
          path: image.path,
          session: sessionName,
          url: null,
          thumbnail: null,
          thumbnailLoading: false,
          created: new Date(image.created_at)
        }))

        this.lastIndex = this.images.length - 1
      } catch (error) {
        console.error(`Erreur chargement images ${sessionName}:`, error)
        uiStore.showSnackbar('Erreur lors du chargement des images', 'error')
      } finally {
        this.loading = false
      }
    },

    async loadThumbnail(imagePath) {
      const image = this.imageByPath(imagePath)
      if (!image || image.thumbnail || image.thumbnailLoading) return

      image.thumbnailLoading = true
      try {
        image.thumbnail = await ApiService.getImageAsBlob(imagePath, true)
      } catch (error) {
        console.error(`Erreur chargement thumbnail ${imagePath}:`, error)
      } finally {
        image.thumbnailLoading = false
      }
    },

    selectImage(image) {
      this.selectedImage = image
    },

    clearImages() {
      this.images = []
      this.selectedImage = null
      this.lastIndex = -1
    }
  }
})
```

---

## Phase 5: Tests & Optimization (3-5 jours, ~28h)

### 5.1 Tests E2E Playwright

**Installation:**
```bash
npm install -D @playwright/test
npx playwright install
```

**Configuration:**
```javascript
// playwright.config.js
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: !process.env.CI
  },
  use: {
    baseURL: 'http://localhost:5173'
  }
})
```

**Test E2E:**
```javascript
// tests/e2e/image-gallery.spec.js
import { test, expect } from '@playwright/test'

test.describe('Image Gallery', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.fill('input[type="password"]', 'test-token')
    await page.click('button[type="submit"]')
    await page.waitForURL('/images')
  })

  test('user can view sessions list', async ({ page }) => {
    await expect(page.locator('text=Sessions')).toBeVisible()
    await expect(page.locator('.session-card')).toHaveCount(10)
  })

  test('user can select session and view images', async ({ page }) => {
    await page.click('.session-card >> nth=0')
    await expect(page.locator('.image-card')).toHaveCount(50)
  })

  test('user can open image dialog with metadata', async ({ page }) => {
    await page.click('.session-card >> nth=0')
    await page.click('.image-card >> nth=0')

    await expect(page.locator('.image-dialog')).toBeVisible()
    await expect(page.locator('text=Métadonnées')).toBeVisible()
  })

  test('user can navigate images with keyboard', async ({ page }) => {
    await page.click('.session-card >> nth=0')
    await page.click('.image-card >> nth=0')

    await page.keyboard.press('ArrowRight')
    // Vérifier que l'image a changé
    await page.keyboard.press('Escape')
    await expect(page.locator('.image-dialog')).not.toBeVisible()
  })
})
```

---

### 5.2 Performance Optimization

**Lighthouse Audit:**
```bash
npx lighthouse http://localhost:5173/images --view
```

**Optimizations:**

1. **Code Splitting (routes lazy loading)**
```javascript
// router/index.js
const routes = [
  {
    path: '/images',
    name: 'Images',
    component: () => import('@/views/Images.vue') // ✅ Déjà fait
  }
]
```

2. **Image Preloading**
```javascript
// composables/useImageLazyLoad.js
function preloadNextImages(currentIndex, images, count = 3) {
  for (let i = 1; i <= count; i++) {
    const nextIndex = currentIndex + i
    if (nextIndex < images.length) {
      const nextImage = images[nextIndex]
      if (!nextImage.thumbnail) {
        loadThumbnail(nextImage)
      }
    }
  }
}
```

3. **Memoization des filtres**
```javascript
import { memoize } from 'lodash-es'

const filteredSessions = computed(() => {
  return memoize((sessions, filters) => {
    // Logique de filtrage
  })(sessions.value, filters.value)
})
```

---

## Résumé Checklist Complète

### Phase 1: Quick Wins (✅ Immédiat)
- [ ] Extraire `formatSessionName()` → `utils/`
- [ ] Extraire `formatDate()` → `utils/`
- [ ] Migrer Vuex → Pinia
- [ ] Ajouter vue-virtual-scroller
- [ ] Setup ESLint + Prettier
- [ ] Setup Vitest
- [ ] Écrire 5 premiers tests utils

### Phase 2: Composables (✅ Semaine 1-2)
- [ ] Créer `useSessionPolling()` + tests
- [ ] Créer `useImagePolling()` + tests
- [ ] Créer `useImageLazyLoad()` + tests
- [ ] Créer `useSessionFilters()` + tests
- [ ] Créer `useKeyboardNav()` + tests
- [ ] Créer `useImageDialog()` + tests
- [ ] Refactor `Images.vue` utiliser composables

### Phase 3: Components (✅ Semaine 2-3)
- [ ] Créer `SessionList.vue` + tests
- [ ] Créer `ImageGrid.vue` + tests
- [ ] Créer `ImageDialog.vue` + tests
- [ ] Créer `ImageFullscreen.vue` + tests
- [ ] Créer `ImageMetadata.vue` + tests
- [ ] Simplifier `Images.vue` → orchestrator

### Phase 4: Stores (✅ Semaine 3)
- [ ] Créer `stores/sessions.js` + tests
- [ ] Créer `stores/images.js` + tests
- [ ] Migrer état local → Pinia
- [ ] Remplacer props drilling

### Phase 5: Tests & Polish (✅ Semaine 3-4)
- [ ] Tests E2E Playwright (5 scénarios)
- [ ] Performance audit Lighthouse
- [ ] Accessibilité audit
- [ ] Documentation composables (JSDoc)
- [ ] Storybook (optionnel)

---

**Auteur:** Claude Code
**Date:** 2025-11-07
**Version:** 1.0
