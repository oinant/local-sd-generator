<template>
  <v-list-item
    :active="isSelected"
    @click="$emit('select', session.name)"
    class="session-card"
    :title="session.name"
  >
    <!-- Session icon -->
    <template v-slot:prepend>
      <v-icon :color="getSessionColor()">{{ getSessionIcon() }}</v-icon>
    </template>

    <!-- Session name and date -->
    <v-list-item-title class="text-caption">
      {{ displayName }}
    </v-list-item-title>
    <v-list-item-subtitle class="text-caption">
      {{ formatDate(session.date) }}
    </v-list-item-subtitle>

    <!-- Actions and metadata -->
    <template v-slot:append>
      <div class="d-flex align-center gap-1">
        <!-- Image count badge -->
        <v-progress-circular
          v-if="session.countLoading"
          indeterminate
          size="20"
          width="2"
        />
        <v-chip
          v-else-if="session.count !== null"
          size="x-small"
          :color="getCountColor()"
        >
          {{ session.count }}
        </v-chip>
        <v-chip
          v-else
          size="x-small"
          color="grey"
          variant="outlined"
        >
          ?
        </v-chip>

        <!-- Rating buttons (show on hover or when metadata exists) -->
        <div
          v-if="showActions"
          class="rating-actions"
          @click.stop
        >
          <!-- Favorite star -->
          <v-btn
            icon
            size="x-small"
            variant="text"
            @click="toggleFavorite"
            :color="metadata?.is_favorite ? 'amber' : 'grey'"
          >
            <v-icon size="small">
              {{ metadata?.is_favorite ? 'mdi-star' : 'mdi-star-outline' }}
            </v-icon>
          </v-btn>

          <!-- Like button -->
          <v-btn
            icon
            size="x-small"
            variant="text"
            @click="setRating('like')"
            :color="metadata?.user_rating === 'like' ? 'success' : 'grey'"
          >
            <v-icon size="small">mdi-thumb-up</v-icon>
          </v-btn>

          <!-- Dislike button -->
          <v-btn
            icon
            size="x-small"
            variant="text"
            @click="setRating('dislike')"
            :color="metadata?.user_rating === 'dislike' ? 'error' : 'grey'"
          >
            <v-icon size="small">mdi-thumb-down</v-icon>
          </v-btn>

          <!-- More actions menu -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                icon
                size="x-small"
                variant="text"
                v-bind="props"
              >
                <v-icon size="small">mdi-dots-vertical</v-icon>
              </v-btn>
            </template>

            <v-list density="compact">
              <!-- Test flag -->
              <v-list-item @click="toggleTest">
                <template v-slot:prepend>
                  <v-icon :color="metadata?.is_test ? 'warning' : ''">
                    {{ metadata?.is_test ? 'mdi-flask' : 'mdi-flask-outline' }}
                  </v-icon>
                </template>
                <v-list-item-title>
                  {{ metadata?.is_test ? 'Marquer comme production' : 'Marquer comme test' }}
                </v-list-item-title>
              </v-list-item>

              <!-- Add note -->
              <v-list-item @click="$emit('add-note', session.name)">
                <template v-slot:prepend>
                  <v-icon>mdi-note-text-outline</v-icon>
                </template>
                <v-list-item-title>Ajouter une note</v-list-item-title>
              </v-list-item>

              <!-- Add tags -->
              <v-list-item @click="$emit('add-tags', session.name)">
                <template v-slot:prepend>
                  <v-icon>mdi-tag-multiple-outline</v-icon>
                </template>
                <v-list-item-title>Ajouter des tags</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
      </div>
    </template>
  </v-list-item>
</template>

<script>
export default {
  name: 'SessionCard',

  props: {
    session: {
      type: Object,
      required: true
    },
    isSelected: {
      type: Boolean,
      default: false
    },
    metadata: {
      type: Object,
      default: null
    }
  },

  emits: ['select', 'update-metadata', 'add-note', 'add-tags'],

  data() {
    return {
      showActions: false
    }
  },

  computed: {
    displayName() {
      // Format: 2025-10-14_163854_hassaku_actualportrait.prompt
      // Include date prefix for easier scanning
      const parts = this.session.name.split('_')
      if (parts.length >= 3) {
        const date = parts[0] // YYYY-MM-DD
        const name = parts.slice(2).join('_').replace('.prompt', '')
        return `${date} · ${name}`
      }
      return this.session.name
    }
  },

  methods: {
    formatDate(date) {
      return new Intl.DateTimeFormat('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date)
    },

    getSessionIcon() {
      if (this.metadata?.is_favorite) return 'mdi-folder-star'
      if (this.metadata?.is_test) return 'mdi-folder-cog'
      if (this.metadata?.user_rating === 'like') return 'mdi-folder-check'
      if (this.metadata?.user_rating === 'dislike') return 'mdi-folder-remove'
      return 'mdi-folder'
    },

    getSessionColor() {
      if (this.metadata?.is_favorite) return 'amber'
      if (this.metadata?.user_rating === 'like') return 'success'
      if (this.metadata?.user_rating === 'dislike') return 'error'
      if (this.metadata?.is_test) return 'warning'
      return undefined
    },

    getCountColor() {
      if (this.session.count === 0) return 'error'
      if (this.session.count < 10) return 'warning'
      return 'info'
    },

    async toggleFavorite() {
      const newValue = !(this.metadata?.is_favorite ?? false)
      await this.updateMetadata({ is_favorite: newValue })
    },

    async setRating(rating) {
      // Toggle off if already set
      const newRating = this.metadata?.user_rating === rating ? null : rating
      await this.updateMetadata({ user_rating: newRating })
    },

    async toggleTest() {
      const newValue = !(this.metadata?.is_test ?? false)
      await this.updateMetadata({ is_test: newValue })
    },

    async updateMetadata(update) {
      this.$emit('update-metadata', {
        sessionName: this.session.name,
        update
      })
    }
  }
}
</script>

<style scoped>
.session-card {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.session-card:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.session-card:hover .rating-actions {
  opacity: 1;
}

.rating-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
  display: flex;
  align-items: center;
  gap: 2px;
}

/* Always show actions if metadata exists */
.session-card:has(.v-btn[color="amber"]) .rating-actions,
.session-card:has(.v-btn[color="success"]) .rating-actions,
.session-card:has(.v-btn[color="error"]) .rating-actions {
  opacity: 1;
}
</style>
