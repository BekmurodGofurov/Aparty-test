/**
 * Example Component - Cache Control UI
 * 
 * Bu component cache statini ko'rsatadi va boshqarish uchun buttons beradi.
 * Shared components-ga qo'shish mumkin.
 */

import { useCacheControl } from '@/hooks/useCacheControl'

export function CacheControlPanel() {
  const {
    cacheEnabled,
    cacheStats,
    toggleCache,
    clearCache,
    invalidateListings,
    invalidateUser,
    invalidateRentals,
    invalidateReviews,
  } = useCacheControl()

  return (
    <div className="cache-control-panel" style={{ padding: '16px', borderRadius: '8px', backgroundColor: '#f5f5f5' }}>
      <h3>Cache Settings</h3>
      
      {/* Cache Status */}
      <div style={{ marginBottom: '12px' }}>
        <p>
          <strong>Status:</strong> {' '}
          <span style={{ color: cacheEnabled ? '#22c55e' : '#ef4444' }}>
            {cacheEnabled ? '✓ Enabled' : '✗ Disabled'}
          </span>
        </p>
        <p>
          <strong>Cache Entries:</strong> {cacheStats.entriesCount}
        </p>
        <p>
          <strong>Cache Size:</strong> {cacheStats.totalSizeKB} KB
        </p>
      </div>

      {/* Control Buttons */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <button 
          onClick={toggleCache}
          style={{
            padding: '8px 12px',
            borderRadius: '4px',
            border: 'none',
            backgroundColor: cacheEnabled ? '#ef4444' : '#22c55e',
            color: 'white',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          {cacheEnabled ? 'Disable Cache' : 'Enable Cache'}
        </button>

        <button 
          onClick={clearCache}
          style={{
            padding: '8px 12px',
            borderRadius: '4px',
            border: 'none',
            backgroundColor: '#f97316',
            color: 'white',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          Clear All Cache
        </button>

        <button 
          onClick={invalidateListings}
          style={{
            padding: '8px 12px',
            borderRadius: '4px',
            border: '1px solid #3b82f6',
            backgroundColor: 'white',
            color: '#3b82f6',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          Clear Listings
        </button>

        <button 
          onClick={invalidateUser}
          style={{
            padding: '8px 12px',
            borderRadius: '4px',
            border: '1px solid #8b5cf6',
            backgroundColor: 'white',
            color: '#8b5cf6',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          Clear User
        </button>

        <button 
          onClick={invalidateRentals}
          style={{
            padding: '8px 12px',
            borderRadius: '4px',
            border: '1px solid #06b6d4',
            backgroundColor: 'white',
            color: '#06b6d4',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          Clear Rentals
        </button>

        <button 
          onClick={invalidateReviews}
          style={{
            padding: '8px 12px',
            borderRadius: '4px',
            border: '1px solid #ec4899',
            backgroundColor: 'white',
            color: '#ec4899',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          Clear Reviews
        </button>
      </div>

      {/* Info */}
      <div style={{ marginTop: '12px', fontSize: '12px', color: '#666' }}>
        <p>💡 Cache avtomatik ravishda:</p>
        <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
          <li>GET requests-ni saqlaydi (5-15 minut)</li>
          <li>POST/PUT/DELETE-dan keyin o'chiriladi</li>
          <li>Offline-da cached data-dan foydalanadi</li>
          <li>Storage to'lganda eski entries o'chiriladi</li>
        </ul>
      </div>
    </div>
  )
}

/**
 * Example usage in another component:
 * 
 * import { useCacheControl } from '@/hooks/useCacheControl'
 * import { useEffect } from 'react'
 * 
 * export function MyListings() {
 *   const { invalidateListings } = useCacheControl()
 * 
 *   const handleCreateListing = async () => {
 *     // ... create listing
 *     invalidateListings() // Clear cache so fresh data loads next time
 *   }
 * 
 *   return <div>...</div>
 * }
 */
