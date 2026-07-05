import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Bath,
  BedDouble,
  Building2,
  Check,
  ChevronDown,
  ChefHat,
  DollarSign,
  Droplets,
  Flame,
  Home,
  MapPin,
  Refrigerator,
  RotateCcw,
  Search,
  SlidersHorizontal,
  Snowflake,
  Sparkles,
  Tv,
  WashingMachine,
  Wifi,
  X,
  Zap,
} from 'lucide-react'
import { RegionSelect } from './RegionSelect'
import { REGIONS_DATA } from '../../data/regions'
import './FilterPanel.scss'

const spring = { type: 'spring', stiffness: 420, damping: 34, mass: 0.8 }

const sectionVariants = {
  hidden: { height: 0, opacity: 0, filter: 'blur(6px)' },
  visible: { height: 'auto', opacity: 1, filter: 'blur(0px)' },
}

function AccordionSection({ icon, title, meta, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <motion.section
      className={`lux-filter-section ${open ? 'is-open' : ''}`}
      layout
      transition={spring}
    >
      <button
        className="lux-section-trigger"
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <span className="lux-section-icon">{icon}</span>
        <span className="lux-section-copy">
          <strong>{title}</strong>
          {meta && <small>{meta}</small>}
        </span>
        <motion.span className="lux-chevron" animate={{ rotate: open ? 180 : 0 }} transition={spring}>
          <ChevronDown size={18} />
        </motion.span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            className="lux-section-body"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  )
}

function PillButton({ active, icon, label, onClick }) {
  return (
    <motion.button
      type="button"
      className={`lux-pill ${active ? 'active' : ''}`}
      onClick={onClick}
      whileHover={{ y: -2, scale: 1.015 }}
      whileTap={{ scale: 0.97 }}
      transition={spring}
    >
      {active && <motion.span className="lux-pill-shine" transition={spring} />}
      {icon && <span className="lux-pill-icon">{icon}</span>}
      <span>{label}</span>
    </motion.button>
  )
}

function AmenityButton({ active, icon, label, onClick }) {
  return (
    <motion.button
      type="button"
      className={`lux-amenity ${active ? 'active' : ''}`}
      onClick={onClick}
      whileHover={{ y: -3 }}
      whileTap={{ scale: 0.98 }}
      transition={spring}
    >
      <span className="lux-amenity-check">{active && <Check size={13} />}</span>
      <span className="lux-amenity-icon">{icon}</span>
      <span className="lux-amenity-label">{label}</span>
    </motion.button>
  )
}

function ToggleCard({ active, icon, title, desc, onClick }) {
  return (
    <motion.button
      type="button"
      className={`lux-toggle-card ${active ? 'active' : ''}`}
      onClick={onClick}
      whileHover={{ y: -3 }}
      whileTap={{ scale: 0.985 }}
      transition={spring}
    >
      <span className="lux-toggle-icon">{icon}</span>
      <span className="lux-toggle-copy">
        <strong>{title}</strong>
        <small>{desc}</small>
      </span>
      <span className="lux-switch" aria-hidden="true">
        <motion.span className="lux-switch-dot" animate={{ x: active ? 22 : 0 }} transition={spring} />
      </span>
    </motion.button>
  )
}

