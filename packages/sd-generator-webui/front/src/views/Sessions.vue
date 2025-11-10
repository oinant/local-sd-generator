<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon class="mr-2">mdi-folder-multiple</v-icon>
              Sessions
              <v-chip v-if="totalCount > 0" class="ml-3" size="small">
                {{ totalCount }} total
              </v-chip>
              <v-chip v-if="totalPages > 1" class="ml-2" size="small" variant="outlined">
                Page {{ page }} / {{ totalPages }}
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
            <!-- Sessions grid -->
            <v-row v-if="sessions.length > 0" justify="center">
              <v-col v-for="session in sessions" :key="session.name" cols="12" sm="12" md="6" lg="4" xl="3">
                <v-card class="session-card" :to="`/sessions/${session.name}`" hover>
                  <v-card-title class="text-h6">
                    {{ formatSessionName(session.name) }}
                  </v-card-title>

                  <v-card-subtitle class="text-caption d-flex justify-space-between align-center">
                    <span>{{ formatDate(session.created_at) }}</span>

                    <!-- Status badge -->
                    <v-chip
                      v-if="session.is_finished !== null"
                      :color="session.is_finished ? 'success' : 'warning'"
                      size="small"
                      variant="tonal"
                    >
                      <v-icon start size="small">
                        {{ session.is_finished ? 'mdi-check-circle' : 'mdi-clock-outline' }}
                      </v-icon>
                      {{ session.is_finished ? 'Finished' : 'In Progress' }}
                    </v-chip>
                  </v-card-subtitle>

                  <v-card-text>
                    <!-- Stats section (from API - no lazy loading) -->
                    <div v-if="session.images_requested || session.images_actual" class="stats-section">
                      <!-- Images count -->
                      <div class="d-flex align-center mb-2">
                        <v-icon size="small" class="mr-1">mdi-image-multiple</v-icon>
                        <span class="text-body-2">
                          {{ session.images_actual || 0 }} / {{ session.images_requested || 0 }} images
                        </span>

                        <!-- Complete badge -->
                        <v-chip
                          v-if="session.completion_percent !== null && session.completion_percent >= 0.95"
                          size="x-small"
                          color="success"
                          variant="tonal"
                          class="ml-2"
                        >
                          <v-icon start size="x-small">mdi-check</v-icon>
                          Complete
                        </v-chip>
                      </div>

                      <!-- Completion progress -->
                      <div v-if="session.completion_percent !== null" class="mb-2">
                        <div class="d-flex justify-space-between align-center mb-1">
                          <span class="text-caption">Progress</span>
                          <span class="text-caption font-weight-bold">
                            {{ Math.round(session.completion_percent * 100) }}%
                          </span>
                        </div>
                        <v-progress-linear
                          :model-value="session.completion_percent * 100"
                          :color="getCompletionColor(session.completion_percent)"
                          height="6"
                          rounded
                        ></v-progress-linear>
                      </div>
                    </div>

                    <!-- No stats available -->
                    <div v-else class="text-caption text-medium-emphasis">
                      <v-icon size="small">mdi-information-outline</v-icon>
                      No statistics available
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

            <!-- Pagination -->
            <div v-if="totalPages > 1" class="d-flex justify-center mt-6">
              <v-pagination
                v-model="page"
                :length="totalPages"
                :total-visible="7"
                @update:model-value="onPageChange"
              ></v-pagination>
            </div>

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
      error: null,
      // Pagination
      page: 1,
      pageSize: 50,
      totalCount: 0,
      totalPages: 0
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
        const response = await api.getSessions(this.page, this.pageSize)
        this.sessions = response.sessions
        this.totalCount = response.total_count
        this.totalPages = response.total_pages
        // Stats are now included in the response (no lazy loading needed)
      } catch (err) {
        console.error('Failed to load sessions:', err)
        this.error = err.response?.data?.detail || 'Failed to load sessions'
      } finally {
        this.loading = false
      }
    },

    onPageChange(newPage) {
      this.page = newPage
      this.loadSessions()
      // Scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' })
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
  max-width: 550px;
  margin: 0 auto;
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
