import { create } from 'zustand'
import { 
  clearCachePattern, 
  clearAllCache,
  getCacheStats
} from '../services/cacheService'

/**
 * Cache Store - Manages cache state and operations
 */
export const useCacheStore = create((set, get) => ({
  // State
  cacheEnabled: true,
  cacheStats: { entriesCount: 0, totalSizeKB: 0 },
  
  // Actions
  enableCache: () => set({ cacheEnabled: true }),
  disableCache: () => set({ cacheEnabled: false }),
  toggleCache: () => set(state => ({ cacheEnabled: !state.cacheEnabled })),
  
  // Invalidate cache for listings
  invalidateListings: () => {
    clearCachePattern('/listings')
  },
  
  // Invalidate cache for user data
  invalidateUser: () => {
    clearCachePattern('/users')
    clearCachePattern('/favorites')
  },
  
  // Invalidate cache for rentals
  invalidateRentals: () => {
    clearCachePattern('/rentals')
  },
  
  // Invalidate cache for reviews
  invalidateReviews: () => {
    clearCachePattern('/reviews')
  },
  
  // Invalidate all cache
  clearCache: () => {
    clearAllCache()
  },
  
  // Update cache statistics
  updateCacheStats: () => {
    const stats = getCacheStats()
    set({ cacheStats: stats })
  },
  
  // Get cache status
  isCacheEnabled: () => get().cacheEnabled,
}))
