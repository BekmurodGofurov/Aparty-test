import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import { browserCache } from './browserCache'
import { decodeJwtPayload } from '../utils/jwt'

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

const networkAdapter = axios.getAdapter(api.defaults.adapter)
// Identical GETs that are already on their way share one request.
const inFlight = new Map()

const signedInUserId = (token) => (token ? decodeJwtPayload(token)?.sub ?? null : null)

const cloneResponse = (response) => ({ ...response, data: structuredClone(response.data) })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  if ((config.method || 'get').toLowerCase() !== 'get') return config

  const userId = signedInUserId(token)
  const rule = browserCache.ruleFor(config.url, userId)
  if (!rule) return config

  const key = browserCache.keyFor(userId, config.url, config.params)
  const cached = browserCache.get(key)
  config.adapter = (adapterConfig) => {
    if (cached !== undefined) {
      return Promise.resolve({ data: cached, status: 200, statusText: 'OK', headers: {}, config: adapterConfig, request: {} })
    }
    if (!inFlight.has(key)) {
      inFlight.set(
        key,
        networkAdapter(adapterConfig)
          .then((response) => {
            browserCache.set(key, response.data, rule.ttl)
            return response
          })
          .finally(() => inFlight.delete(key)),
      )
    }
    return inFlight.get(key).then(cloneResponse)
  }
  return config
})

api.interceptors.response.use(
  (response) => {
    const method = response.config.method?.toUpperCase()
    if (method && method !== 'GET') {
      browserCache.invalidateForWrite(response.config.url)
    }

    return response
  },
  async (error) => {
    const originalRequest = error.config

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
      }
      return Promise.reject(refreshError)
    }
  },
)
