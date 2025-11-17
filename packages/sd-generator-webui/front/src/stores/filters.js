import { defineStore } from 'pinia'

/**
 * Filters Store - Manages gallery filtering state
 *
 * Supports filtering images by placeholder values with:
 * - Intra-placeholder OR logic (HairColor = red OR blue)
 * - Inter-placeholder AND logic ((HairColor = red OR blue) AND Expression = smiling)
 * - URL sync for sharing/bookmarking
 * - Smart thumbnail batching for filtered results
 */
export const useFiltersStore = defineStore('filters', {
  state: () => ({
    // Active filters: { PlaceholderName: [value1, value2, ...] }
    filters: {},

    // Available placeholders and their possible values
    // { PlaceholderName: [value1, value2, value3, ...] }
    availablePlaceholders: {},

    // All images from current session (unfiltered)
    allImages: [],

    // Filtered images (computed from allImages + filters)
    filteredImages: [],

    // UI state
    isDrawerOpen: false,

    // Loading state
    loading: false
  }),

  getters: {
    /**
     * Check if any filters are active
     */
    hasActiveFilters: (state) => {
      return Object.values(state.filters).some(values => values.length > 0)
    },

    /**
     * Count of filtered images
     */
    filteredCount: (state) => {
      return state.filteredImages.length
    },

    /**
     * Count of total images
     */
    totalCount: (state) => {
      return state.allImages.length
    },

    /**
     * Get filter stats for display
     * Returns: "Showing: X / Y images"
     */
    filterStats: (state) => {
      const filtered = state.filteredImages.length
      const total = state.allImages.length
      return `Showing: ${filtered.toLocaleString()} / ${total.toLocaleString()} images`
    }
  },

  actions: {
    /**
     * Load images for a session and extract available placeholders
     * @param {Array} images - Array of image objects with applied_variations
     */
    loadImages(images) {
      this.allImages = images
      this.extractAvailablePlaceholders()
      this.applyFilters() // Apply existing filters to new images
    },

    /**
     * Extract available placeholders from all images
     * Builds availablePlaceholders object
     */
    extractAvailablePlaceholders() {
      const placeholders = {}

      // Scan all images for unique placeholder values
      this.allImages.forEach(image => {
        if (!image.applied_variations) return

        Object.entries(image.applied_variations).forEach(([placeholder, value]) => {
          if (!placeholders[placeholder]) {
            placeholders[placeholder] = new Set()
          }
          placeholders[placeholder].add(value)
        })
      })

      // Add seed as special placeholder
      if (this.allImages.length > 0) {
        placeholders.Seed = new Set()
        this.allImages.forEach(image => {
          if (image.seed !== undefined) {
            placeholders.Seed.add(image.seed)
          }
        })
      }

      // Convert Sets to sorted arrays
      this.availablePlaceholders = Object.fromEntries(
        Object.entries(placeholders).map(([key, valueSet]) => {
          const values = Array.from(valueSet)
          // Sort numerically for Seed, alphabetically for others
          if (key === 'Seed') {
            values.sort((a, b) => a - b)
          } else {
            values.sort()
          }
          return [key, values]
        })
      )
    },

    /**
     * Toggle a filter value for a placeholder
     * @param {string} placeholder - Placeholder name
     * @param {string|number} value - Value to toggle
     */
    toggleFilter(placeholder, value) {
      if (!this.filters[placeholder]) {
        this.filters[placeholder] = []
      }

      const index = this.filters[placeholder].indexOf(value)
      if (index === -1) {
        // Add value
        this.filters[placeholder].push(value)
      } else {
        // Remove value
        this.filters[placeholder].splice(index, 1)
      }

      // Clean up empty arrays
      if (this.filters[placeholder].length === 0) {
        delete this.filters[placeholder]
      }

      this.applyFilters()
      this.syncToURL()
    },

    /**
     * Check if a specific value is selected for a placeholder
     * @param {string} placeholder - Placeholder name
     * @param {string|number} value - Value to check
     * @returns {boolean}
     */
    isSelected(placeholder, value) {
      return this.filters[placeholder]?.includes(value) || false
    },

    /**
     * Clear all filters
     */
    clearFilters() {
      this.filters = {}
      this.applyFilters()
      this.syncToURL()
    },

    /**
     * Apply current filters to allImages and update filteredImages
     *
     * Filter logic:
     * - Intra-placeholder: OR (any selected value matches)
     * - Inter-placeholder: AND (all placeholders must match)
     */
    applyFilters() {
      // If no filters, show all images
      if (!this.hasActiveFilters) {
        this.filteredImages = [...this.allImages]
        return
      }

      this.filteredImages = this.allImages.filter(image => {
        // For each placeholder filter
        for (const [placeholder, selectedValues] of Object.entries(this.filters)) {
          if (selectedValues.length === 0) continue // No filter

          // Get image value for this placeholder
          let imageValue
          if (placeholder === 'Seed') {
            imageValue = image.seed
          } else {
            imageValue = image.applied_variations?.[placeholder]
          }

          // OR logic within placeholder: must match at least one selected value
          if (!selectedValues.includes(imageValue)) {
            return false // AND logic: must match ALL placeholders
          }
        }

        return true
      })
    },

    /**
     * Sync current filters to URL query params
     * Format: ?HairColor=red,blue&Expression=smiling&Seed=1000,1001
     */
    syncToURL() {
      const params = new URLSearchParams()

      Object.entries(this.filters).forEach(([placeholder, values]) => {
        if (values.length > 0) {
          params.set(placeholder, values.join(','))
        }
      })

      // Update URL without reloading page
      const newURL = params.toString()
        ? `${window.location.pathname}?${params.toString()}`
        : window.location.pathname

      window.history.replaceState({}, '', newURL)
    },

    /**
     * Sync filters from URL query params
     * Call this on page load to restore filters from URL
     */
    syncFromURL() {
      const params = new URLSearchParams(window.location.search)
      const filters = {}

      params.forEach((value, key) => {
        // Parse comma-separated values
        const values = value.split(',').map(v => {
          // Try to parse as number (for Seed)
          const num = Number(v)
          return isNaN(num) ? v : num
        })
        filters[key] = values
      })

      this.filters = filters
      this.applyFilters()
    },

    /**
     * Copy current filter URL to clipboard
     */
    async copyFilterURL() {
      const url = window.location.href
      try {
        await navigator.clipboard.writeText(url)
        return true
      } catch (error) {
        console.error('Failed to copy URL:', error)
        return false
      }
    },

    /**
     * Toggle drawer open/closed
     */
    toggleDrawer() {
      this.isDrawerOpen = !this.isDrawerOpen
    },

    /**
     * Open drawer
     */
    openDrawer() {
      this.isDrawerOpen = true
    },

    /**
     * Close drawer
     */
    closeDrawer() {
      this.isDrawerOpen = false
    }
  }
})
