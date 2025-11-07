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

            <!-- Metadata section (Feature 5: Editable Metadata) -->
            <v-row class="mt-4">
              <v-col cols="12">
                <v-card variant="outlined">
                  <v-card-title class="text-h6">
                    <v-icon class="mr-2">mdi-tag-multiple</v-icon>
                    Session Metadata
                  </v-card-title>

                  <v-card-text>
                    <!-- Flags -->
                    <div class="mb-4">
                      <div class="text-caption text-medium-emphasis mb-2">Flags</div>
                      <v-chip-group>
                        <v-chip
                          :color="metadata?.is_favorite ? 'yellow' : 'grey'"
                          :variant="metadata?.is_favorite ? 'flat' : 'outlined'"
                          @click="toggleFlag('is_favorite')"
                          class="cursor-pointer"
                        >
                          <v-icon start>mdi-star</v-icon>
                          Favorite
                        </v-chip>

                        <v-chip
                          :color="metadata?.is_test ? 'orange' : 'grey'"
                          :variant="metadata?.is_test ? 'flat' : 'outlined'"
                          @click="toggleFlag('is_test')"
                          class="cursor-pointer"
                        >
                          <v-icon start>mdi-test-tube</v-icon>
                          Test
                        </v-chip>

                        <v-chip
                          :color="metadata?.is_complete ? 'green' : 'grey'"
                          :variant="metadata?.is_complete ? 'flat' : 'outlined'"
                          @click="toggleFlag('is_complete')"
                          class="cursor-pointer"
                        >
                          <v-icon start>mdi-check-circle</v-icon>
                          Complete
                        </v-chip>
                      </v-chip-group>
                    </div>

                    <!-- Rating -->
                    <div class="mb-4">
                      <div class="text-caption text-medium-emphasis mb-2">Rating</div>
                      <v-chip-group>
                        <v-chip
                          :color="metadata?.user_rating === 'like' ? 'success' : 'grey'"
                          :variant="metadata?.user_rating === 'like' ? 'flat' : 'outlined'"
                          @click="setRating('like')"
                          class="cursor-pointer"
                        >
                          <v-icon start>mdi-thumb-up</v-icon>
                          Like
                        </v-chip>

                        <v-chip
                          :color="metadata?.user_rating === 'dislike' ? 'error' : 'grey'"
                          :variant="metadata?.user_rating === 'dislike' ? 'flat' : 'outlined'"
                          @click="setRating('dislike')"
                          class="cursor-pointer"
                        >
                          <v-icon start>mdi-thumb-down</v-icon>
                          Dislike
                        </v-chip>

                        <v-chip
                          v-if="metadata?.user_rating"
                          color="grey"
                          variant="outlined"
                          @click="setRating(null)"
                          class="cursor-pointer"
                        >
                          <v-icon start>mdi-close</v-icon>
                          Clear
                        </v-chip>
                      </v-chip-group>
                    </div>

                    <!-- Tags -->
                    <div class="mb-4">
                      <div class="text-caption text-medium-emphasis mb-2">Tags</div>
                      <div class="d-flex flex-wrap align-center">
                        <v-chip
                          v-for="tag in metadata?.tags || []"
                          :key="tag"
                          size="small"
                          closable
                          @click:close="removeTag(tag)"
                          class="mr-1 mb-1"
                        >
                          {{ tag }}
                        </v-chip>

                        <!-- Add tag input -->
                        <v-chip
                          v-if="!showTagInput"
                          size="small"
                          variant="outlined"
                          @click="showTagInput = true"
                          class="cursor-pointer"
                        >
                          <v-icon start>mdi-plus</v-icon>
                          Add tag
                        </v-chip>

                        <v-text-field
                          v-if="showTagInput"
                          v-model="newTag"
                          density="compact"
                          variant="outlined"
                          placeholder="Enter tag name"
                          hide-details
                          @keyup.enter="addTag"
                          @blur="cancelAddTag"
                          class="ml-2"
                          style="max-width: 200px"
                        >
                          <template #append-inner>
                            <v-icon @click="addTag" class="cursor-pointer">mdi-check</v-icon>
                          </template>
                        </v-text-field>
                      </div>
                    </div>

                    <!-- User notes -->
                    <div>
                      <div class="text-caption text-medium-emphasis mb-2">Notes</div>
                      <v-textarea
                        v-model="metadata.user_notes"
                        variant="outlined"
                        placeholder="Add your notes about this session..."
                        rows="3"
                        @blur="saveMetadata"
                        hide-details
                      ></v-textarea>
                    </div>

                    <!-- Save indicator -->
                    <v-alert
                      v-if="savingMetadata"
                      type="info"
                      variant="tonal"
                      density="compact"
                      class="mt-2"
                    >
                      <v-icon start>mdi-content-save</v-icon>
                      Saving...
                    </v-alert>

                    <v-alert
                      v-if="metadataSaved"
                      type="success"
                      variant="tonal"
                      density="compact"
                      class="mt-2"
                    >
                      <v-icon start>mdi-check</v-icon>
                      Saved successfully
                    </v-alert>
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
import api from '@/services/api'

export default {
  name: 'SessionDetailView',

  data() {
    return {
      stats: null,
      manifest: null,
      metadata: null,
      loading: false,
      error: null,
      showTagInput: false,
      newTag: '',
      savingMetadata: false,
      metadataSaved: false
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
        this.stats = await api.getSessionStats(this.sessionName)

        // Load manifest
        this.manifest = await api.getSessionManifest(this.sessionName)

        // Load metadata
        try {
          this.metadata = await api.getSessionMetadata(this.sessionName)
        } catch (err) {
          // Metadata might not exist yet, initialize default
          this.metadata = {
            is_favorite: false,
            is_test: false,
            is_complete: false,
            user_rating: null,
            tags: [],
            user_notes: ''
          }
        }
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

    async saveMetadata() {
      this.savingMetadata = true
      this.metadataSaved = false

      try {
        await api.updateSessionMetadata(this.sessionName, this.metadata)
        this.metadataSaved = true

        // Hide success message after 2 seconds
        setTimeout(() => {
          this.metadataSaved = false
        }, 2000)
      } catch (err) {
        console.error('Failed to save metadata:', err)
        this.error = err.response?.data?.detail || 'Failed to save metadata'
      } finally {
        this.savingMetadata = false
      }
    },

    async toggleFlag(flagName) {
      if (!this.metadata) return
      this.metadata[flagName] = !this.metadata[flagName]
      await this.saveMetadata()
    },

    async setRating(rating) {
      if (!this.metadata) return
      this.metadata.user_rating = rating
      await this.saveMetadata()
    },

    async addTag() {
      if (!this.newTag.trim()) return
      if (!this.metadata) return

      if (!this.metadata.tags) {
        this.metadata.tags = []
      }

      // Avoid duplicates
      if (!this.metadata.tags.includes(this.newTag.trim())) {
        this.metadata.tags.push(this.newTag.trim())
        await this.saveMetadata()
      }

      this.newTag = ''
      this.showTagInput = false
    },

    cancelAddTag() {
      // Delay to allow click on check icon
      setTimeout(() => {
        this.newTag = ''
        this.showTagInput = false
      }, 200)
    },

    async removeTag(tag) {
      if (!this.metadata || !this.metadata.tags) return

      const index = this.metadata.tags.indexOf(tag)
      if (index !== -1) {
        this.metadata.tags.splice(index, 1)
        await this.saveMetadata()
      }
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

.cursor-pointer {
  cursor: pointer;
}
</style>
