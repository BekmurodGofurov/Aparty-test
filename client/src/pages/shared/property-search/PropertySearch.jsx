import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowUpRight, House, MapPinned, RotateCcw, Search, ShieldCheck, SlidersHorizontal, X } from 'lucide-react'
import ListingCard from '../../../components/ListingCard/ListingCard.jsx'
import { FilterPanel } from '../../../components/search/FilterPanel'
import { ListingCardSkeleton } from '../../../components/ui/ListingCardSkeleton.jsx'
import { useListingStore } from '../../../store/listingStore'
import { AMENITY_KEYS } from '../../../utils/amenities'
import './PropertySearch.scss'

const FILTER_KEYS = ['region', 'district', 'price_min', 'price_max', 'target_gender', 'rental_type', 'rooms_count', 'available_spaces', 'move_in_ready', 'owner_role']
const AMENITY_LABELS = { air_conditioner: 'ac', washing_machine: 'washer' }

function parseFilters(params) {
  const filters = {}
  for (const [key, value] of params) {
    if (AMENITY_KEYS.includes(key)) filters.amenities = { ...filters.amenities, [key]: value === 'true' }
    else if (FILTER_KEYS.includes(key)) filters[key] = key === 'move_in_ready' ? value === 'true' : value
  }
  return filters
}

function FilterDrawer({ onClose, children, label }) {
  const dialog = useRef(null)

  useEffect(() => {
    const previousFocus = document.activeElement
    const previousOverflow = document.body.style.overflow
    const root = document.getElementById('root')
    const previousInert = root?.inert
    document.body.style.overflow = 'hidden'
    if (root) root.inert = true
    dialog.current?.querySelector('.filter-close')?.focus()
    const onKeyDown = event => {
      if (event.key === 'Escape') { event.preventDefault(); onClose(); return }
      if (event.key !== 'Tab') return
      const items = [...dialog.current.querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), summary, [tabindex="0"]')]
        .filter(element => element.getClientRects().length > 0)
      const first = items[0]
      const last = items.at(-1)
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    }
    const media = window.matchMedia('(min-width: 1024px)')
    const onResize = event => { if (event.matches) onClose() }
    document.addEventListener('keydown', onKeyDown)
    media.addEventListener('change', onResize)
    return () => {
      document.body.style.overflow = previousOverflow
      if (root) root.inert = previousInert
      document.removeEventListener('keydown', onKeyDown)
      media.removeEventListener('change', onResize)
      previousFocus?.focus()
    }
  }, [onClose])

  return createPortal(
    <div className="search-filter-drawer">
      <div className="search-drawer-backdrop" onClick={onClose} aria-hidden="true" />
      <div className="search-drawer-content" role="dialog" aria-modal="true" aria-label={label} tabIndex={-1} ref={dialog}>{children}</div>
    </div>,
    document.body,
  )
}

