<template>
  <v-navigation-drawer
    v-model="filtersStore.isDrawerOpen"
    location="right"
    temporary
    width="400"
    class="filter-drawer"
  >
    <!-- Header -->
    <v-toolbar density="compact" color="primary">
      <v-toolbar-title>
        <v-icon icon="mdi-filter-variant" class="mr-2" />
        Filters
      </v-toolbar-title>
      <v-spacer />
      <v-btn
        v-if="filtersStore.hasActiveFilters"
        icon="mdi-close"
        variant="text"
        @click="filtersStore.clearFilters"
      >
        <v-icon>mdi-filter-off</v-icon>
        <v-tooltip activator="parent" location="bottom">Clear</v-tooltip>
      </v-btn>
      <v-btn icon="mdi-close" variant="text" @click="filtersStore.closeDrawer">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-toolbar>

    <v-divider />

    <!-- Filter Stats -->
    <v-card-text class="pa-3 bg-grey-lighten-5">
      <div class="text-body-2 text-center">
        {{ filtersStore.filterStats }}
      </div>
    </v-card-text>

    <v-divider />

    <!-- Empty state when no placeholders -->
    <v-card-text v-if="Object.keys(filtersStore.availablePlaceholders).length === 0" class="text-center text-grey">
      <v-icon size="64" color="grey-lighten-1">mdi-filter-off-outline</v-icon>
      <p class="mt-4">No placeholders available</p>
      <p class="text-caption">Load a session to see filters</p>
    </v-card-text>

    <!-- Filters list -->
    <v-list v-else class="py-0">
      <div
        v-for="(values, placeholder) in filtersStore.availablePlaceholders"
        :key="placeholder"
        class="filter-group"
      >
        <v-list-subheader class="text-uppercase font-weight-bold">
          {{ placeholder }}
          <span class="text-grey text-caption ml-2">
            ({{ values.length }} {{ values.length === 1 ? 'variant' : 'variants' }})
          </span>
        </v-list-subheader>

        <v-list-item class="px-4">
          <div class="filter-values">
            <label
              v-for="value in values"
              :key="value"
              class="filter-checkbox d-inline-block mr-4 mb-2"
            >
              <input
                type="checkbox"
                :checked="filtersStore.isSelected(placeholder, value)"
                @change="filtersStore.toggleFilter(placeholder, value)"
                class="mr-2"
              />
              <span>{{ value }}</span>
            </label>
          </div>
        </v-list-item>

        <v-divider />
      </div>
    </v-list>

    <!-- Footer actions -->
    <template v-if="Object.keys(filtersStore.availablePlaceholders).length > 0" #append>
      <v-divider />
      <v-card-actions class="pa-3">
        <v-btn
          prepend-icon="mdi-content-copy"
          variant="outlined"
          color="primary"
          block
          @click="copyFilterURL"
        >
          Copy Filter
        </v-btn>
      </v-card-actions>
    </template>
  </v-navigation-drawer>
</template>

<script setup>
import { useFiltersStore } from '@/stores/filters'
import { useNotificationStore } from '@/stores/notification'

const filtersStore = useFiltersStore()
const notification = useNotificationStore()

/**
 * Copy current filter URL to clipboard
 */
async function copyFilterURL() {
  const success = await filtersStore.copyFilterURL()

  if (success) {
    notification.show({
      message: 'Filter URL copied to clipboard',
      color: 'success'
    })
  } else {
    notification.show({
      message: 'Failed to copy URL',
      color: 'error'
    })
  }
}
</script>

<style scoped>
.filter-drawer {
  /* Custom styles if needed */
}

.filter-group {
  /* Group styles */
}

.filter-values {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-checkbox {
  cursor: pointer;
  user-select: none;
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.filter-checkbox:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.filter-checkbox input[type="checkbox"] {
  cursor: pointer;
}

.filter-checkbox span {
  font-size: 0.875rem;
}
</style>
