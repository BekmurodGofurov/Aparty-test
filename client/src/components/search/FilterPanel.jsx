import { useId } from 'react'
import { useTranslation } from 'react-i18next'
import {
  BedDouble, Building2, Check, ChevronDown, ChefHat, DollarSign, Droplets,
  Flame, Home, MapPin, Refrigerator, RotateCcw, Search, SlidersHorizontal,
  Snowflake, Sparkles, Tv, Users, WashingMachine, Wifi, X,
} from 'lucide-react'
import { REGIONS_DATA } from '../../data/regions'
import './FilterPanel.scss'

function FilterSection({ icon, title, meta, defaultOpen = false, children }) {
  return (
    <details className="filter-section" open={defaultOpen}>
      <summary>
        <span className="filter-section-icon">{icon}</span>
        <span className="filter-section-copy"><strong>{title}</strong>{meta && <small>{meta}</small>}</span>
        <ChevronDown size={15} className="filter-chevron" aria-hidden="true" />
      </summary>
      <div className="filter-section-body">{children}</div>
    </details>
  )
}

function Choice({ active, icon, children, onClick }) {
  return (
    <button type="button" className={'filter-choice' + (active ? ' active' : '')} aria-pressed={active} onClick={onClick}>
      {icon}{children}
    </button>
  )
}

