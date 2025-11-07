import { defineStore } from 'pinia'
import ApiService from '@/services/api'
import { useNotificationStore } from './notification'

export const useImagesStore = defineStore('images', {
  state: () => ({
    images: [],
    imagesTotal: 0,
    currentPage: 1,
    pageSize: 20,
    loading: false,
    error: null
  }),

  actions: {
    async loadImages({ page = 1, session = null } = {}) {
      const notifications = useNotificationStore()

      try {
        this.loading = true
        const data = await ApiService.getImages(page, 20, session)
        this.images = data.images
        this.imagesTotal = data.total_count
        this.currentPage = data.page
      } catch (error) {
        this.error = error.response?.data?.detail || 'Erreur lors du chargement des images'
        notifications.show({ message: 'Erreur lors du chargement des images', color: 'error' })
      } finally {
        this.loading = false
      }
    }
  }
})
