import axios from 'axios'

class ApiService {
  constructor() {
    this.baseURL = process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : ''
    this.token = localStorage.getItem('authToken') || ''

    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      }
    })

    // Intercepteur pour ajouter le token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Intercepteur pour gérer les erreurs d'auth
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearAuth()
        }
        return Promise.reject(error)
      }
    )
  }

  setToken(token) {
    this.token = token
    localStorage.setItem('authToken', token)
  }

  clearAuth() {
    this.token = ''
    localStorage.removeItem('authToken')
  }

  // Auth endpoints
  async validateAuth() {
    const response = await this.client.get('/api/auth/validate')
    return response.data
  }

  async getCurrentUser() {
    const response = await this.client.get('/api/auth/me')
    return response.data
  }

  // Sessions endpoints
  async getSessions() {
    const response = await this.client.get('/api/sessions/')
    return response.data
  }

  async getSessionCount(sessionName) {
    const response = await this.client.get(`/api/sessions/${sessionName}/count`)
    return response.data
  }

  async getSessionImages(sessionName) {
    const response = await this.client.get(`/api/sessions/${sessionName}/images`)
    return response.data
  }

  // Images endpoints
  async getImages(page = 1, pageSize = 20, session = null) {
    const params = { page, page_size: pageSize }
    if (session) params.session = session

    const response = await this.client.get('/api/images/', { params })
    return response.data
  }

  async getImageUrl(filename, thumbnail = false) {
    const params = thumbnail ? '?thumbnail=true' : ''
    return `${this.baseURL}/api/images/${filename}${params}`
  }

  async getImageAsBlob(filename, thumbnail = false) {
    const params = { thumbnail }
    const response = await this.client.get(`/api/images/${filename}`, {
      params,
      responseType: 'blob'
    })
    // Convertir le blob en data URL pour l'afficher
    return URL.createObjectURL(response.data)
  }

  async getImageMetadata(filename) {
    const response = await this.client.get(`/api/images/${filename}/metadata`)
    return response.data
  }

  // Generation endpoints
  async createGeneration(request) {
    const response = await this.client.post('/api/generation/', request)
    return response.data
  }

  async getGenerationStatus(jobId) {
    const response = await this.client.get(`/api/generation/${jobId}`)
    return response.data
  }

  async getGenerations() {
    const response = await this.client.get('/api/generation/')
    return response.data
  }

  // Files endpoints
  async getFileTree(path = null) {
    console.log('[ApiService] getFileTree called with path:', path)
    const params = path ? { path } : {}
    console.log('[ApiService] Request params:', params)
    const response = await this.client.get('/api/files/tree', { params })
    console.log('[ApiService] Response:', response.data)
    return response.data
  }

  async getFileImages(path = null) {
    const params = path ? { path } : {}
    const response = await this.client.get('/api/files/images', { params })
    return response.data
  }

  // Warm cache: fire-and-forget request to preload file tree
  warmFileTreeCache() {
    console.log('[ApiService] Warming file tree cache...')
    // Fire-and-forget: on ne attend pas la réponse
    this.client.get('/api/files/tree').catch(() => {
      // Ignore les erreurs, c'est juste pour warmer le cache
    })
  }

  getFileImageUrl(filePath) {
    return `${this.baseURL}/api/files/serve/${filePath}`
  }
}

export default new ApiService()