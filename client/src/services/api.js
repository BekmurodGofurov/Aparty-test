import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import { useCacheStore } from '../store/cacheStore'
import { decodeJwtPayload } from '../utils/jwt'
import {
  generateCacheKey,
  isCacheable,
  getCachedData,
  setCachedData,
} from './cacheService'

// All requests go through the API gateway (see docker-compose.yml, port 8080).
// An empty VITE_BACKEND_API means "same origin": the dev server proxies /api to the gateway.
const DEFAULT_GATEWAY_URL = 'http://localhost:8080'
const backendUrl = import.meta.env.VITE_BACKEND_API ?? DEFAULT_GATEWAY_URL

const normalizedBackendUrl = backendUrl.replace(/\/+$/, '')
const apiBaseUrl = normalizedBackendUrl.endsWith('/api/v1')
  ? normalizedBackendUrl
  : `${normalizedBackendUrl}/api/v1`

// Refresh tokens are single-use, so concurrent 401s must share one refresh: a second call with the
// already-used token would fail and wrongly sign the user out. Requests of one tab share a promise;
// several tabs take turns through a Web Lock and reuse the token another tab already refreshed.
const REFRESH_LOCK = 'aparty-token-refresh'
let refreshPromise = null

const runExclusively = (task) => (navigator.locks ? navigator.locks.request(REFRESH_LOCK, task) : task())

const refreshAccessToken = (failedToken) => {
  if (!refreshPromise) {
    refreshPromise = runExclusively(async () => {
      const current = localStorage.getItem('accessToken')
      if (current && current !== failedToken) return current

      const { data } = await axios.post(`${apiBaseUrl}/auth/refresh`, {}, { withCredentials: true })
      const claims = decodeJwtPayload(data.access_token)
      const userId = localStorage.getItem('userId') || claims?.sub
      // The role comes from the new token, so it survives whatever happened to local storage.
      useAuthStore.getState().setAuth(data.access_token, claims?.role ?? null, userId)
      return data.access_token
    }).finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

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
      const failedToken = originalRequest.headers?.Authorization?.replace('Bearer ', '')
      const newToken = await refreshAccessToken(failedToken)
      originalRequest.headers.Authorization = `Bearer ${newToken}`
      return api(originalRequest)
    } catch (refreshError) {
      // Sign out only when the server refused the refresh token. A network error must not log the user out.
      if (refreshError.response?.status === 401) {
        useAuthStore.getState().clear()
        useCacheStore.getState().clearCache()
      }
      return Promise.reject(refreshError)
    }
  },
)
