/**
 * Cache Service - Manages localStorage caching for API requests
 * Reduces server load by storing frequently accessed data locally
 */

const CACHE_PREFIX = 'aparty_cache_'
const CACHE_EXPIRY_PREFIX = 'aparty_cache_expiry_'
const DEFAULT_TTL = 5 * 60 * 1000 // 5 minutes default
const LISTING_TTL = 10 * 60 * 1000 // 10 minutes for listings
const USER_TTL = 15 * 60 * 1000 // 15 minutes for user data

// Endpoints that should NOT be cached (auth, mutations, etc)
const NON_CACHEABLE_ENDPOINTS = [
  '/auth',
  '/upload',
]

// GET endpoints with custom TTL
const CUSTOM_TTL_ENDPOINTS = {
  '/listings/search': LISTING_TTL,
  '/listings/': LISTING_TTL,
  '/users/me': USER_TTL,
  '/users/': USER_TTL,
  '/favorites/me': USER_TTL,
  '/rentals/owner/me': 10 * 60 * 1000,
}

/**
 * Generate cache key from request config
 */
export const generateCacheKey = (config) => {
  const { url, params } = config
  const paramString = params ? JSON.stringify(params) : ''
  return `${CACHE_PREFIX}${url}${paramString}`
}

/**
 * Check if endpoint should be cached
 */
export const isCacheable = (config) => {
  const { method = 'GET', url } = config
  
  // Only cache GET requests
  if (method.toUpperCase() !== 'GET') return false
  
  // Don't cache auth endpoints and uploads
  if (NON_CACHEABLE_ENDPOINTS.some(endpoint => url.includes(endpoint))) {
    return false
  }
  
  return true
}

/**
 * Get TTL for an endpoint
 */
const getTTL = (url) => {
  for (const [endpoint, ttl] of Object.entries(CUSTOM_TTL_ENDPOINTS)) {
    if (url.includes(endpoint)) {
      return ttl
    }
  }
  return DEFAULT_TTL
}

/**
 * Get cached data if available and not expired
 */
export const getCachedData = (key) => {
  try {
    const cachedData = localStorage.getItem(key)
    const expiry = localStorage.getItem(CACHE_EXPIRY_PREFIX + key)
    
    if (!cachedData || !expiry) return null
    
    // Check if cache has expired
    if (Date.now() > parseInt(expiry, 10)) {
      removeCachedData(key)
      return null
    }
    
    return JSON.parse(cachedData)
  } catch (error) {
    console.warn('Error reading cache:', error)
    return null
  }
}

/**
 * Set cache data with expiry
 */
export const setCachedData = (key, data, url = '') => {
  try {
    const ttl = getTTL(url)
    const expiryTime = Date.now() + ttl
    
    localStorage.setItem(key, JSON.stringify(data))
    localStorage.setItem(CACHE_EXPIRY_PREFIX + key, expiryTime.toString())
  } catch (error) {
    console.warn('Error setting cache:', error)
    // If storage quota exceeded, clear old caches
    if (error.name === 'QuotaExceededError') {
      clearOldestCache()
      try {
        localStorage.setItem(key, JSON.stringify(data))
        localStorage.setItem(CACHE_EXPIRY_PREFIX + key, (Date.now() + getTTL(url)).toString())
      } catch (retryError) {
        console.warn('Cache still failed after cleanup:', retryError)
      }
    }
  }
}

/**
 * Remove specific cached data
 */
export const removeCachedData = (key) => {
  try {
    localStorage.removeItem(key)
    localStorage.removeItem(CACHE_EXPIRY_PREFIX + key)
  } catch (error) {
    console.warn('Error removing cache:', error)
  }
}

/**
 * Clear cache for a specific endpoint pattern
 */
export const clearCachePattern = (pattern) => {
  try {
    const keys = Object.keys(localStorage)
    keys.forEach(key => {
      if (key.startsWith(CACHE_PREFIX) && key.includes(pattern)) {
        const expireKey = CACHE_EXPIRY_PREFIX + key
        localStorage.removeItem(key)
        localStorage.removeItem(expireKey)
      }
    })
  } catch (error) {
    console.warn('Error clearing cache pattern:', error)
  }
}

/**
 * Clear all cache
 */
export const clearAllCache = () => {
  try {
    const keys = Object.keys(localStorage)
    keys.forEach(key => {
      if (key.startsWith(CACHE_PREFIX) || key.startsWith(CACHE_EXPIRY_PREFIX)) {
        localStorage.removeItem(key)
      }
    })
  } catch (error) {
    console.warn('Error clearing all cache:', error)
  }
}

/**
 * Clear oldest cache entry (for quota exceeded)
 */
const clearOldestCache = () => {
  try {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(CACHE_EXPIRY_PREFIX))
    if (keys.length === 0) return
    
    // Find oldest expiry
    let oldestKey = keys[0]
    let oldestTime = parseInt(localStorage.getItem(oldestKey), 10)
    
    keys.forEach(key => {
      const time = parseInt(localStorage.getItem(key), 10)
      if (time < oldestTime) {
        oldestTime = time
        oldestKey = key
      }
    })
    
    // Remove the oldest entry
    const dataKey = oldestKey.replace(CACHE_EXPIRY_PREFIX, '')
    localStorage.removeItem(dataKey)
    localStorage.removeItem(oldestKey)
  } catch (error) {
    console.warn('Error clearing oldest cache:', error)
  }
}

/**
 * Get cache statistics
 */
export const getCacheStats = () => {
  try {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(CACHE_PREFIX))
    let totalSize = 0
    
    keys.forEach(key => {
      totalSize += localStorage.getItem(key).length
    })
    
    return {
      entriesCount: keys.length,
      totalSizeKB: (totalSize / 1024).toFixed(2),
    }
  } catch (error) {
    console.warn('Error getting cache stats:', error)
    return { entriesCount: 0, totalSizeKB: 0 }
  }
}
