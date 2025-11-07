<template>
  <v-card flat>
    <v-card-title class="d-flex align-center justify-space-between pb-2">
      <span>
        <v-icon class="mr-2">mdi-filter-variant</v-icon>
        Filtres
      </span>
      <v-btn v-if="hasActiveFilters" size="small" variant="text" @click="clearFilters">
        Réinitialiser
      </v-btn>
    </v-card-title>

    <v-divider />

    <v-card-text>
      <!-- Rating filter -->
      <div class="mb-3">
        <div class="text-caption font-weight-bold mb-2">Notation</div>
        <v-chip-group v-model="localFilters.rating" selected-class="text-primary" column>
          <v-chip value="all" size="small" variant="outlined">
            <v-icon start>mdi-all-inclusive</v-icon>
            Toutes
          </v-chip>
          <v-chip value="like" size="small" variant="outlined" color="success">
            <v-icon start>mdi-thumb-up</v-icon>
            Aimées
          </v-chip>
          <v-chip value="dislike" size="small" variant="outlined" color="error">
            <v-icon start>mdi-thumb-down</v-icon>
            Non aimées
          </v-chip>
          <v-chip value="unrated" size="small" variant="outlined">
            <v-icon start>mdi-help</v-icon>
            Non notées
          </v-chip>
        </v-chip-group>
      </div>

      <v-divider class="my-3" />

      <!-- Flags filter -->
      <div class="mb-3">
        <div class="text-caption font-weight-bold mb-2">Statut</div>
        <v-chip-group v-model="localFilters.flags" selected-class="text-primary" multiple column>
          <v-chip value="favorite" size="small" variant="outlined" color="amber">
            <v-icon start>mdi-star</v-icon>
            Favoris
          </v-chip>
          <v-chip value="test" size="small" variant="outlined" color="warning">
            <v-icon start>mdi-flask</v-icon>
            Tests
          </v-chip>
          <v-chip value="complete" size="small" variant="outlined" color="success">
            <v-icon start>mdi-check-circle</v-icon>
            Complètes
          </v-chip>
        </v-chip-group>
      </div>

      <v-divider class="my-3" />

      <!-- Image count filter -->
      <div class="mb-3">
        <div class="text-caption font-weight-bold mb-2">
          Nombre d'images ({{ localFilters.minImages }} - {{ localFilters.maxImages }})
        </div>
        <v-range-slider
          v-model="imageCountRange"
          :min="0"
          :max="maxImageCount"
          :step="1"
          thumb-label
          density="compact"
        />
      </div>

      <v-divider class="my-3" />

      <!-- Date range filter -->
      <div class="mb-3">
        <div class="text-caption font-weight-bold mb-2">Période</div>
        <v-chip-group v-model="localFilters.dateRange" selected-class="text-primary" column>
          <v-chip value="all" size="small" variant="outlined">
            <v-icon start>mdi-calendar</v-icon>
            Toutes
          </v-chip>
          <v-chip value="today" size="small" variant="outlined">
            <v-icon start>mdi-calendar-today</v-icon>
            Aujourd'hui
          </v-chip>
          <v-chip value="week" size="small" variant="outlined">
            <v-icon start>mdi-calendar-week</v-icon>
            7 derniers jours
          </v-chip>
          <v-chip value="month" size="small" variant="outlined">
            <v-icon start>mdi-calendar-month</v-icon>
            30 derniers jours
          </v-chip>
          <v-chip value="custom" size="small" variant="outlined">
            <v-icon start>mdi-calendar-range</v-icon>
            Personnalisé
          </v-chip>
        </v-chip-group>

        <!-- Custom date range picker -->
        <v-expand-transition>
          <div v-if="localFilters.dateRange === 'custom'" class="mt-3">
            <v-row dense>
              <v-col cols="12">
                <v-text-field
                  v-model="localFilters.dateStart"
                  type="date"
                  label="Date début"
                  density="compact"
                  variant="outlined"
                  prepend-inner-icon="mdi-calendar-start"
                  hide-details
                />
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="localFilters.dateEnd"
                  type="date"
                  label="Date fin"
                  density="compact"
                  variant="outlined"
                  prepend-inner-icon="mdi-calendar-end"
                  hide-details
                />
              </v-col>
            </v-row>
          </div>
        </v-expand-transition>
      </div>

      <v-divider class="my-3" />

      <!-- Search -->
      <div class="mb-3">
        <v-text-field
          v-model="localFilters.search"
          density="compact"
          placeholder="Rechercher..."
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          clearable
          hide-details
        />
      </div>
    </v-card-text>

    <v-divider />

    <v-card-actions>
      <v-spacer />
      <v-btn color="primary" variant="elevated" @click="applyFilters"> Appliquer </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
export default {
  name: 'SessionFilters',

  props: {
    filters: {
      type: Object,
      default: () => ({
        rating: 'all',
        flags: [],
        minImages: 0,
        maxImages: 1000,
        dateRange: 'all',
        dateStart: null,
        dateEnd: null,
        search: ''
      })
    },
    maxImageCount: {
      type: Number,
      default: 1000
    }
  },

  emits: ['update:filters'],

  data() {
    return {
      localFilters: { ...this.filters }
    }
  },

  computed: {
    imageCountRange: {
      get() {
        return [this.localFilters.minImages, this.localFilters.maxImages]
      },
      set(value) {
        this.localFilters.minImages = value[0]
        this.localFilters.maxImages = value[1]
      }
    },

    hasActiveFilters() {
      return (
        this.localFilters.rating !== 'all' ||
        this.localFilters.flags.length > 0 ||
        this.localFilters.minImages > 0 ||
        this.localFilters.maxImages < this.maxImageCount ||
        this.localFilters.dateRange !== 'all' ||
        this.localFilters.dateStart !== null ||
        this.localFilters.dateEnd !== null ||
        this.localFilters.search !== ''
      )
    }
  },

  watch: {
    filters: {
      handler(newVal) {
        this.localFilters = { ...newVal }
      },
      deep: true
    }
  },

  methods: {
    applyFilters() {
      this.$emit('update:filters', { ...this.localFilters })
    },

    clearFilters() {
      this.localFilters = {
        rating: 'all',
        flags: [],
        minImages: 0,
        maxImages: this.maxImageCount,
        dateRange: 'all',
        dateStart: null,
        dateEnd: null,
        search: ''
      }
      this.applyFilters()
    }
  }
}
</script>

<style scoped>
/* Optional custom styles */
</style>
