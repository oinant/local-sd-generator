import { defineStore } from 'pinia'
import ApiService from '@/services/api'
import { useNotificationStore } from './notification'

export const useGenerationsStore = defineStore('generations', {
  state: () => ({
    generations: {},
    loading: false,
    error: null
  }),

  actions: {
    async createGeneration(request) {
      const notifications = useNotificationStore()

      try {
        this.loading = true
        const response = await ApiService.createGeneration(request)
        this.generations[response.job_id] = {
          job_id: response.job_id,
          status: response.status,
          request: request,
          created_at: new Date().toISOString()
        }
        notifications.show({ message: 'Génération lancée avec succès', color: 'success' })
        return response.job_id
      } catch (error) {
        this.error = error.response?.data?.detail || 'Erreur lors de la création de la génération'
        notifications.show({ message: 'Erreur lors de la génération', color: 'error' })
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateGenerationStatus(jobId) {
      try {
        const generation = await ApiService.getGenerationStatus(jobId)
        if (this.generations[jobId]) {
          this.generations[jobId] = generation
        }
        return generation
      } catch (error) {
        console.error('Error updating generation status:', error)
      }
    }
  }
})
