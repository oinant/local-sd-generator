import { defineStore } from 'pinia'
import ApiService from '@/services/api'
import { useNotificationStore } from './notification'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null
  }),

  getters: {
    canGenerate: state => state.user?.can_generate || false
  },

  actions: {
    async login(token) {
      const notifications = useNotificationStore()

      try {
        this.loading = true
        ApiService.setToken(token)

        const user = await ApiService.getCurrentUser()
        this.user = user
        this.isAuthenticated = !!user
        notifications.show({ message: 'Connexion réussie', color: 'success' })

        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Erreur de connexion'
        notifications.show({ message: 'Token invalide', color: 'error' })
        return false
      } finally {
        this.loading = false
      }
    },

    logout() {
      const notifications = useNotificationStore()

      ApiService.clearAuth()
      this.user = null
      this.isAuthenticated = false
      notifications.show({ message: 'Déconnexion réussie', color: 'info' })
    }
  }
})
