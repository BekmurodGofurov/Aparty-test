import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { AnimatePresence, motion } from 'framer-motion'
import { SlidersHorizontal } from 'lucide-react'
import ListingCard from '../../../components/ListingCard/ListingCard.jsx'
import { FilterPanel } from '../../../components/search/FilterPanel'
import { EmptyState } from '../../../components/ui/EmptyState'
import { ListingCardSkeleton } from '../../../components/ui/ListingCardSkeleton.jsx'
import { useListingStore } from '../../../store/listingStore'
import { AMENITY_KEYS } from '../../../utils/amenities'
import './PropertySearch.scss'

export function PropertySearch() {
  const { t } = useTranslation()
  const [filterOpen, setFilterOpen] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()
  const {
    filters,
    results,
    total,
    page,
    pages,
    loading,
    loadingMore,
    error,
    setFilter,
    setAmenity,
    clearFilters,
    replaceFilters,
    fetchResults,
    loadMore,
  } = useListingStore()

  const searchString = searchParams.toString()

  useEffect(() => {
    const entries = Object.fromEntries(searchParams.entries())
    const nextFilters = Object.entries(entries).reduce((acc, [key, value]) => {
      if (AMENITY_KEYS.includes(key)) {
        acc.amenities = { ...acc.amenities, [key]: value === 'true' }
      } else {
        acc[key] = value === 'true' ? true : value
      }
      return acc
    }, {})
    replaceFilters(nextFilters)
    void fetchResults(1, nextFilters)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchString])

  const applyFilters = (event) => {
    event?.preventDefault?.()
    const params = Object.entries(filters).reduce((acc, [key, value]) => {
      if (key === 'amenities') {
        Object.entries(value).forEach(([amenityKey, amenityValue]) => {
          if (amenityValue) acc[amenityKey] = 'true'
        })
        return acc
      }
      if (value === '' || value === false || value === null) return acc
      acc[key] = String(value)
      return acc
    }, {})
    setSearchParams(params)
    setFilterOpen(false)
  }

  const activeFilterCount = useMemo(() => {
    let count = 0
    if (filters.region) count++
    if (filters.district) count++
    if (filters.price_min || filters.price_max) count++
    if (filters.target_gender) count++
    if (filters.rental_type) count++
    if (filters.rooms_count) count++
    if (filters.available_spaces) count++
    if (filters.move_in_ready) count++
    if (filters.owner_role) count++
    Object.values(filters.amenities || {}).forEach((v) => { if (v) count++ })
    return count
  }, [filters])

  return (
    <main className="search-page page">
      <motion.button
        className="filter-toggle-btn"
        onClick={() => setFilterOpen(true)}
        whileHover={{ y: -2, scale: 1.01 }}
        whileTap={{ scale: 0.97 }}
      >
        <SlidersHorizontal size={18} />
        <span>{t('search.filters')}</span>
        {activeFilterCount > 0 && <span className="filter-count-badge">{activeFilterCount}</span>}
      </motion.button>

      <aside className="filter-panel desktop-panel">
        <FilterPanel
          filters={filters}
          setFilter={setFilter}
          setAmenity={setAmenity}
          applyFilters={applyFilters}
          activeFilterCount={activeFilterCount}
          clearAll={() => {
            clearFilters()
            setSearchParams({})
          }}
        />
      </aside>

      <AnimatePresence>
        {filterOpen && (
          <motion.aside className="filter-panel mobile-panel open" initial={false}>
            <motion.div
              className="drawer-backdrop"
              onClick={() => setFilterOpen(false)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.22 }}
            />
            <motion.div
              className="drawer-content"
              initial={{ x: '100%', opacity: 0.9 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: '100%', opacity: 0.9 }}
              transition={{ type: 'spring', stiffness: 360, damping: 34 }}
            >
              <FilterPanel
                filters={filters}
                setFilter={setFilter}
                setAmenity={setAmenity}
                applyFilters={applyFilters}
                activeFilterCount={activeFilterCount}
                onClose={() => setFilterOpen(false)}
                clearAll={() => {
                  clearFilters()
                  setSearchParams({})
                }}
              />
            </motion.div>
          </motion.aside>
        )}
      </AnimatePresence>

      <section className="results-area">
        {loading && (
          <div className="listings-grid">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <ListingCardSkeleton key={i} />
            ))}
          </div>
        )}
        {!loading && (
          <div className="results-top">
            <p>
              <span className="results-count-num">{total || results.length}</span>
              {' '}{t('search.results')}
            </p>
            <div className="mono">{t('search.premium_top')}</div>
          </div>
        )}
        {!loading && error && (
          <EmptyState
            icon="⚠️"
            title={error}
            desc="Backenddan ma'lumot kelmadi. Sahifani yangilang yoki server logini tekshiring."
            action={{
              label: t('search.show_10'),
              onClick: () => void fetchResults(1),
            }}
          />
        )}
        {!loading && !error && results.length === 0 && (
          <EmptyState
            icon="🔍"
            title={t('search.nothing_found')}
            desc={t('search.nothing_found_desc')}
            action={{
              label: t('search.clear_filter'),
              onClick: () => {
                clearFilters()
                setSearchParams({})
              },
            }}
          />
        )}
        {!loading && (
          <div className="listings-grid">
            {results.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        )}
        {!loading && page < pages && (
          <div className="pagination-wrap">
            <button className="button-secondary" type="button" onClick={() => void loadMore()} disabled={loadingMore}>
              {t('search.show_10')}
            </button>
          </div>
        )}

        {/* Bottom count summary */}
        {!loading && results.length > 0 && (
          <div className="results-footer-count">
            <span className="results-footer-icon">🏠</span>
            <span>
              Jami <strong>{total || results.length}</strong> ta kvartira topildi
            </span>
          </div>
        )}
      </section>
    </main>
  )
}