export function FilterPanel({ filters, setFilter, setAmenity, applyFilters, clearAll, onClose, activeFilterCount = 0 }) {
  const { t } = useTranslation()
  const formId = useId()
  const districts = REGIONS_DATA[filters.region] || []
  const amenities = [
    ['wifi', 'wifi', Wifi], ['gas', 'gas', Flame], ['water', 'water', Droplets], ['tv', 'tv', Tv],
    ['air_conditioner', 'ac', Snowflake], ['washing_machine', 'washer', WashingMachine],
    ['fridge', 'fridge', Refrigerator], ['kitchen', 'kitchen', ChefHat],
  ]
  const priceMax = filters.price_max === '' ? 1000 : Number(filters.price_max)
  const invalidPrice = filters.price_min !== '' && filters.price_max !== '' && Number(filters.price_min) > Number(filters.price_max)
  const selectedAmenities = Object.values(filters.amenities || {}).filter(Boolean).length

  return (
    <div className="filter-panel-inner">
      <div className="filter-panel-head">
        <span className="filter-head-icon"><SlidersHorizontal size={19} /></span>
        <div><h2>{t('search.filters')}{activeFilterCount > 0 && <span>{activeFilterCount}</span>}</h2><p>{t('search.experience.filter_hint')}</p></div>
        {onClose && <button type="button" className="filter-close" onClick={onClose} aria-label={t('search.experience.close')}><X size={20} /></button>}
      </div>
      <form id={formId} className="filter-form" onSubmit={event => { event.preventDefault(); if (!invalidPrice) applyFilters() }}>
        <div className="filter-fields">
          <FilterSection icon={<MapPin size={17} />} title={t('search.location')} meta={filters.district || filters.region || t('search.anywhere')} defaultOpen>
            <label className="filter-field">
              <span>{t('search.region')}</span>
              <select value={filters.region} onChange={event => { setFilter('region', event.target.value); setFilter('district', '') }}>
                <option value="">{t('home.experience.all_regions')}</option>
                {Object.keys(REGIONS_DATA).map(region => <option key={region} value={region}>{region}</option>)}
              </select>
            </label>
            <label className="filter-field">
              <span>{t('home.experience.district')}</span>
              <select value={filters.district} disabled={!filters.region} onChange={event => setFilter('district', event.target.value)}>
                <option value="">{filters.region ? t('home.experience.all_districts') : t('home.experience.choose_region')}</option>
                {districts.map(district => <option key={district} value={district}>{district}</option>)}
              </select>
            </label>
          </FilterSection>
          <FilterSection icon={<DollarSign size={17} />} title={t('search.price')} meta={t('home.experience.monthly_price')} defaultOpen>
            <div className="filter-price-range" style={{ '--range-progress': Math.min(100, Math.max(0, priceMax / 10)) + '%' }}>
              <span>{filters.price_min ? '$' + filters.price_min : '$0'}</span>
              <strong>{filters.price_max !== '' ? '$' + filters.price_max : t('search.any_price')}</strong>
              <input type="range" min="0" max="1000" step="10" value={Math.min(1000, priceMax)} onChange={event => setFilter('price_max', event.target.value)} aria-label={t('home.experience.maximum_price')} />
            </div>
            <div className="filter-price-inputs">
              <label className="filter-field"><span>{t('search.price_min')}, $</span><input type="number" inputMode="numeric" min="0" placeholder="0" value={filters.price_min} onChange={event => setFilter('price_min', event.target.value)} aria-invalid={invalidPrice} aria-describedby={invalidPrice ? formId + '-price-error' : undefined} /></label>
              <span aria-hidden="true">—</span>
              <label className="filter-field"><span>{t('search.price_max')}, $</span><input type="number" inputMode="numeric" min="0" placeholder="1000+" value={filters.price_max} onChange={event => setFilter('price_max', event.target.value)} aria-invalid={invalidPrice} /></label>
            </div>
            {invalidPrice && <p className="filter-error" id={formId + '-price-error'} role="alert">{t('search.experience.price_error')}</p>}
          </FilterSection>
          <FilterSection icon={<Home size={17} />} title={t('search.apartment_type')} defaultOpen>
            <div className="filter-type-options">
              {[['', 'apartment_type_all', Building2], ['full_unit', 'apartment_type_entire', Home], ['shared_room', 'apartment_type_per_bed', BedDouble]].map(([value, label, Icon]) => (
                <Choice key={value} active={filters.rental_type === value} icon={<Icon size={15} />} onClick={() => setFilter('rental_type', value)}>{t('search.' + label)}</Choice>
              ))}
            </div>
            <span className="filter-field-label">{t('search.rooms')}</span>
            <div className="filter-room-options">
              {['', '1', '2', '3', '4'].map(value => (
                <Choice key={value} active={String(filters.rooms_count) === value} onClick={() => setFilter('rooms_count', value)}>{value || t('search.any')}</Choice>
              ))}
            </div>
          </FilterSection>
          <FilterSection icon={<Users size={17} />} title={t('search.gender')} meta={t('search.available_spots')}>
            <div className="filter-gender-options">
              {[['', 'gender_all'], ['male', 'gender_male'], ['female', 'gender_female'], ['mixed', 'gender_mixed']].map(([value, label]) => (
                <Choice key={value} active={filters.target_gender === value} onClick={() => setFilter('target_gender', value)}>{t('search.' + label)}</Choice>
              ))}
            </div>
            <label className="filter-field"><span>{t('search.available_spots')}</span><input type="number" inputMode="numeric" min="0" value={filters.available_spaces} placeholder="0" onChange={event => setFilter('available_spaces', event.target.value)} /></label>
          </FilterSection>
          <FilterSection icon={<Sparkles size={17} />} title={t('search.amenities')} meta={selectedAmenities > 0 ? t('search.experience.selected', { count: selectedAmenities }) : undefined}>
            <div className="filter-amenities">
              {amenities.map(([key, label, Icon]) => (
                <label key={key} className={'filter-amenity' + (filters.amenities?.[key] ? ' active' : '')}>
                  <input type="checkbox" checked={Boolean(filters.amenities?.[key])} onChange={event => setAmenity(key, event.target.checked)} />
                  <Icon size={16} /><span>{t('search.' + label)}</span><Check size={13} className="filter-check" aria-hidden="true" />
                </label>
              ))}
            </div>
          </FilterSection>
          <label className="filter-ready">
            <span className="filter-ready-icon"><Sparkles size={17} /></span>
            <span><strong>{t('search.move_in')}</strong><small>{t('search.move_in_desc')}</small></span>
            <input type="checkbox" role="switch" checked={Boolean(filters.move_in_ready)} onChange={event => setFilter('move_in_ready', event.target.checked)} />
          </label>
        </div>
        <div className="filter-panel-actions">
          <button type="submit" className="filter-apply" disabled={invalidPrice}><Search size={17} />{t('search.experience.show_results')}</button>
          <button type="button" className="filter-reset" onClick={clearAll}><RotateCcw size={14} />{t('search.clear')}</button>
        </div>
      </form>
    </div>
  )
}
