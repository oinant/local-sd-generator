<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon class="mr-2">mdi-folder-multiple</v-icon>
              Sessions
              <v-chip v-if="sessions.length > 0" class="ml-3" size="small">
                {{ sessions.length }} sessions
              </v-chip>
            </div>

            <v-btn color="primary" variant="text" :loading="loading" @click="refreshSessions">
              <v-icon>mdi-refresh</v-icon>
              Refresh
            </v-btn>
          </v-card-title>

          <v-card-text>
            <!-- Loading state -->
            <v-progress-linear
              v-if="loading && sessions.length === 0"
              indeterminate
              color="primary"
            ></v-progress-linear>

            <!-- Error state -->
            <v-alert v-if="error" type="error" variant="tonal" closable @click:close="error = null">
              {{ error }}
            </v-alert>

            <!-- Sessions list -->
            <v-row v-if="sessions.length > 0">
              <v-col v-for="session in sessions" :key="session.name" cols="12" md="6" lg="4">
                <v-card class="session-card" :to="`/sessions/${session.name}`" hover>
                  <v-card-title class="text-h6">
                    {{ formatSessionName(session.name) }}
                  </v-card-title>

                  <v-card-subtitle class="text-caption">
                    {{ formatDate(session.created_at) }}
                  </v-card-subtitle>

                  <v-card-text>
                    <!-- Stats section -->
                    <div v-if="session.stats" class="stats-section">
                      <!-- Model info -->
                      <div v-if="session.stats.sd_model" class="mb-2">
                        <v-chip size="small" color="primary" variant="tonal">
                          <v-icon start size="small">mdi-brain</v-icon>
                          {{ session.stats.sd_model }}
                        </v-chip>
                      </div>

                      <!-- Seed-sweep badge -->
                      <div v-if="session.stats.is_seed_sweep" class="mb-2">
                        <v-chip size="small" color="purple" variant="tonal">
                          <v-icon start size="small">mdi-shuffle-variant</v-icon>
                          Seed Sweep
                        </v-chip>
                        <span class="text-caption ml-2">
                          Seeds {{ session.stats.seed_min }}-{{ session.stats.seed_max }}
                        </span>
                      </div>

                      <!-- Images count -->
                      <div class="d-flex align-center mb-2">
                        <v-icon size="small" class="mr-1">mdi-image-multiple</v-icon>
                        <span class="text-body-2">
                          {{ session.stats.images_actual }} /
                          {{ session.stats.images_requested }} images
                        </span>
                      </div>

                      <!-- Completion progress -->
                      <div class="mb-2">
                        <div class="d-flex justify-space-between align-center mb-1">
                          <span class="text-caption">Completion</span>
                          <span class="text-caption font-weight-bold">
                            {{ Math.round(session.stats.completion_percent * 100) }}%
                          </span>
                        </div>
                        <v-progress-linear
                          :model-value="session.stats.completion_percent * 100"
                          :color="getCompletionColor(session.stats.completion_percent)"
                          height="6"
                          rounded
                        ></v-progress-linear>
                      </div>

                      <!-- Placeholders info -->
                      <div
                        v-if="session.stats.placeholders_count > 0"
                        class="text-caption text-medium-emphasis"
                      >
                        <v-icon size="small">mdi-variable</v-icon>
                        {{ session.stats.placeholders_count }} placeholders ({{
                          session.stats.variations_theoretical
                        }}
                        combinations)
                      </div>
                    </div>

                    <!-- Loading stats -->
                    <div v-else-if="loadingStats[session.name]" class="text-center py-4">
                      <v-progress-circular
                        indeterminate
                        size="24"
                        width="2"
                        color="primary"
                      ></v-progress-circular>
                      <div class="text-caption mt-2">Loading stats...</div>
                    </div>

                    <!-- Stats not loaded yet -->
                    <div v-else>
                      <v-btn
                        size="small"
                        variant="text"
                        @click.prevent="loadSessionStats(session.name)"
                      >
                        <v-icon start>mdi-chart-bar</v-icon>
                        Load stats
                      </v-btn>
                    </div>

                    <!-- Metadata (tags, favorite) -->
                    <div v-if="session.metadata" class="mt-3">
                      <v-chip
                        v-if="session.metadata.is_favorite"
                        size="x-small"
                        color="yellow"
                        variant="tonal"
                        class="mr-1"
                      >
                        <v-icon start size="x-small">mdi-star</v-icon>
                        Favorite
                      </v-chip>

                      <v-chip
                        v-if="session.metadata.is_test"
                        size="x-small"
                        color="orange"
                        variant="tonal"
                        class="mr-1"
                      >
                        <v-icon start size="x-small">mdi-test-tube</v-icon>
                        Test
                      </v-chip>

                      <v-chip
                        v-for="tag in session.metadata.tags"
                        :key="tag"
                        size="x-small"
                        variant="outlined"
                        class="mr-1"
                      >
                        {{ tag }}
                      </v-chip>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Empty state -->
            <v-alert v-else-if="!loading" type="info" variant="tonal">
              No sessions found. Generate some images to create sessions!
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'SessionsView',

  data() {
    return {
      sessions: [],
      loading: false,
      loadingStats: {}, // Track which sessions are loading stats
      error: null
    }
  },

  mounted() {
    this.loadSessions()
  },

  methods: {
    async loadSessions() {
      this.loading = true
      this.error = null

      try {
        const response = await api.getSessions()
        this.sessions = response.sessions

        // Attach empty stats/metadata objects for reactivity
        this.sessions.forEach(session => {
          if (!session.stats) {
            session.stats = null
          }
          if (!session.metadata) {
            session.metadata = null
          }
        })
      } catch (err) {
        console.error('Failed to load sessions:', err)
        this.error = err.response?.data?.detail || 'Failed to load sessions'
      } finally {
        this.loading = false
      }
    },

    async loadSessionStats(sessionName) {
      // Mark as loading
      this.$set(this.loadingStats, sessionName, true)

      try {
        const stats = await api.getSessionStats(sessionName)

        // Find session and attach stats
        const session = this.sessions.find(s => s.name === sessionName)
        if (session) {
          this.$set(session, 'stats', stats)
        }
      } catch (err) {
        console.error(`Failed to load stats for ${sessionName}:`, err)
        // Don't show error, just silently fail (stats are optional)
      } finally {
        this.$delete(this.loadingStats, sessionName)
      }
    },

    async refreshSessions() {
      await this.loadSessions()
    },

    formatSessionName(name) {
      // Remove date prefix for display (e.g., "20251014_173320-name" -> "name")
      const match = name.match(/^\d{8}_\d{6}-?(.+)$/)
      return match ? match[1] : name
    },

    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    },

    getCompletionColor(percent) {
      if (percent >= 0.95) return 'success'
      if (percent >= 0.7) return 'warning'
      return 'error'
    }
  }
}
</script>

<style scoped>
.session-card {
  transition: all 0.2s ease;
}

.session-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stats-section {
  border-left: 3px solid rgba(var(--v-theme-primary), 0.3);
  padding-left: 12px;
}
</style>
