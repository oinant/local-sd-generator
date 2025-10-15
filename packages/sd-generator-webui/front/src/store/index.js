import { createStore } from 'vuex'
import ApiService from '@/services/api'

export default createStore({
  state: {
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    images: [],
    imagesTotal: 0,
    currentPage: 1,
    pageSize: 20,
    generations: {},
    snackbar: {
      show: false,
      message: '',
      color: 'info'
    }
  },

  getters: {
    isAuthenticated: (state) => state.isAuthenticated,
    user: (state) => state.user,
    canGenerate: (state) => state.user?.can_generate || false,
    images: (state) => state.images,
    loading: (state) => state.loading,
    error: (state) => state.error,
    snackbar: (state) => state.snackbar
  },

  mutations: {
    SET_LOADING(state, loading) {
      state.loading = loading
    },

    SET_ERROR(state, error) {
      state.error = error
    },

    SET_USER(state, user) {
      state.user = user
      state.isAuthenticated = !!user
    },

    SET_IMAGES(state, { images, total, page }) {
      state.images = images
      state.imagesTotal = total
      state.currentPage = page
    },

    ADD_GENERATION(state, generation) {
      state.generations[generation.job_id] = generation
    },

    UPDATE_GENERATION(state, generation) {
      if (state.generations[generation.job_id]) {
        state.generations[generation.job_id] = generation
      }
    },

    SHOW_SNACKBAR(state, { message, color = 'info' }) {
      state.snackbar = {
        show: true,
        message,
        color
      }
    },

    HIDE_SNACKBAR(state) {
      state.snackbar.show = false
    }
  },

  actions: {
    async login({ commit }, token) {
      try {
        commit('SET_LOADING', true)
        ApiService.setToken(token)

        const user = await ApiService.getCurrentUser()
        commit('SET_USER', user)
        commit('SHOW_SNACKBAR', { message: 'Connexion réussie', color: 'success' })

        return true
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Erreur de connexion')
        commit('SHOW_SNACKBAR', { message: 'Token invalide', color: 'error' })
        return false
      } finally {
        commit('SET_LOADING', false)
      }
    },

    logout({ commit }) {
      ApiService.clearAuth()
      commit('SET_USER', null)
      commit('SHOW_SNACKBAR', { message: 'Déconnexion réussie', color: 'info' })
    },

    async loadImages({ commit }, { page = 1, session = null } = {}) {
      try {
        commit('SET_LOADING', true)
        const data = await ApiService.getImages(page, 20, session)
        commit('SET_IMAGES', {
          images: data.images,
          total: data.total_count,
          page: data.page
        })
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Erreur lors du chargement des images')
        commit('SHOW_SNACKBAR', { message: 'Erreur lors du chargement des images', color: 'error' })
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async createGeneration({ commit }, request) {
      try {
        commit('SET_LOADING', true)
        const response = await ApiService.createGeneration(request)
        commit('ADD_GENERATION', {
          job_id: response.job_id,
          status: response.status,
          request: request,
          created_at: new Date().toISOString()
        })
        commit('SHOW_SNACKBAR', { message: 'Génération lancée avec succès', color: 'success' })
        return response.job_id
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Erreur lors de la création de la génération')
        commit('SHOW_SNACKBAR', { message: 'Erreur lors de la génération', color: 'error' })
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async updateGenerationStatus({ commit }, jobId) {
      try {
        const generation = await ApiService.getGenerationStatus(jobId)
        commit('UPDATE_GENERATION', generation)
        return generation
      } catch (error) {
        console.error('Error updating generation status:', error)
      }
    },

    showSnackbar({ commit }, payload) {
      commit('SHOW_SNACKBAR', payload)
    },

    hideSnackbar({ commit }) {
      commit('HIDE_SNACKBAR')
    }
  },

  modules: {
  }
})