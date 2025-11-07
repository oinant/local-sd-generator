<template>
  <v-container fluid>
    <!-- Back button and session header -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-btn
                icon="mdi-arrow-left"
                variant="text"
                :to="{ name: 'Sessions' }"
              ></v-btn>
              <span class="ml-2">{{ formatSessionName(sessionName) }}</span>
            </div>

            <v-btn color="primary" variant="text" :loading="loading" @click="refreshSession">
              <v-icon>mdi-refresh</v-icon>
              Refresh
            </v-btn>
          </v-card-title>

          <!-- Error state -->
          <v-alert v-if="error" type="error" variant="tonal" closable @click:close="error = null">
            {{ error }}
          </v-alert>

          <!-- Loading state -->
          <v-progress-linear v-if="loading" indeterminate color="primary"></v-progress-linear>

          <v-card-text v-if="!loading && stats">
            <!-- Quick actions -->
            <div class="mb-4">
              <v-btn color="primary" :to="`/sessions/${sessionName}/images`" class="mr-2">
                <v-icon start>mdi-image-multiple</v-icon>
                View Images
              </v-btn>
              <v-btn color="secondary" :to="`/sessions/${sessionName}/rating`">
                <v-icon start>mdi-star</v-icon>
                Rate Variations
              </v-btn>
            </div>

            <v-row>
              <!-- Left column: Stats overview -->
              <v-col cols="12" md="6">
                <v-card variant="outlined">
                  <v-card-title class="text-h6">
                    <v-icon class="mr-2">mdi-chart-box</v-icon>
                    Statistics Overview
                  </v-card-title>

                  <v-card-text>
                    <!-- Model info -->
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">SD Model</div>
                      <v-chip color="primary" variant="tonal" size="small">
                        <v-icon start size="small">mdi-brain</v-icon>
                        {{ stats.sd_model }}
                      </v-chip>
                    </div>

                    <!-- Seed sweep badge -->
                    <div v-if="stats.is_seed_sweep" class="mb-3">
                      <div class="text-caption text-medium-emphasis">Generation Type</div>
                      <v-chip color="purple" variant="tonal" size="small">
                        <v-icon start size="small">mdi-shuffle-variant</v-icon>
                        Seed Sweep
                      </v-chip>
                      <div class="text-caption mt-1">
                        Seeds {{ stats.seed_min }} - {{ stats.seed_max }}
                      </div>
                    </div>

                    <!-- Images count -->
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">Images</div>
                      <div class="d-flex align-center">
                        <v-icon size="small" class="mr-1">mdi-image-multiple</v-icon>
                        <span class="text-h6">
                          {{ stats.images_actual }} / {{ stats.images_requested }}
                        </span>
                      </div>
                    </div>

                    <!-- Completion percentage -->
                    <div class="mb-3">
                      <div class="d-flex justify-space-between align-center mb-1">
                        <span class="text-caption text-medium-emphasis">Completion</span>
                        <span class="text-h6 font-weight-bold">
                          {{ Math.round(stats.completion_percent * 100) }}%
                        </span>
                      </div>
                      <v-progress-linear
                        :model-value="stats.completion_percent * 100"
                        :color="getCompletionColor(stats.completion_percent)"
                        height="10"
                        rounded
                      ></v-progress-linear>
                    </div>

                    <!-- Placeholders info -->
                    <div v-if="stats.placeholders_count > 0" class="mb-3">
                      <div class="text-caption text-medium-emphasis">Variations</div>
                      <div>
                        <v-icon size="small">mdi-variable</v-icon>
                        {{ stats.placeholders_count }} placeholders
                      </div>
                      <div class="text-caption">
                        {{ stats.variations_theoretical }} theoretical combinations
                      </div>
                    </div>

                    <!-- Timestamps -->
                    <div class="mb-3">
                      <div class="text-caption text-medium-emphasis">Created</div>
                      <div class="text-body-2">{{ formatDate(stats.created_at) }}</div>
                    </div>

                    <div v-if="stats.completed_at" class="mb-3">
                      <div class="text-caption text-medium-emphasis">Completed</div>
                      <div class="text-body-2">{{ formatDate(stats.completed_at) }}</div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>

              <!-- Right column: Manifest data -->
              <v-col cols="12" md="6">
                <v-card variant="outlined">
                  <v-card-title class="text-h6">
                    <v-icon class="mr-2">mdi-file-document</v-icon>
                    Manifest
                  </v-card-title>

                  <v-card-text>
                    <v-expansion-panels variant="accordion">
                      <!-- Template info -->
                      <v-expansion-panel v-if="manifest">
                        <v-expansion-panel-title>
                          <v-icon class="mr-2">mdi-code-braces</v-icon>
                          Template Configuration
                        </v-expansion-panel-title>
                        <v-expansion-panel-text>
                          <div class="mb-2">
                            <div class="text-caption text-medium-emphasis">Template File</div>
                            <div class="text-body-2 font-mono">{{ manifest.template_file }}</div>
                          </div>

                          <div v-if="manifest.generation_mode" class="mb-2">
                            <div class="text-caption text-medium-emphasis">Generation Mode</div>
                            <div class="text-body-2">{{ manifest.generation_mode }}</div>
                          </div>

                          <div v-if="manifest.seed_mode" class="mb-2">
                            <div class="text-caption text-medium-emphasis">Seed Mode</div>
                            <div class="text-body-2">{{ manifest.seed_mode }}</div>
                          </div>

                          <div v-if="manifest.base_seed !== undefined" class="mb-2">
                            <div class="text-caption text-medium-emphasis">Base Seed</div>
                            <div class="text-body-2">{{ manifest.base_seed }}</div>
                          </div>
                        </v-expansion-panel-text>
                      </v-expansion-panel>

                      <!-- Placeholders -->
                      <v-expansion-panel v-if="manifest && manifest.placeholders">
                        <v-expansion-panel-title>
                          <v-icon class="mr-2">mdi-variable</v-icon>
                          Placeholders ({{ Object.keys(manifest.placeholders).length }})
                        </v-expansion-panel-title>
                        <v-expansion-panel-text>
                          <div
                            v-for="(values, placeholder) in manifest.placeholders"
                            :key="placeholder"
                            class="mb-3"
                          >
                            <div class="text-caption text-medium-emphasis">{{ placeholder }}</div>
                            <v-chip
                              v-for="(value, key) in values"
                              :key="key"
                              size="small"
                              class="mr-1 mb-1"
                            >
                              {{ key }}: {{ truncate(value, 30) }}
                            </v-chip>
                          </div>
                        </v-expansion-panel-text>
                      </v-expansion-panel>

                      <!-- Parameters -->
                      <v-expansion-panel v-if="manifest && manifest.parameters">
                        <v-expansion-panel-title>
                          <v-icon class="mr-2">mdi-cog</v-icon>
                          Generation Parameters
                        </v-expansion-panel-title>
                        <v-expansion-panel-text>
                          <div class="font-mono text-body-2">
                            <pre>{{ JSON.stringify(manifest.parameters, null, 2) }}</pre>
                          </div>
                        </v-expansion-panel-text>
                      </v-expansion-panel>

                      <!-- Raw manifest -->
                      <v-expansion-panel v-if="manifest">
                        <v-expansion-panel-title>
                          <v-icon class="mr-2">mdi-code-json</v-icon>
                          Raw Manifest JSON
                        </v-expansion-panel-title>
                        <v-expansion-panel-text>
                          <div class="font-mono text-body-2">
                            <pre>{{ JSON.stringify(manifest, null, 2) }}</pre>
                          </div>
                        </v-expansion-panel-text>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SessionDetailView',

  data() {
    return {
      stats: null,
      manifest: null,
      loading: false,
      error: null
    }
  },

  computed: {
    sessionName() {
      return this.$route.params.name
    }
  },

  mounted() {
    this.loadSessionData()
  },

  methods: {
    async loadSessionData() {
      this.loading = true
      this.error = null

      try {
        // Load stats
        const statsResponse = await axios.get(`/api/sessions/${this.sessionName}/stats`)
        this.stats = statsResponse.data

        // Load manifest
        const manifestResponse = await axios.get(`/api/sessions/${this.sessionName}/manifest`)
        this.manifest = manifestResponse.data
      } catch (err) {
        console.error('Failed to load session data:', err)
        this.error = err.response?.data?.detail || 'Failed to load session data'
      } finally {
        this.loading = false
      }
    },

    async refreshSession() {
      await this.loadSessionData()
    },

    formatSessionName(name) {
      // Remove date prefix: "20251014_173320-name" -> "name"
      const match = name.match(/^\d{8}_\d{6}-?(.+)$/)
      return match ? match[1] : name
    },

    formatDate(dateString) {
      if (!dateString) return ''
      return new Date(dateString).toLocaleString()
    },

    getCompletionColor(percent) {
      if (percent >= 0.95) return 'success'
      if (percent >= 0.7) return 'warning'
      return 'error'
    },

    truncate(str, maxLen) {
      if (!str) return ''
      const text = String(str)
      return text.length > maxLen ? text.substring(0, maxLen) + '...' : text
    }
  }
}
</script>

<style scoped>
.font-mono {
  font-family: 'Courier New', monospace;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
}
</style>
