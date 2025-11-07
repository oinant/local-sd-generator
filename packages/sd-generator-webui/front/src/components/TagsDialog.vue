<template>
  <v-dialog v-model="show" max-width="500">
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between pb-2">
        <span>
          <v-icon class="mr-2">mdi-tag-multiple</v-icon>
          Gérer les tags
        </span>
        <v-btn icon variant="text" size="small" @click="close">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider />

      <v-card-text class="pt-4">
        <!-- Current tags -->
        <div v-if="currentTags.length > 0" class="mb-4">
          <div class="text-caption font-weight-bold mb-2">Tags actuels :</div>
          <div class="d-flex flex-wrap gap-2">
            <v-chip
              v-for="tag in currentTags"
              :key="tag"
              size="small"
              closable
              color="primary"
              variant="tonal"
              @click:close="removeTag(tag)"
            >
              {{ tag }}
            </v-chip>
          </div>
        </div>
        <div v-else class="mb-4 text-caption text-grey">Aucun tag pour cette session</div>

        <v-divider class="my-3" />

        <!-- Add new tag -->
        <div>
          <div class="text-caption font-weight-bold mb-2">Ajouter un tag :</div>
          <v-combobox
            v-model="newTag"
            :items="suggestedTags"
            label="Nouveau tag"
            density="compact"
            variant="outlined"
            clearable
            hide-details
            @keydown.enter="addTag"
          >
            <template #append>
              <v-btn
                icon
                size="small"
                variant="text"
                :disabled="!newTag || newTag.trim() === ''"
                @click="addTag"
              >
                <v-icon>mdi-plus</v-icon>
              </v-btn>
            </template>
          </v-combobox>
          <div class="text-caption text-grey mt-1">
            Appuyez sur Entrée ou cliquez sur + pour ajouter
          </div>
        </div>
      </v-card-text>

      <v-divider />

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close"> Fermer </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'TagsDialog',

  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    sessionName: {
      type: String,
      required: true
    },
    tags: {
      type: Array,
      default: () => []
    },
    allTags: {
      type: Array,
      default: () => []
    }
  },

  emits: ['update:modelValue', 'update:tags'],

  data() {
    return {
      newTag: null,
      currentTags: [...this.tags]
    }
  },

  computed: {
    show: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    },

    suggestedTags() {
      // Suggérer les tags existants qui ne sont pas déjà utilisés
      return this.allTags.filter(tag => !this.currentTags.includes(tag))
    }
  },

  watch: {
    tags: {
      handler(newTags) {
        this.currentTags = [...newTags]
      },
      deep: true
    }
  },

  methods: {
    addTag() {
      if (!this.newTag || this.newTag.trim() === '') return

      const tag = this.newTag.trim().toLowerCase()

      if (!this.currentTags.includes(tag)) {
        this.currentTags.push(tag)
        this.emitUpdate()
      }

      this.newTag = null
    },

    removeTag(tag) {
      const index = this.currentTags.indexOf(tag)
      if (index > -1) {
        this.currentTags.splice(index, 1)
        this.emitUpdate()
      }
    },

    emitUpdate() {
      this.$emit('update:tags', [...this.currentTags])
    },

    close() {
      this.show = false
    }
  }
}
</script>

<style scoped>
.gap-2 {
  gap: 8px;
}
</style>
