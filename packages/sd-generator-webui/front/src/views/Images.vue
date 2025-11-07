<template>
  <v-container fluid class="pa-0 fill-height">
    <v-row no-gutters class="fill-height">
      <!-- Panneau latéral avec liste des sessions -->
      <v-col cols="3" class="border-r">
        <v-card flat height="100vh" class="d-flex flex-column">
          <v-card-title class="pb-2 d-flex justify-space-between align-center">
            <span>
              <v-icon class="mr-2">mdi-folder-multiple</v-icon>
              Sessions
              <v-chip size="x-small" variant="text" class="ml-2">
                <v-icon size="x-small">mdi-sort-clock-descending</v-icon>
                Par date {{ sortDescending ? '↓' : '↑' }}
              </v-chip>
            </span>
            <div class="d-flex gap-1">
              <v-btn
                icon
                size="small"
                variant="text"
                @click="refreshSessions"
                :loading="loadingSessions"
                title="Rafraîchir la liste des sessions"
              >
                <v-icon>mdi-refresh</v-icon>
              </v-btn>
              <v-btn
                icon
                size="small"
                :variant="autoRefresh ? 'tonal' : 'text'"
                :color="autoRefresh ? 'primary' : undefined"
                @click="toggleAutoRefresh"
                title="Auto-refresh (1 minute)"
              >
                <v-icon>{{ autoRefresh ? 'mdi-play-circle' : 'mdi-play-circle-outline' }}</v-icon>
              </v-btn>
              <v-btn
                icon
                size="small"
                variant="text"
                @click="toggleSortOrder"
                title="Inverser l'ordre de tri"
              >
                <v-icon>{{ sortDescending ? 'mdi-sort-descending' : 'mdi-sort-ascending' }}</v-icon>
              </v-btn>
              <v-btn
                icon
                size="small"
                variant="text"
                @click="filtersDrawer = !filtersDrawer"
                title="Filtres"
              >
                <v-icon>mdi-filter-variant</v-icon>
              </v-btn>
            </div>
          </v-card-title>

          <v-divider />

          <v-card-text class="flex-grow-1 overflow-auto pa-0">
            <v-progress-linear v-if="loadingSessions" indeterminate />

            <v-list density="compact" class="pa-0">
              <!-- Liste des sessions avec SessionCard -->
              <session-card
                v-for="session in filteredSessions"
                :key="session.name"
                :session="session"
                :is-selected="selectedSession === session.name"
                :metadata="sessionMetadata[session.name]"
                @select="selectSession"
                @update-metadata="handleMetadataUpdate"
                @add-note="openNoteDialog"
                ref="sessionItems"
                :data-session-name="session.name"
              />
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Zone principale avec galerie -->
      <v-col cols="9">
        <v-card flat height="100vh" class="d-flex flex-column">
          <v-card-title class="pb-2">
            <div class="d-flex align-center w-100">
              <v-icon class="mr-2">mdi-image-multiple</v-icon>
              <span class="flex-grow-1">
                {{ selectedSession ? formatSessionName(selectedSession) : 'Sélectionnez une session' }}
              </span>
              <div v-if="selectedSession" class="d-flex align-center gap-2">
                <v-chip color="primary" variant="outlined" size="small">
                  {{ allImages.length }} image{{ allImages.length > 1 ? 's' : '' }}
                </v-chip>
                <v-chip color="success" variant="tonal" size="small">
                  <v-icon size="x-small" class="mr-1">mdi-update</v-icon>
                  Auto (5s)
                </v-chip>
              </div>
            </div>
          </v-card-title>

          <!-- Tags inline pour la session courante -->
          <v-card-subtitle v-if="selectedSession" class="pt-0 pb-2">
            <div class="d-flex align-center gap-2">
              <v-icon size="small">mdi-tag-multiple</v-icon>
              <v-combobox
                v-model="currentSessionTags"
                :items="allTags"
                label="Tags"
                multiple
                chips
                clearable
                density="compact"
                variant="outlined"
                hide-details
                @update:model-value="handleTagsUpdate"
                class="flex-grow-1"
              >
                <template v-slot:chip="{ item, props }">
                  <v-chip
                    v-bind="props"
                    size="small"
                    closable
                    color="primary"
                    variant="tonal"
                  >
                    {{ item.title }}
                  </v-chip>
                </template>
              </v-combobox>
            </div>
          </v-card-subtitle>

          <v-divider />

          <v-card-text class="flex-grow-1 overflow-auto">
            <!-- Message si aucune session sélectionnée -->
            <div v-if="!selectedSession && !loading" class="text-center py-16">
              <v-icon size="64" color="grey-lighten-2">mdi-folder-outline</v-icon>
              <p class="text-h6 text-grey mt-4">
                Sélectionnez une session dans la liste de gauche
              </p>
            </div>

            <!-- Message si aucune image dans la session -->
            <div v-else-if="selectedSession && allImages.length === 0 && !loading" class="text-center py-16">
              <v-icon size="64" color="grey-lighten-2">mdi-image-off-outline</v-icon>
              <p class="text-h6 text-grey mt-4">
                Aucune image dans cette session
              </p>
            </div>

            <!-- Grille d'images -->
            <v-container v-else-if="selectedSession && allImages.length > 0" fluid>
              <v-row>
                <v-col
                  v-for="image in filteredImages"
                  :key="image.id"
                  cols="12" sm="6" md="4" lg="3" xl="2"
                >
                  <v-card class="image-card" elevation="2">
                    <div
                      ref="imageRefs"
                      :data-image-path="image.path"
                      class="lazy-image-container"
                    >
                      <v-img
                        v-if="image.thumbnail"
                        :src="image.thumbnail"
                        :aspect-ratio="1"
                        cover
                        @click="openImageDialog(image)"
                        class="cursor-pointer"
                      >
                        <template v-slot:placeholder>
                          <div class="d-flex align-center justify-center fill-height">
                            <v-progress-circular indeterminate color="grey-lighten-2" />
                          </div>
                        </template>
                      </v-img>
                      <div
                        v-else
                        class="d-flex align-center justify-center fill-height bg-grey-lighten-3"
                        style="aspect-ratio: 1"
                      >
                        <v-progress-circular v-if="image.thumbnailLoading" indeterminate color="primary" />
                        <v-icon v-else size="48" color="grey-lighten-1">mdi-image-outline</v-icon>
                      </div>
                    </div>
                    <v-card-subtitle class="text-caption pa-2">
                      {{ image.name }}
                    </v-card-subtitle>
                  </v-card>
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog pour l'image avec métadonnées -->
    <v-dialog v-model="imageDialog" max-width="95vw">
      <v-card v-if="selectedImage">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>{{ selectedImage.name }}</span>
          <v-btn icon variant="text" @click="imageDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4">
          <v-row>
            <!-- Colonne image avec navigation -->
            <v-col cols="12" md="8" class="position-relative">
              <!-- Bouton Précédent -->
              <v-btn
                v-if="hasPreviousImage"
                icon
                variant="elevated"
                color="primary"
                class="nav-button nav-button-left"
                @click="showPreviousImage"
              >
                <v-icon>mdi-chevron-left</v-icon>
              </v-btn>

              <!-- Image (cliquable pour fullscreen) -->
              <v-img
                :src="selectedImage.url"
                contain
                max-height="75vh"
                @click="openFullscreen"
                class="cursor-pointer fullscreen-trigger"
                title="Cliquer pour afficher en plein écran"
              />

              <!-- Bouton Suivant -->
              <v-btn
                v-if="hasNextImage"
                icon
                variant="elevated"
                color="primary"
                class="nav-button nav-button-right"
                @click="showNextImage"
              >
                <v-icon>mdi-chevron-right</v-icon>
              </v-btn>

              <div class="mt-2 d-flex gap-2">
                <v-chip size="small" color="info">{{ selectedImage.session }}</v-chip>
                <v-chip size="small" color="success">{{ formatDate(selectedImage.created) }}</v-chip>
                <v-chip size="small" color="grey" variant="outlined">
                  {{ currentImageIndex + 1 }} / {{ allImages.length }}
                </v-chip>
              </div>
            </v-col>

            <!-- Colonne métadonnées -->
            <v-col cols="12" md="4">
              <div class="text-h6 mb-3">
                <v-icon class="mr-2">mdi-information-outline</v-icon>
                Métadonnées
              </div>

              <div v-if="loadingMetadata" class="text-center py-4">
                <v-progress-circular indeterminate />
              </div>

              <div v-else-if="imageMetadata" style="max-height: 75vh; overflow-y: auto;">
                <!-- Prompt -->
                <div class="mb-3">
                  <div class="text-subtitle-2 mb-1">Prompt</div>
                  <div class="text-caption pa-2 bg-grey-lighten-4 rounded" style="max-height: 150px; overflow-y: auto;">
                    {{ imageMetadata.prompt }}
                  </div>
                </div>

                <!-- Negative Prompt -->
                <div class="mb-3" v-if="imageMetadata.negative_prompt">
                  <div class="text-subtitle-2 mb-1">Negative Prompt</div>
                  <div class="text-caption pa-2 bg-grey-lighten-4 rounded" style="max-height: 100px; overflow-y: auto;">
                    {{ imageMetadata.negative_prompt }}
                  </div>
                </div>

                <!-- Paramètres -->
                <div class="text-subtitle-2 mb-2">Paramètres</div>
                <div class="d-flex flex-wrap gap-1">
                  <v-chip size="small" v-for="(value, key) in metadataFields" :key="key">
                    <strong>{{ key }}:</strong>&nbsp;{{ value }}
                  </v-chip>
                </div>

                <!-- Infos du manifest (session) -->
                <v-divider class="my-3" />

                <div v-if="loadingManifest" class="text-center py-2">
                  <v-progress-circular indeterminate size="20" width="2" />
                  <div class="text-caption mt-1">Chargement infos session...</div>
                </div>

                <div v-else-if="manifestDataForCurrentImage">
                  <div class="text-h6 mb-2">
                    <v-icon class="mr-2" size="small">mdi-folder-cog</v-icon>
                    Infos de Session
                  </div>

                  <!-- Applied Variations -->
                  <div v-if="Object.keys(manifestDataForCurrentImage.appliedVariations).length > 0" class="mb-3">
                    <div class="text-subtitle-2 mb-1">Variations Appliquées</div>
                    <div class="d-flex flex-wrap gap-1">
                      <v-chip size="small" color="secondary" v-for="(value, key) in manifestDataForCurrentImage.appliedVariations" :key="key">
                        <strong>{{ key }}:</strong>&nbsp;{{ value }}
                      </v-chip>
                    </div>
                  </div>

                  <!-- Generation Params -->
                  <div v-if="Object.keys(manifestDataForCurrentImage.generationParams).length > 0" class="mb-3">
                    <div class="text-subtitle-2 mb-1">Paramètres de Génération</div>
                    <div class="d-flex flex-wrap gap-1">
                      <v-chip size="small" color="info" v-for="(value, key) in manifestDataForCurrentImage.generationParams" :key="key">
                        <strong>{{ key }}:</strong>&nbsp;{{ value }}
                      </v-chip>
                    </div>
                  </div>

                  <!-- API Params (already in imageMetadata, but can show from manifest too) -->
                  <div v-if="Object.keys(manifestDataForCurrentImage.apiParams).length > 0" class="mb-3">
                    <div class="text-subtitle-2 mb-1">Paramètres API (session)</div>
                    <div class="d-flex flex-wrap gap-1">
                      <v-chip size="small" color="grey" variant="outlined" v-for="(value, key) in manifestDataForCurrentImage.apiParams" :key="key">
                        <strong>{{ key }}:</strong>&nbsp;{{ value }}
                      </v-chip>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else class="text-center py-4">
                <v-alert type="info" variant="outlined" density="compact">
                  Chargement des métadonnées...
                </v-alert>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Overlay Fullscreen pour l'image -->
    <v-overlay
      v-model="fullscreenOverlay"
      class="fullscreen-overlay"
      :persistent="false"
      :z-index="2000"
    >
      <div class="fullscreen-container" @click="closeFullscreen">
        <!-- Bouton fermer -->
        <v-btn
          icon
          size="large"
          variant="elevated"
          color="white"
          class="fullscreen-close"
          @click.stop="closeFullscreen"
        >
          <v-icon color="black">mdi-close</v-icon>
        </v-btn>

        <!-- Bouton Précédent -->
        <v-btn
          v-if="hasPreviousImage"
          icon
          size="large"
          variant="elevated"
          color="primary"
          class="fullscreen-nav fullscreen-nav-left"
          @click.stop="showPreviousImage"
        >
          <v-icon>mdi-chevron-left</v-icon>
        </v-btn>

        <!-- Image fullscreen -->
        <div class="fullscreen-image-wrapper" @click.stop>
          <img
            v-if="selectedImage"
            :src="selectedImage.url"
            class="fullscreen-image"
            alt="Fullscreen image"
          />
        </div>

        <!-- Bouton Suivant -->
        <v-btn
          v-if="hasNextImage"
          icon
          size="large"
          variant="elevated"
          color="primary"
          class="fullscreen-nav fullscreen-nav-right"
          @click.stop="showNextImage"
        >
          <v-icon>mdi-chevron-right</v-icon>
        </v-btn>

        <!-- Indicateur de position -->
        <div class="fullscreen-indicator">
          <v-chip color="white" variant="elevated">
            <strong>{{ currentImageIndex + 1 }}</strong> / {{ allImages.length }}
          </v-chip>
        </div>
      </div>
    </v-overlay>

    <!-- Drawer pour les filtres -->
    <v-navigation-drawer
      v-model="filtersDrawer"
      location="left"
      temporary
      width="350"
    >
      <session-filters
        :filters="filters"
        :max-image-count="1000"
        @update:filters="filters = $event"
      />
    </v-navigation-drawer>

  </v-container>
