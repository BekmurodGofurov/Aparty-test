import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import { useCacheStore } from '../store/cacheStore'
import {
  generateCacheKey,
  isCacheable,
  getCachedData,
  setCachedData,
} from './cacheService'

// All requests go through the API gateway (see docker-compose.yml, port 8080).
const DEFAULT_GATEWAY_URL = 'http://localhost:8080'
const backendUrl = import.meta.env.VITE_BACKEND_API || DEFAULT_GATEWAY_URL

const normalizedBackendUrl = backendUrl.replace(/\/+$/, '')
const apiBaseUrl = normalizedBackendUrl.endsWith('/api/v1')
  ? normalizedBackendUrl
  : `${normalizedBackendUrl}/api/v1`

export const api = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
  timeout: 15000,
})

// Cache request interceptor - Check cache before making request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  // Check cache for GET requests
  const cacheStore = useCacheStore.getState()
  if (cacheStore.cacheEnabled && isCacheable(config)) {
    const cacheKey = generateCacheKey(config)
    const cachedData = getCachedData(cacheKey)

    if (cachedData) {
      // Return cached data by resolving the promise
      config._useCache = true
      config._cachedData = cachedData
      config._cacheKey = cacheKey
    }
  }

  return config
})

api.interceptors.response.use(
  (response) => {
    // Cache GET responses
    const cacheStore = useCacheStore.getState()
    if (cacheStore.cacheEnabled && isCacheable(response.config)) {
      const cacheKey = generateCacheKey(response.config)
      setCachedData(cacheKey, response.data, response.config.url)
      cacheStore.updateCacheStats()
    }

    // Invalidate related caches on mutations
    const method = response.config.method?.toUpperCase()
    if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
      const url = response.config.url

      if (url.includes('/listings')) {
        cacheStore.invalidateListings()
      }
      if (url.includes('/users')) {
        cacheStore.invalidateUser()
      }
      if (url.includes('/favorites')) {
        cacheStore.invalidateUser()
      }
      if (url.includes('/rentals')) {
        cacheStore.invalidateRentals()
      }
      if (url.includes('/reviews')) {
        cacheStore.invalidateReviews()
      }
    }

    return response
  },
  async (error) => {
    const originalRequest = error.config

    // If cache was available, return it on error
    if (originalRequest?._useCache && originalRequest?._cachedData) {
      return Promise.resolve({
        ...originalRequest,
        data: originalRequest._cachedData,
        status: 200,
        statusText: 'OK (from cache)',
        headers: {},
        config: originalRequest,
      })
    }

    if (
      error.response?.status !== 401 ||
      originalRequest?._retry ||
      originalRequest?.url?.includes('/auth/')
    ) {
      return Promise.reject(error)
    }

    originalRequest._retry = true
    try {
      const { data } = await axios.post(
        `${api.defaults.baseURL}/auth/refresh`,
        {},
        { withCredentials: true },
      )
      const newToken = data.access_token
      localStorage.setItem('accessToken', newToken)

      // Update auth store with new token
      const authStore = useAuthStore.getState()
      const currentRole = localStorage.getItem('role')
      const currentUserId = localStorage.getItem('userId')
      if (currentRole && currentUserId) {
        authStore.setAuth(newToken, currentRole, currentUserId)
      }

      originalRequest.headers.Authorization = `Bearer ${newToken}`
      return api(originalRequest)
    } catch (refreshError) {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('role')
      localStorage.removeItem('userId')

      // Clear auth store on logout
      const authStore = useAuthStore.getState()
      authStore.clear()

      // Clear cache on logout
      const cacheStore = useCacheStore.getState()
      cacheStore.clearCache()

      return Promise.reject(refreshError)
    }
  },
)
