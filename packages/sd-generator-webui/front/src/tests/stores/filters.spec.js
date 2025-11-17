import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFiltersStore } from '@/stores/filters'

describe('useFiltersStore', () => {
  beforeEach(() => {
    // Create fresh pinia instance for each test
    setActivePinia(createPinia())
  })

  describe('State initialization', () => {
    it('initializes with empty state', () => {
      const store = useFiltersStore()

      expect(store.filters).toEqual({})
      expect(store.availablePlaceholders).toEqual({})
      expect(store.allImages).toEqual([])
      expect(store.filteredImages).toEqual([])
      expect(store.isDrawerOpen).toBe(false)
      expect(store.loading).toBe(false)
    })
  })

  describe('loadImages', () => {
    it('loads images and extracts placeholders', () => {
      const store = useFiltersStore()
      const images = [
        {
          filename: 'image_001.png',
          seed: 1000,
          applied_variations: {
            HairColor: 'red',
            Expression: 'smiling'
          }
        },
        {
          filename: 'image_002.png',
          seed: 1001,
          applied_variations: {
            HairColor: 'blue',
            Expression: 'smiling'
          }
        },
        {
          filename: 'image_003.png',
          seed: 1000,
          applied_variations: {
            HairColor: 'red',
            Expression: 'angry'
          }
        }
      ]

      store.loadImages(images)

      expect(store.allImages).toHaveLength(3)
      expect(store.availablePlaceholders).toEqual({
        HairColor: ['blue', 'red'], // Sorted alphabetically
        Expression: ['angry', 'smiling'],
        Seed: [1000, 1001] // Sorted numerically
      })
    })

    it('handles images without applied_variations', () => {
      const store = useFiltersStore()
      const images = [
        { filename: 'image_001.png', seed: 1000 },
        { filename: 'image_002.png', seed: 1001 }
      ]

      store.loadImages(images)

      expect(store.availablePlaceholders).toEqual({
        Seed: [1000, 1001]
      })
    })

    it('sorts seed values numerically', () => {
      const store = useFiltersStore()
      const images = [
        { filename: 'img1.png', seed: 1005 },
        { filename: 'img2.png', seed: 1001 },
        { filename: 'img3.png', seed: 1003 }
      ]

      store.loadImages(images)

      expect(store.availablePlaceholders.Seed).toEqual([1001, 1003, 1005])
    })
  })

  describe('toggleFilter', () => {
    beforeEach(() => {
      const store = useFiltersStore()
      const images = [
        {
          filename: 'img1.png',
          seed: 1000,
          applied_variations: { HairColor: 'red', Expression: 'smiling' }
        },
        {
          filename: 'img2.png',
          seed: 1001,
          applied_variations: { HairColor: 'blue', Expression: 'smiling' }
        },
        {
          filename: 'img3.png',
          seed: 1002,
          applied_variations: { HairColor: 'red', Expression: 'angry' }
        }
      ]
      store.loadImages(images)
    })

    it('adds filter value when not present', () => {
      const store = useFiltersStore()

      store.toggleFilter('HairColor', 'red')

      expect(store.filters.HairColor).toEqual(['red'])
    })

    it('removes filter value when present', () => {
      const store = useFiltersStore()

      store.toggleFilter('HairColor', 'red')
      expect(store.filters.HairColor).toEqual(['red'])

      store.toggleFilter('HairColor', 'red')
      expect(store.filters.HairColor).toBeUndefined()
    })

    it('supports multiple values for same placeholder', () => {
      const store = useFiltersStore()

      store.toggleFilter('HairColor', 'red')
      store.toggleFilter('HairColor', 'blue')

      expect(store.filters.HairColor).toEqual(['red', 'blue'])
    })

    it('applies filters after toggle', () => {
      const store = useFiltersStore()

      store.toggleFilter('HairColor', 'red')

      // Should filter to images with red hair only
      expect(store.filteredImages).toHaveLength(2)
      expect(store.filteredImages[0].filename).toBe('img1.png')
      expect(store.filteredImages[1].filename).toBe('img3.png')
    })
  })

  describe('applyFilters', () => {
    beforeEach(() => {
      const store = useFiltersStore()
      const images = [
        {
          filename: 'img1.png',
          seed: 1000,
          applied_variations: { HairColor: 'red', Expression: 'smiling' }
        },
        {
          filename: 'img2.png',
          seed: 1001,
          applied_variations: { HairColor: 'blue', Expression: 'smiling' }
        },
        {
          filename: 'img3.png',
          seed: 1002,
          applied_variations: { HairColor: 'red', Expression: 'angry' }
        },
        {
          filename: 'img4.png',
          seed: 1003,
          applied_variations: { HairColor: 'green', Expression: 'neutral' }
        }
      ]
      store.loadImages(images)
    })

    it('shows all images when no filters active', () => {
      const store = useFiltersStore()

      store.applyFilters()

      expect(store.filteredImages).toHaveLength(4)
    })

    it('filters by single placeholder (Intra-placeholder OR)', () => {
      const store = useFiltersStore()

      store.filters = { HairColor: ['red', 'blue'] }
      store.applyFilters()

      // Should match red OR blue
      expect(store.filteredImages).toHaveLength(3)
      expect(store.filteredImages.map(i => i.filename)).toEqual([
        'img1.png',
        'img2.png',
        'img3.png'
      ])
    })

    it('filters by multiple placeholders (Inter-placeholder AND)', () => {
      const store = useFiltersStore()

      store.filters = {
        HairColor: ['red'],
        Expression: ['smiling']
      }
      store.applyFilters()

      // Should match (HairColor = red) AND (Expression = smiling)
      expect(store.filteredImages).toHaveLength(1)
      expect(store.filteredImages[0].filename).toBe('img1.png')
    })

    it('filters by seed', () => {
      const store = useFiltersStore()

      store.filters = { Seed: [1000, 1001] }
      store.applyFilters()

      expect(store.filteredImages).toHaveLength(2)
      expect(store.filteredImages.map(i => i.filename)).toEqual([
        'img1.png',
        'img2.png'
      ])
    })

    it('combines placeholder and seed filters', () => {
      const store = useFiltersStore()

      store.filters = {
        HairColor: ['red'],
        Seed: [1000]
      }
      store.applyFilters()

      // Should match (HairColor = red) AND (Seed = 1000)
      expect(store.filteredImages).toHaveLength(1)
      expect(store.filteredImages[0].filename).toBe('img1.png')
    })

    it('returns empty when no images match', () => {
      const store = useFiltersStore()

      store.filters = {
        HairColor: ['red'],
        Expression: ['neutral'] // No red+neutral combo
      }
      store.applyFilters()

      expect(store.filteredImages).toHaveLength(0)
    })
  })

  describe('isSelected', () => {
    it('returns true when value is selected', () => {
      const store = useFiltersStore()

      store.filters = { HairColor: ['red', 'blue'] }

      expect(store.isSelected('HairColor', 'red')).toBe(true)
      expect(store.isSelected('HairColor', 'blue')).toBe(true)
    })

    it('returns false when value is not selected', () => {
      const store = useFiltersStore()

      store.filters = { HairColor: ['red'] }

      expect(store.isSelected('HairColor', 'blue')).toBe(false)
    })

    it('returns false when placeholder has no filters', () => {
      const store = useFiltersStore()

      expect(store.isSelected('HairColor', 'red')).toBe(false)
    })
  })

  describe('clearFilters', () => {
    it('removes all filters and shows all images', () => {
      const store = useFiltersStore()
      const images = [
        { filename: 'img1.png', seed: 1000, applied_variations: { HairColor: 'red' } },
        { filename: 'img2.png', seed: 1001, applied_variations: { HairColor: 'blue' } }
      ]
      store.loadImages(images)

      store.toggleFilter('HairColor', 'red')
      expect(store.filteredImages).toHaveLength(1)

      store.clearFilters()

      expect(store.filters).toEqual({})
      expect(store.filteredImages).toHaveLength(2)
    })
  })

  describe('URL sync', () => {
    beforeEach(() => {
      // Mock window.location and history
      delete window.location
      window.location = new URL('http://localhost/session/test')
      window.history.replaceState = vi.fn()
    })

    it('syncToURL encodes filters in URL', () => {
      const store = useFiltersStore()

      store.filters = {
        HairColor: ['red', 'blue'],
        Expression: ['smiling']
      }
      store.syncToURL()

      const callArgs = window.history.replaceState.mock.calls[0]
      const url = callArgs[2]

      // Check that URL contains encoded filters
      expect(url).toContain('HairColor=red')
      expect(url).toContain('Expression=smiling')
    })

    it('syncToURL clears URL when no filters', () => {
      const store = useFiltersStore()

      store.filters = {}
      store.syncToURL()

      expect(window.history.replaceState).toHaveBeenCalledWith(
        {},
        '',
        '/session/test'
      )
    })

    it('syncFromURL restores filters from URL', () => {
      const store = useFiltersStore()
      const images = [
        { filename: 'img1.png', seed: 1000, applied_variations: { HairColor: 'red', Expression: 'smiling' } },
        { filename: 'img2.png', seed: 1001, applied_variations: { HairColor: 'blue', Expression: 'angry' } }
      ]
      store.loadImages(images)

      window.location.search = '?HairColor=red,blue&Expression=smiling&Seed=1000'
      store.syncFromURL()

      expect(store.filters).toEqual({
        HairColor: ['red', 'blue'],
        Expression: ['smiling'],
        Seed: [1000] // Parsed as number
      })
    })
  })

  describe('Getters', () => {
    it('hasActiveFilters returns true when filters exist', () => {
      const store = useFiltersStore()

      store.filters = { HairColor: ['red'] }

      expect(store.hasActiveFilters).toBe(true)
    })

    it('hasActiveFilters returns false when no filters', () => {
      const store = useFiltersStore()

      expect(store.hasActiveFilters).toBe(false)
    })

    it('filteredCount returns count of filtered images', () => {
      const store = useFiltersStore()
      const images = [
        { filename: 'img1.png', seed: 1000, applied_variations: { HairColor: 'red' } },
        { filename: 'img2.png', seed: 1001, applied_variations: { HairColor: 'blue' } }
      ]
      store.loadImages(images)

      store.toggleFilter('HairColor', 'red')

      expect(store.filteredCount).toBe(1)
    })

    it('filterStats returns formatted string', () => {
      const store = useFiltersStore()
      const images = [
        { filename: 'img1.png', seed: 1000, applied_variations: { HairColor: 'red' } },
        { filename: 'img2.png', seed: 1001, applied_variations: { HairColor: 'blue' } }
      ]
      store.loadImages(images)

      store.toggleFilter('HairColor', 'red')

      expect(store.filterStats).toBe('Showing: 1 / 2 images')
    })
  })

  describe('Drawer state', () => {
    it('toggleDrawer switches drawer state', () => {
      const store = useFiltersStore()

      expect(store.isDrawerOpen).toBe(false)

      store.toggleDrawer()
      expect(store.isDrawerOpen).toBe(true)

      store.toggleDrawer()
      expect(store.isDrawerOpen).toBe(false)
    })

    it('openDrawer sets drawer to open', () => {
      const store = useFiltersStore()

      store.openDrawer()
      expect(store.isDrawerOpen).toBe(true)
    })

    it('closeDrawer sets drawer to closed', () => {
      const store = useFiltersStore()

      store.isDrawerOpen = true
      store.closeDrawer()
      expect(store.isDrawerOpen).toBe(false)
    })
  })
})