</template>

<script>
import ApiService from '@/services/api'
import SessionCard from '@/components/SessionCard.vue'
import SessionFilters from '@/components/SessionFilters.vue'

export default {
  name: 'ImagesView',

  components: {
    SessionCard,
    SessionFilters
  },

  data() {
    return {
      loading: false,
      loadingSessions: false,
      sessions: [],  // Liste des sessions depuis l'API
      sessionMetadata: {},  // Metadata indexé par session.name
      allImages: [],
      selectedSession: null,
      imageDialog: false,
      metadataDialog: false,
      fullscreenOverlay: false,
      selectedImage: null,
      imageMetadata: null,
      loadingMetadata: false,
      sessionManifest: null,
      loadingManifest: false,
      intersectionObserver: null,
      sessionObserver: null,
      // Sort
      sortDescending: true,  // Par défaut: plus récent d'abord
      // Auto-refresh
      autoRefresh: false,
      autoRefreshInterval: null,
      // Image polling (for current session)
      imagePollingInterval: null,
      lastImageIndex: -1,  // Track highest known image index for polling
      // Tags
      allTags: [],
      // Filtres
      filtersDrawer: false,
      filters: {
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
  },

  watch: {
    // Observer les changements dans filteredImages pour attacher l'observer
    filteredImages: {
      handler() {
        // Attendre le prochain tick pour que le DOM soit mis à jour
        this.$nextTick(() => {
          this.attachObservers()
        })
      }
    },

    // Gérer les raccourcis clavier quand la modal est ouverte
    imageDialog(isOpen) {
      if (isOpen) {
        window.addEventListener('keydown', this.handleKeyNavigation)
      } else {
        window.removeEventListener('keydown', this.handleKeyNavigation)
        // Fermer aussi le fullscreen si la dialog se ferme
        this.fullscreenOverlay = false
      }
    }
  },

  computed: {
    // Tags de la session courante
    currentSessionTags: {
      get() {
        if (!this.selectedSession) return []
        return this.sessionMetadata[this.selectedSession]?.tags || []
      },
      set(newTags) {
        // Sera géré par handleTagsUpdate
      }
    },

    // Sessions filtrées selon les filtres actifs
    filteredSessions() {
      let filtered = [...this.sessions]

      // Filter by rating
      if (this.filters.rating !== 'all') {
        filtered = filtered.filter(session => {
          const metadata = this.sessionMetadata[session.name]
          if (this.filters.rating === 'unrated') {
            return !metadata || !metadata.user_rating
          }
          return metadata && metadata.user_rating === this.filters.rating
        })
      }

      // Filter by flags
      if (this.filters.flags.length > 0) {
        filtered = filtered.filter(session => {
          const metadata = this.sessionMetadata[session.name]
          if (!metadata) return false

          return this.filters.flags.every(flag => {
            if (flag === 'favorite') return metadata.is_favorite
            if (flag === 'test') return metadata.is_test
            if (flag === 'complete') return metadata.is_complete
            return false
          })
        })
      }

      // Filter by image count
      filtered = filtered.filter(session => {
        const count = session.count ?? 0
        return count >= this.filters.minImages && count <= this.filters.maxImages
      })

      // Filter by search
      if (this.filters.search) {
        const search = this.filters.search.toLowerCase()
        filtered = filtered.filter(session =>
          session.displayName.toLowerCase().includes(search)
        )
      }

      // Filter by date range
      if (this.filters.dateRange !== 'all') {
        const now = new Date()
        let startDate = null
        let endDate = null

        switch (this.filters.dateRange) {
          case 'today':
            // Start of today
            startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0)
            break
          case 'week':
            // 7 days ago
            startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
            break
          case 'month':
            // 30 days ago
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
            break
          case 'custom':
            // Custom date range
            if (this.filters.dateStart) {
              startDate = new Date(this.filters.dateStart)
            }
            if (this.filters.dateEnd) {
              // End of selected day (23:59:59)
              endDate = new Date(this.filters.dateEnd)
              endDate.setHours(23, 59, 59, 999)
            }
            break
        }

        if (startDate || endDate) {
          filtered = filtered.filter(session => {
            const sessionDate = session.date
            if (startDate && sessionDate < startDate) return false
            if (endDate && sessionDate > endDate) return false
            return true
          })
        }
      }

      // Sort by date (respects sortDescending flag)
      filtered.sort((a, b) => {
        const timeA = a.date.getTime()
        const timeB = b.date.getTime()
        return this.sortDescending ? timeB - timeA : timeA - timeB
      })

      return filtered
    },

    // Images filtrées (toutes si pas de session sélectionnée)
    filteredImages() {
      return this.allImages
    },

    // Index de l'image courante dans la liste
    currentImageIndex() {
      if (!this.selectedImage) return -1
      return this.allImages.findIndex(img => img.id === this.selectedImage.id)
    },

    // Y a-t-il une image précédente ?
    hasPreviousImage() {
      return this.currentImageIndex > 0
    },

    // Y a-t-il une image suivante ?
    hasNextImage() {
      return this.currentImageIndex >= 0 && this.currentImageIndex < this.allImages.length - 1
    },

    // Extraire les infos du manifest pour l'image courante
    manifestDataForCurrentImage() {
      if (!this.sessionManifest || !this.selectedImage) return null

      // Trouver l'entry de cette image dans manifest.images
      const imageEntry = this.sessionManifest.images?.find(
        img => img.filename === this.selectedImage.name
      )

      if (!imageEntry) return null

      return {
        appliedVariations: imageEntry.applied_variations || {},
        generationParams: this.sessionManifest.snapshot?.generation_params || {},
        apiParams: this.sessionManifest.snapshot?.api_params || {}
      }
    },

    // Extraire les champs de métadonnées à afficher en chips
    metadataFields() {
      if (!this.imageMetadata) return {}

      const fields = {}
      const keys = ['seed', 'steps', 'sampler', 'scheduler', 'cfg_scale', 'model', 'width', 'height']

      keys.forEach(key => {
        if (this.imageMetadata[key] !== undefined && this.imageMetadata[key] !== null) {
          fields[key] = this.imageMetadata[key]
        }
      })

      return fields
    }
  },

  async mounted() {
    await this.loadSessions()
    this.setupLazyLoading()
    this.setupSessionObserver()
  },

  beforeUnmount() {
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect()
    }
    if (this.sessionObserver) {
      this.sessionObserver.disconnect()
    }
    // Nettoyer l'event listener clavier
    window.removeEventListener('keydown', this.handleKeyNavigation)
    // Nettoyer l'auto-refresh interval
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval)
    }
    // Nettoyer le polling des images
    this.stopImagePolling()
  },

  methods: {
    async loadSessions() {
      try {
        this.loadingSessions = true
        // Charger les sessions (sans metadata pour l'instant)
        const response = await ApiService.getSessions()

        // Transformer les sessions pour l'affichage
        this.sessions = response.sessions.map(session => ({
          name: session.name,
          displayName: this.formatSessionName(session.name),
          date: new Date(session.created_at),
          count: null,  // Sera chargé à la demande
          countLoading: false
        }))

        // Metadata will be lazy-loaded per session when visible
        // (handled by sessionObserver or on-demand)

        // Les counts seront chargés par le sessionObserver au scroll
      } catch (error) {
        console.error('Erreur lors du chargement des sessions:', error)
        this.$store.dispatch('showSnackbar', {
          message: 'Erreur lors du chargement des sessions',
          color: 'error'
        })
      } finally {
        this.loadingSessions = false
      }
    },

    setupSessionObserver() {
      // Intersection Observer pour lazy loading des session counts
      const options = {
        root: null, // viewport
        rootMargin: '50px', // Charger 50px avant que la session soit visible
        threshold: 0.1 // Déclencher dès que 10% de l'élément est visible
      }

      this.sessionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const sessionName = entry.target.dataset.sessionName
            const session = this.sessions.find(s => s.name === sessionName)

            if (session && session.count === null && !session.countLoading) {
              this.loadSessionCount(session)
            }
          }
        })
      }, options)

      // Attacher l'observer à tous les éléments de session
      this.$nextTick(() => {
        const sessionItems = this.$refs.sessionItems
        if (!sessionItems) return

        const items = Array.isArray(sessionItems) ? sessionItems : [sessionItems]
        items.forEach(item => {
          // Vuetify v-list-item a un $el
          const el = item.$el || item
          if (el && el instanceof Element) {
            this.sessionObserver.observe(el)
          }
        })
      })
    },

    async loadSessionCount(session) {
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
    },

    async loadSessionImages(sessionName) {
      try {
        this.loading = true
        const response = await ApiService.getSessionImages(sessionName)

        // Préparer les images pour affichage
        this.allImages = response.images.map((image) => ({
          id: image.path,
          name: image.filename,
          path: image.path,
          session: sessionName,
          url: null, // Chargé à la demande lors du clic dans la modal
          thumbnail: null, // Sera chargé via lazy loading
          thumbnailLoading: false,
          created: new Date(image.created_at)
        }))

        // Initialize lastImageIndex for polling (length - 1 because 0-indexed)
        this.lastImageIndex = this.allImages.length - 1
      } catch (error) {
        console.error(`Erreur chargement images session ${sessionName}:`, error)
        this.$store.dispatch('showSnackbar', {
          message: 'Erreur lors du chargement des images',
          color: 'error'
        })
      } finally {
        this.loading = false
      }
    },

    async loadSessionMetadata(sessionName) {
      try {
        const metadata = await ApiService.getSessionMetadata(sessionName)
        this.$set(this.sessionMetadata, sessionName, metadata)
      } catch (error) {
        // Metadata is optional, so don't show error if not found
        if (error.response?.status !== 404) {
          console.error(`Erreur chargement metadata ${sessionName}:`, error)
        }
      }
    },

    setupLazyLoading() {
      // Intersection Observer pour lazy loading des thumbnails
      const options = {
        root: null, // viewport
        rootMargin: '100px', // Charger 100px avant que l'image soit visible
        threshold: 0.01 // Déclencher dès que 1% de l'image est visible
      }

      this.intersectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const imgElement = entry.target
            const imagePath = imgElement.dataset.imagePath

            if (imagePath) {
              this.loadThumbnail(imagePath)
              // Arrêter d'observer cette image une fois chargée
              this.intersectionObserver.unobserve(imgElement)
            }
          }
        })
      }, options)
    },

    attachObservers() {
      // Attacher l'observer à tous les éléments imageRefs
      if (!this.intersectionObserver || !this.$refs.imageRefs) {
        return
      }

      const refs = Array.isArray(this.$refs.imageRefs)
        ? this.$refs.imageRefs
        : [this.$refs.imageRefs]

      refs.forEach(el => {
        if (el) {
          this.intersectionObserver.observe(el)
        }
      })
    },

    async loadThumbnail(imagePath) {
      const image = this.allImages.find(img => img.path === imagePath)
      if (!image || image.thumbnail || image.thumbnailLoading) {
        return // Déjà chargé ou en cours de chargement
      }

      image.thumbnailLoading = true
      try {
        image.thumbnail = await ApiService.getImageAsBlob(imagePath, true)
      } catch (error) {
        console.error(`Erreur chargement thumbnail ${imagePath}:`, error)
      } finally {
        image.thumbnailLoading = false
      }
    },

    async selectSession(sessionName) {
      // Stop polling for previous session
      this.stopImagePolling()

      this.selectedSession = sessionName
      this.allImages = []  // Clear images
      this.lastImageIndex = -1  // Reset polling index

      if (sessionName) {
        // Charger les images de cette session
        await this.loadSessionImages(sessionName)

        // Charger les métadonnées de la session si pas déjà chargées
        if (!this.sessionMetadata[sessionName]) {
          await this.loadSessionMetadata(sessionName)
        }

        // Charger tous les tags disponibles pour l'autocomplete
        await this.loadAllTags()

        // Start polling for new images every 5 seconds
        this.startImagePolling()
      }
    },

    startImagePolling() {
      // Clear any existing interval
      this.stopImagePolling()

      // Poll every 5 seconds
      this.imagePollingInterval = setInterval(() => {
        this.refreshCurrentSession()
      }, 5000)
    },

    stopImagePolling() {
      if (this.imagePollingInterval) {
        clearInterval(this.imagePollingInterval)
        this.imagePollingInterval = null
      }
    },

    async openImageDialog(image) {
      this.selectedImage = image
      this.imageDialog = true
      this.imageMetadata = null // Reset metadata
      this.sessionManifest = null // Reset manifest
      this.loadingMetadata = true
      this.loadingManifest = true

      // Charger l'image full size si pas déjà chargée
      if (!image.url) {
        try {
          image.url = await ApiService.getImageAsBlob(image.path, false)
        } catch (error) {
          console.error('Erreur chargement image:', error)
        }
      }

      // Charger les métadonnées ET le manifest EN PARALLÈLE
      await Promise.allSettled([
        // Load image metadata
        ApiService.getImageMetadata(image.path)
          .then(metadata => {
            this.imageMetadata = metadata
          })
          .catch(error => {
            console.error('Erreur lors du chargement des métadonnées:', error)
            this.$store.dispatch('showSnackbar', {
              message: 'Erreur lors du chargement des métadonnées',
              color: 'error'
            })
          })
          .finally(() => {
            this.loadingMetadata = false
          }),

        // Load session manifest
        ApiService.getSessionManifest(this.selectedSession)
          .then(manifest => {
            this.sessionManifest = manifest
          })
          .catch(error => {
            console.error('Erreur lors du chargement du manifest:', error)
            // Pas de snackbar pour manifest car c'est optionnel
          })
          .finally(() => {
            this.loadingManifest = false
          })
      ])
    },

    formatSessionName(sessionName) {
      // Support two formats:
      // Old: 2025-10-14_163854_hassaku_actualportrait.prompt
      // New: 20251014_163854-Hassaku-fantasy-default

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
    },

    formatDate(date) {
      return new Intl.DateTimeFormat('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date)
    },

    showPreviousImage() {
      if (this.hasPreviousImage) {
        const prevImage = this.allImages[this.currentImageIndex - 1]
        this.openImageDialog(prevImage)
      }
    },

    showNextImage() {
      if (this.hasNextImage) {
        const nextImage = this.allImages[this.currentImageIndex + 1]
        this.openImageDialog(nextImage)
      }
    },

    handleKeyNavigation(event) {
      // Navigation avec les flèches du clavier
      if (event.key === 'ArrowLeft') {
        this.showPreviousImage()
      } else if (event.key === 'ArrowRight') {
        this.showNextImage()
      } else if (event.key === 'Escape') {
        // Si fullscreen est ouvert, fermer seulement le fullscreen
        if (this.fullscreenOverlay) {
          this.closeFullscreen()
        } else {
          // Sinon, fermer la dialog
          this.imageDialog = false
        }
      }
    },

    openFullscreen() {
      this.fullscreenOverlay = true
    },

    closeFullscreen() {
      this.fullscreenOverlay = false
    },

    async handleMetadataUpdate({ sessionName, update }) {
      try {
        // Update metadata via API
        const metadata = await ApiService.updateSessionMetadata(sessionName, update)

        // Update local state
        this.$set(this.sessionMetadata, sessionName, metadata)

        this.$store.dispatch('showSnackbar', {
          message: 'Metadata mise à jour',
          color: 'success'
        })
      } catch (error) {
        console.error('Erreur mise à jour metadata:', error)
        this.$store.dispatch('showSnackbar', {
          message: 'Erreur lors de la mise à jour',
          color: 'error'
        })
      }
    },

    openNoteDialog(sessionName) {
      // TODO: Implémenter le dialog pour ajouter une note
      console.log('Open note dialog for', sessionName)
      this.$store.dispatch('showSnackbar', {
        message: 'Dialog notes - À implémenter',
        color: 'info'
      })
    },

    async loadAllTags() {
      // Collect all unique tags from all sessions
      const tagsSet = new Set()

      Object.values(this.sessionMetadata).forEach(metadata => {
        if (metadata && metadata.tags) {
          metadata.tags.forEach(tag => tagsSet.add(tag))
        }
      })

      this.allTags = Array.from(tagsSet).sort()
    },

    async handleTagsUpdate(newTags) {
      if (!this.selectedSession) return

      try {
        // Update metadata via API
        const metadata = await ApiService.updateSessionMetadata(
          this.selectedSession,
          { tags: newTags }
        )

        // Update local state (Vue 3 reactivity)
        this.sessionMetadata[this.selectedSession] = metadata

        this.$store.dispatch('showSnackbar', {
          message: 'Tags mis à jour',
          color: 'success'
        })
      } catch (error) {
        console.error('Erreur mise à jour tags:', error)
        this.$store.dispatch('showSnackbar', {
          message: 'Erreur lors de la mise à jour des tags',
          color: 'error'
        })
      }
    },

    toggleSortOrder() {
      this.sortDescending = !this.sortDescending
    },

    async refreshSessions() {
      try {
        // Refresh incrémental : récupérer toutes les sessions
        const response = await ApiService.getSessions()

        // Transformer les nouvelles sessions
        const allSessions = response.sessions.map(session => ({
          name: session.name,
          displayName: this.formatSessionName(session.name),
          date: new Date(session.created_at),
          count: null,
          countLoading: false
        }))

        // Trouver la session la plus récente actuelle
        const mostRecent = this.sessions.length > 0 ? this.sessions[0] : null

        if (mostRecent) {
          // Filtrer uniquement les nouvelles sessions (plus récentes que la plus récente actuelle)
          const newSessions = allSessions.filter(s => s.date > mostRecent.date)

          if (newSessions.length > 0) {
            // Ajouter les nouvelles sessions au début
            this.sessions.unshift(...newSessions)

            this.$store.dispatch('showSnackbar', {
              message: `${newSessions.length} nouvelle${newSessions.length > 1 ? 's' : ''} session${newSessions.length > 1 ? 's' : ''} détectée${newSessions.length > 1 ? 's' : ''}`,
              color: 'info'
            })
          }

          // Rafraîchir le count de la session la plus récente (peut-être en cours de génération)
          const updatedMostRecent = allSessions.find(s => s.name === mostRecent.name)
          if (updatedMostRecent) {
            await this.loadSessionCount(mostRecent)
          }
        } else {
          // Première fois : charger toutes les sessions
          this.sessions = allSessions
        }
      } catch (error) {
        console.error('Erreur lors du refresh des sessions:', error)
      }
    },

    async refreshCurrentSession() {
      if (!this.selectedSession) return

      try {
        // Polling mode: fetch only new images after lastImageIndex
        const response = await ApiService.getSessionImages(
          this.selectedSession,
          this.lastImageIndex
        )

        // If no new images, response.images will be empty
        if (response.images.length === 0) return

        // Transform new images
        const newImages = response.images.map((image) => ({
          id: image.path,
          name: image.filename,
          path: image.path,
          session: this.selectedSession,
          url: null,
          thumbnail: null,
          thumbnailLoading: false,
          created: new Date(image.created_at)
        }))

        // Append new images to the end (backend returns them sorted)
        this.allImages.push(...newImages)

        // Update lastImageIndex to new highest index
        this.lastImageIndex = this.allImages.length - 1

        this.$store.dispatch('showSnackbar', {
          message: `${newImages.length} nouvelle${newImages.length > 1 ? 's' : ''} image${newImages.length > 1 ? 's' : ''} détectée${newImages.length > 1 ? 's' : ''}`,
          color: 'info'
        })

        // Attach observers for lazy loading
        this.$nextTick(() => {
          this.attachObservers()
        })
      } catch (error) {
        console.error(`Erreur refresh images session ${this.selectedSession}:`, error)
      }
    },

    toggleAutoRefresh() {
      this.autoRefresh = !this.autoRefresh

      if (this.autoRefresh) {
        // Démarrer auto-refresh toutes les 60 secondes
        this.autoRefreshInterval = setInterval(() => {
          this.refreshSessions()
          if (this.selectedSession) {
            this.refreshCurrentSession()
          }
        }, 60000) // 1 minute

        this.$store.dispatch('showSnackbar', {
          message: 'Auto-refresh activé (1 minute)',
          color: 'info'
        })
      } else {
        // Arrêter auto-refresh
        if (this.autoRefreshInterval) {
          clearInterval(this.autoRefreshInterval)
          this.autoRefreshInterval = null
        }

        this.$store.dispatch('showSnackbar', {
          message: 'Auto-refresh désactivé',
          color: 'info'
        })
      }
    }
  }
}
</script>

<style scoped>
.border-r {
  border-right: 1px solid rgba(0, 0, 0, 0.12);
}

.cursor-pointer {
  cursor: pointer;
}

.image-card {
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.image-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
}

.session-item {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.session-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.lazy-image-container {
  width: 100%;
  min-height: 200px;
}

.position-relative {
  position: relative;
}

.nav-button {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
}

.nav-button-left {
  left: 10px;
}

.nav-button-right {
  right: 10px;
}

.nav-button:hover {
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4) !important;
}

/* Fullscreen overlay styles */
.fullscreen-overlay {
  background-color: rgba(0, 0, 0, 0.95) !important;
}

.fullscreen-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.fullscreen-image-wrapper {
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fullscreen-image {
  max-width: 100%;
  max-height: 90vh;
}

.fullscreen-trigger:hover {
  opacity: 0.9;
}

.fullscreen-close {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.fullscreen-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
}

.fullscreen-nav-left {
  left: 30px;
}

.fullscreen-nav-right {
  right: 30px;
}

.fullscreen-nav:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.6) !important;
}

.fullscreen-indicator {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}
</style>