export function PropertySearch() {
  const { t } = useTranslation()
  const titleId = useId()
  const [filterOpen, setFilterOpen] = useState(false)
  const closeFilters = useCallback(() => setFilterOpen(false), [])
  const [searchParams, setSearchParams] = useSearchParams()
  const { filters, results, total, page, pages, loading, loadingMore, error, setFilter, setAmenity, clearFilters, replaceFilters, fetchResults, loadMore } = useListingStore()
  const searchString = searchParams.toString()

  useEffect(() => {
    const nextFilters = parseFilters(new URLSearchParams(searchString))
    replaceFilters(nextFilters)
    void fetchResults(1, nextFilters)
  }, [searchString, replaceFilters, fetchResults])

  const applyFilters = () => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (key === 'amenities') {
        Object.entries(value).forEach(([amenityKey, enabled]) => { if (enabled) params.set(amenityKey, 'true') })
      } else if (value !== '' && value !== false && value != null) params.set(key, String(value))
    })
    if (params.toString() === searchString) void fetchResults(1, filters)
    else setSearchParams(params)
    closeFilters()
  }

  const clearAll = () => {
    clearFilters()
    if (!searchString) void fetchResults(1, {})
    else setSearchParams({})
  }

  const removeFilter = key => {
    const next = new URLSearchParams(searchParams)
    if (key === 'price') { next.delete('price_min'); next.delete('price_max') }
    else next.delete(key)
    if (key === 'region') next.delete('district')
    setSearchParams(next)
  }

  const activeFilterCount = useMemo(() => {
    return FILTER_KEYS.filter(key => !['price_min', 'price_max'].includes(key) && Boolean(filters[key])).length
      + Number(filters.price_min !== '' || filters.price_max !== '')
      + Object.values(filters.amenities || {}).filter(Boolean).length
  }, [filters])

  const appliedFilters = []
  for (const [key, value] of searchParams) {
    if (!value || value === 'false' || key === 'price_max' && searchParams.has('price_min')) continue
    let label
    if (key === 'region' || key === 'district') label = value
    else if (key === 'price_min' || key === 'price_max') {
      const min = searchParams.get('price_min')
      const max = searchParams.get('price_max')
      label = min && max ? '$' + min + ' – $' + max : min ? '$' + min + '+' : '≤ $' + max
    } else if (key === 'rooms_count') label = value + ' ' + t('card.rooms')
    else if (key === 'target_gender') label = t('search.gender_' + value)
    else if (key === 'rental_type') label = t(value === 'full_unit' ? 'search.apartment_type_entire' : 'search.apartment_type_per_bed')
    else if (key === 'move_in_ready') label = t('search.move_in')
    else if (key === 'available_spaces') label = t('search.available_spots') + ': ' + value
    else if (key === 'owner_role') label = t('card.' + value)
    else if (AMENITY_KEYS.includes(key) && value === 'true') label = t('search.' + (AMENITY_LABELS[key] || key))
    if (label) appliedFilters.push({ key: key.startsWith('price_') ? 'price' : key, label })
  }

  const panelProps = { filters, setFilter, setAmenity, applyFilters, clearAll, activeFilterCount }

  return (
    <div className="search-page page">
      <header className="search-page-heading">
        <div className="search-heading-copy">
          <p className="search-eyebrow"><span />{t('search.experience.eyebrow')}</p>
          <h1 id={titleId}>{t('search.experience.title')}<span>.</span></h1>
          <p className="search-heading-description">{t('search.experience.subtitle')}</p>
        </div>
        <Link className="search-map-link" to="/map"><MapPinned size={18} /><span>{t('home.experience.map_action')}</span><ArrowUpRight size={15} /></Link>
      </header>

      <div className="search-layout">
        <aside className="search-desktop-filters" aria-label={t('search.filters')}><FilterPanel {...panelProps} /></aside>
        <section className="results-area" aria-labelledby={titleId} aria-busy={loading}>
          <div className="search-results-toolbar">
            <div className="search-results-count">
              <span className="search-result-icon"><House size={18} /></span>
              <p role="status">{loading ? t('search.experience.loading') : <><strong>{total}</strong> {t('search.results')}</>}</p>
            </div>
            <span className="search-result-note"><ShieldCheck size={14} />{t('search.premium_top')}</span>
            <button type="button" className="filter-toggle-btn" onClick={() => setFilterOpen(true)} aria-haspopup="dialog" aria-expanded={filterOpen}>
              <SlidersHorizontal size={17} /><span>{t('search.filters')}</span>{activeFilterCount > 0 && <b>{activeFilterCount}</b>}
            </button>
          </div>

          {appliedFilters.length > 0 && (
            <div className="search-active-filters" aria-label={t('search.experience.active_filters')}>
              {appliedFilters.map(({ key, label }) => <button key={key} className="search-filter-chip" type="button" onClick={() => removeFilter(key)} aria-label={t('search.experience.remove', { label })}>{label}<X size={12} /></button>)}
              <button type="button" className="search-clear-all" onClick={clearAll}>{t('search.clear')}</button>
            </div>
          )}

          {loading && results.length === 0 && <div className="listings-grid" aria-hidden="true">{Array.from({ length: 6 }, (_, i) => <ListingCardSkeleton key={i} />)}</div>}

          {!loading && (error || results.length === 0) && (
            <div className="search-empty-state" role={error ? 'alert' : undefined}>
              <div className="search-empty-art" aria-hidden="true"><div className="search-empty-ring" /><div className="search-empty-ring inner" /><span><Search size={32} strokeWidth={1.3} /></span><House size={18} className="search-empty-house" /></div>
              <span className="search-empty-kicker">{t('search.experience.eyebrow')}</span>
              <h2>{t(error ? 'search.experience.load_error' : 'search.nothing_found')}</h2>
              <p>{t(error ? 'search.experience.error_hint' : 'search.nothing_found_desc')}</p>
              <button className="search-empty-action" type="button" onClick={error ? () => void fetchResults(1) : clearAll}>
                <RotateCcw size={15} />{t(error ? 'search.experience.retry' : 'search.clear_filter')}
              </button>
              <Link to="/map" className="search-empty-map">{t('home.experience.map_action')}<ArrowUpRight size={14} /></Link>
            </div>
          )}

          {results.length > 0 && <div className="listings-grid">{results.map(listing => <ListingCard key={listing.id} listing={listing} />)}</div>}
          {!error && page < pages && <div className="pagination-wrap"><button className="search-load-more" type="button" onClick={() => void loadMore()} disabled={loading || loadingMore}>{t(loadingMore ? 'search.experience.loading' : 'search.show_10')}</button></div>}
          {results.length > 0 && <p className="search-results-footer">{t('search.experience.summary', { shown: results.length, total })}</p>}
        </section>
      </div>
      {filterOpen && <FilterDrawer onClose={closeFilters} label={t('search.filters')}><FilterPanel {...panelProps} onClose={closeFilters} /></FilterDrawer>}
    </div>
  )
}
