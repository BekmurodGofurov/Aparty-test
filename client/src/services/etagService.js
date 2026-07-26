/**
 * ETag Service — Zero-bandwidth caching via HTTP 304 Not Modified.
 *
 * How it works:
 * ┌─────────┐   GET /locations          ┌─────────┐
 * │ Browser │ ───────────────────────>   │ Server  │
 * │         │   If-None-Match: W/"abc"   │         │
 * │         │ <─────────────────────── │         │
 * │         │   304 Not Modified         │         │
 * │         │   (empty body = 0 bytes)   │         │
 * └─────────┘                            └─────────┘
 *
 * 1. On the FIRST request, the server responds with 200 + ETag header.
 *    We store both the data AND the ETag in the Zustand persist store.
 *
 * 2. On SUBSEQUENT requests, we attach the stored ETag as `If-None-Match`.
 *    - If data hasn't changed → server returns 304 (empty body).
 *      We intercept this and return the locally cached data.
 *    - If data changed → server returns 200 + new ETag + new data.
 *      We update the store with both.
 *
 * This eliminates redundant data transfer entirely for unchanged resources.
 */

import { api } from './api'
import { useLocalCacheStore } from '../store/useLocalCacheStore'

/**
 * Make a GET request with automatic ETag handling.
 *
 * @param {string} url    — API endpoint path (e.g. '/locations')
 * @param {Object} [config] — Optional Axios config (params, headers, etc.)
 * @returns {Promise<any>}  — The response data (from server or local cache)
 */
export async function fetchWithEtag(url, config = {}) {
  const store = useLocalCacheStore.getState()

  // ── Step 1: Check if we have a stored ETag for this URL ──────────
  const storedEntry = store.etagCache[url]
  const headers = { ...(config.headers || {}) }

  if (storedEntry?.etag) {
    // Attach the stored ETag so the server can compare.
    headers['If-None-Match'] = storedEntry.etag
  }

  try {
    const response = await api.get(url, {
      ...config,
      headers,
      // CRITICAL: Tell Axios to NOT throw on 304 status codes.
      // By default Axios treats any 2xx as success and everything else as error.
      // We override validateStatus to also accept 304.
      validateStatus: (status) => (status >= 200 && status < 300) || status === 304,
    })

    // ── Step 2: Handle 304 Not Modified ──────────────────────────
    // Server confirmed our cached version is still fresh.
    // Return the locally stored data — zero bytes were transferred!
    if (response.status === 304) {
      if (storedEntry?.data !== undefined) {
        return storedEntry.data
      }
      // Edge case: we sent an ETag but lost the local data (e.g. cleared storage).
      // Fall through to refetch without ETag.
      return refetchWithoutEtag(url, config)
    }

    // ── Step 3: Handle 200 OK — fresh data from server ───────────
    const newEtag = response.headers['etag'] || response.headers['ETag'] || ''
    const newData = response.data

    // Persist both the data and the ETag to the Zustand store.
    if (newEtag) {
      store.setEtagEntry(url, newEtag, newData)
    }

    return newData
  } catch (error) {
    // ── Fallback: If the request fails entirely, try to serve stale cache ─
    if (storedEntry?.data !== undefined) {
      console.warn(
        `[ETag] Network error for ${url}, serving stale cache.`,
        error.message
      )
      return storedEntry.data
    }
    // No cache available — propagate the error.
    throw error
  }
}

/**
 * Refetch without ETag header (used when local data is missing).
 * @param {string} url
 * @param {Object} config
 * @returns {Promise<any>}
 */
async function refetchWithoutEtag(url, config = {}) {
  const store = useLocalCacheStore.getState()

  const response = await api.get(url, config)
  const newEtag = response.headers['etag'] || response.headers['ETag'] || ''
  const newData = response.data

  if (newEtag) {
    store.setEtagEntry(url, newEtag, newData)
  }

  return newData
}

/**
 * Invalidate a specific ETag cache entry.
 * Use after mutations (POST/PUT/DELETE) that change the resource.
 *
 * @param {string} url — The endpoint URL to invalidate.
 */
export function invalidateEtag(url) {
  const store = useLocalCacheStore.getState()
  store.removeEtagEntry(url)
}

/**
 * Invalidate all ETag cache entries.
 */
export function invalidateAllEtags() {
  const store = useLocalCacheStore.getState()
  store.clearEtagCache()
}