export function FilterPanel({
  filters,
  setFilter,
  setAmenity,
  applyFilters,
  clearAll,
  onClose,
  activeFilterCount = 0,
}) {
  const { t } = useTranslation()
  const [smartQuery, setSmartQuery] = useState('')

  const amenities = [
    { key: 'wifi', label: t('search.wifi'), icon: <Wifi size={17} /> },
    { key: 'gaz', label: t('search.gas'), icon: <Flame size={17} /> },
    { key: 'suv', label: t('search.water'), icon: <Droplets size={17} /> },
    { key: 'tv', label: t('search.tv'), icon: <Tv size={17} /> },
    { key: 'konditsioner', label: t('search.ac'), icon: <Snowflake size={17} /> },
    { key: 'kir_mashina', label: t('search.washer'), icon: <WashingMachine size={17} /> },
    { key: 'holodilnik', label: t('search.fridge'), icon: <Refrigerator size={17} /> },
    { key: 'oshxona_jihozi', label: t('search.kitchen'), icon: <ChefHat size={17} /> },
  ]

  const searchHint = useMemo(() => {
    if (filters.tuman) return filters.tuman
    if (filters.viloyat) return filters.viloyat
    return t('search.region_placeholder')
  }, [filters.tuman, filters.viloyat, t])

  const priceMax = Number(filters.narx_max || 1000)
  const priceMin = Number(filters.narx_min || 0)
  const pricePercent = Math.min(100, Math.max(0, (priceMax / 1000) * 100))

  const handleSmartSearch = (value) => {
    setSmartQuery(value)
    const normalized = value.trim().toLowerCase()
    if (!normalized) return

    const matchedRegion = Object.keys(REGIONS_DATA).find((region) => region.toLowerCase().includes(normalized))
    if (matchedRegion) {
      setFilter('viloyat', matchedRegion)
      return
    }

    Object.entries(REGIONS_DATA).some(([region, districts]) => {
      const district = districts.find((item) => item.toLowerCase().includes(normalized))
      if (!district) return false
      setFilter('viloyat', region)
      setFilter('tuman', district)
      return true
    })
  }

  return (
    <motion.div
      className="filter-panel-inner"
      initial={{ opacity: 0, y: 18, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="lux-panel-orbit" aria-hidden="true" />

      <div className="lux-panel-head">
        <div>
          <span className="lux-kicker">
            <Sparkles size={13} />
            {t('search.filters')}
          </span>
          <h2>Smart match</h2>
        </div>
        <div className="lux-head-actions">
          {activeFilterCount > 0 && <span className="lux-active-badge">{activeFilterCount}</span>}
          {onClose && (
            <button className="lux-close-btn" type="button" onClick={onClose} aria-label="Close filters">
              <X size={18} />
            </button>
          )}
        </div>
      </div>

      <form onSubmit={(event) => applyFilters(event)} className="lux-filter-form">
        <motion.div className="lux-search-card" whileHover={{ y: -3 }} transition={spring}>
          <div className="lux-search-glow" aria-hidden="true" />
          <Search className="lux-search-icon" size={21} />
          <input
            type="search"
            value={smartQuery}
            onChange={(event) => handleSmartSearch(event.target.value)}
            placeholder={`Search ${searchHint}`}
            aria-label="Search by region or district"
          />
          <motion.span
            className="lux-search-pulse"
            animate={{ opacity: smartQuery ? 1 : 0.45, scale: smartQuery ? 1.08 : 1 }}
            transition={spring}
          >
            <Zap size={15} />
          </motion.span>
        </motion.div>

        <AccordionSection
          icon={<MapPin size={18} />}
          title={t('search.location', { defaultValue: t('search.region') })}
          meta={filters.tuman || filters.viloyat || t('search.district_placeholder')}
          defaultOpen
        >
          <RegionSelect
            regions={REGIONS_DATA}
            selectedRegion={filters.viloyat}
            selectedDistrict={filters.tuman}
            onRegionChange={(region) => setFilter('viloyat', region)}
            onDistrictChange={(district) => setFilter('tuman', district)}
            regionPlaceholder={t('search.region_placeholder')}
            districtPlaceholder={t('search.district_placeholder')}
          />
        </AccordionSection>

        <AccordionSection
          icon={<DollarSign size={18} />}
          title={t('search.price')}
          meta={`$${priceMin} - $${priceMax}`}
          defaultOpen
        >
          <div className="lux-price-card">
            <div className="lux-price-values">
              <motion.span layout>${priceMin}</motion.span>
              <motion.span layout>${priceMax}+</motion.span>
            </div>
            <div className="lux-slider-shell" style={{ '--range-progress': `${pricePercent}%` }}>
              <input
                type="range"
                min="0"
                max="1000"
                step="10"
                value={priceMax}
                onChange={(event) => setFilter('narx_max', event.target.value)}
                aria-label="Maximum price"
              />
            </div>
            <div className="lux-price-inputs">
              <label>
                <small>{t('search.price_min')}</small>
                <input
                  type="number"
                  min="0"
                  value={filters.narx_min}
                  placeholder="0"
                  onChange={(event) => setFilter('narx_min', event.target.value)}
                />
              </label>
              <label>
                <small>{t('search.price_max')}</small>
                <input
                  type="number"
                  min="0"
                  value={filters.narx_max}
                  placeholder="1000"
                  onChange={(event) => setFilter('narx_max', event.target.value)}
                />
              </label>
            </div>
          </div>
        </AccordionSection>

        <AccordionSection icon={<Home size={18} />} title={t('search.apartment_type')} meta={t('search.rooms')}>
          <div className="lux-pill-grid">
            {[
              { id: '', label: t('search.apartment_type_all'), icon: <Building2 size={16} /> },
              { id: 'bomboq', label: t('search.apartment_type_entire'), icon: <Home size={16} /> },
              { id: 'yotoqxona', label: t('search.apartment_type_per_bed'), icon: <BedDouble size={16} /> },
            ].map((type) => (
              <PillButton
                key={type.id || 'all'}
                active={filters.apartmentType === type.id}
                icon={type.icon}
                label={type.label}
                onClick={() => setFilter('apartmentType', type.id)}
              />
            ))}
          </div>

          <div className="lux-room-row">
            {['1', '2', '3', '4'].map((value) => (
              <PillButton
                key={value}
                active={String(filters.xonalar_soni) === value}
                label={value === '4' ? '4+' : value}
                onClick={() => setFilter('xonalar_soni', String(filters.xonalar_soni) === value ? '' : value)}
              />
            ))}
          </div>
        </AccordionSection>

        <AccordionSection icon={<Bath size={18} />} title={t('search.gender')} meta={t('search.available_spots')}>
          <div className="lux-pill-grid compact">
            {[
              { id: '', label: t('search.gender_all') },
              { id: 'erkak', label: t('search.gender_male') },
              { id: 'ayol', label: t('search.gender_female') },
              { id: 'aralash', label: t('search.gender_mixed') },
            ].map((item) => (
              <PillButton
                key={item.id || 'all-gender'}
                active={filters.jins === item.id}
                label={item.label}
                onClick={() => setFilter('jins', item.id)}
              />
            ))}
          </div>
          <label className="lux-number-field">
            <span>{t('search.available_spots')}</span>
            <input
              type="number"
              min="0"
              value={filters.bosh_joy}
              placeholder="0"
              onChange={(event) => setFilter('bosh_joy', event.target.value)}
            />
          </label>
        </AccordionSection>

        <AccordionSection icon={<SlidersHorizontal size={18} />} title={t('search.amenities')} meta="Essentials">
          <div className="lux-amenities-grid">
            {amenities.map(({ key, label, icon }) => (
              <AmenityButton
                key={key}
                active={Boolean(filters.qulayliklar?.[key])}
                icon={icon}
                label={label}
                onClick={() => setAmenity(key, !filters.qulayliklar?.[key])}
              />
            ))}
          </div>
        </AccordionSection>

        <ToggleCard
          active={Boolean(filters.kiring_yashaing)}
          icon={<Sparkles size={18} />}
          title={t('search.move_in')}
          desc={t('search.move_in_desc')}
          onClick={() => setFilter('kiring_yashaing', !filters.kiring_yashaing)}
        />

        <div className="lux-panel-buttons">
          <motion.button
            type="submit"
            className="lux-apply-btn"
            whileHover={{ y: -3, scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            transition={spring}
          >
            <span>{t('search.apply')}</span>
            <Search size={18} />
          </motion.button>
          <motion.button
            type="button"
            className="lux-reset-btn"
            onClick={clearAll}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
            transition={spring}
          >
            <RotateCcw size={16} />
            <span>{t('search.clear')}</span>
          </motion.button>
        </div>
      </form>
    </motion.div>
  )
}
