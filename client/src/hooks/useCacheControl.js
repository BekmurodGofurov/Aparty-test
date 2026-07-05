import { useCallback } from 'react'
import { useCacheStore } from '../store/cacheStore'

/**
 * useCacheControl - Hook for managing cache in components
 * Provides easy access to cache operations
 */
export const useCacheControl = () => {
  const cacheStore = useCacheStore()

  const toggleCache = useCallback(() => {
    cacheStore.toggleCache()
  }, [cacheStore])

  const clearCache = useCallback(() => {
    cacheStore.clearCache()
  }, [cacheStore])

  const invalidateListings = useCallback(() => {
    cacheStore.invalidateListings()
  }, [cacheStore])

  const invalidateUser = useCallback(() => {
    cacheStore.invalidateUser()
  }, [cacheStore])

  const invalidateRentals = useCallback(() => {
    cacheStore.invalidateRentals()
  }, [cacheStore])

  const invalidateReviews = useCallback(() => {
    cacheStore.invalidateReviews()
  }, [cacheStore])

  return {
    cacheEnabled: cacheStore.cacheEnabled,
    cacheStats: cacheStore.cacheStats,
    toggleCache,
    clearCache,
    invalidateListings,
    invalidateUser,
    invalidateRentals,
    invalidateReviews,
  }
}
