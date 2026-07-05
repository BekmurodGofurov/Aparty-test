import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { MapPin, DollarSign, Home, Users, Search, ChevronDown } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import './FilterBar.scss'

export function FilterBar({ onSearch, initialFilters = {} }) {
  const { t } = useTranslation()
  const [filters, setFilters] = useState({
    viloyat: initialFilters.viloyat || '',
    narx_max: initialFilters.narx_max || '',
    xonalar_soni: initialFilters.xonalar_soni || '',
    apartmentType: initialFilters.apartmentType || '',
  })
  
  const [activeDropdown, setActiveDropdown] = useState(null)
  const containerRef = useRef(null)

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setActiveDropdown(null)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleApply = () => {
    setActiveDropdown(null)
    onSearch?.(filters)
  }

  const toggleDropdown = (name) => {
    setActiveDropdown(activeDropdown === name ? null : name)
  }

  return (
    <div className="filter-bar-container" ref={containerRef}>
      <div className="filter-bar-inner">
        
        {/* ── LOCATION ──────────────────────────────── */}
        <div className={`filter-item ${activeDropdown === 'location' ? 'active' : ''}`} onClick={() => toggleDropdown('location')}>
          <div className="filter-icon-box"><MapPin size={18} /></div>
          <div className="filter-text">
            <span className="filter-label">{t('search.location')}</span>
            <span className="filter-value">{filters.viloyat || t('search.anywhere')}</span>
          </div>
          <ChevronDown size={14} className="chevron" />
        </div>

        <div className="divider" />

        {/* ── PRICE ─────────────────────────────────── */}
        <div className={`filter-item ${activeDropdown === 'price' ? 'active' : ''}`} onClick={() => toggleDropdown('price')}>
          <div className="filter-icon-box"><DollarSign size={18} /></div>
          <div className="filter-text">
            <span className="filter-label">{t('search.price')}</span>
            <span className="filter-value">{filters.narx_max ? `$${filters.narx_max}` : t('search.any_price')}</span>
          </div>
          <ChevronDown size={14} className="chevron" />
        </div>

        <div className="divider" />

        {/* ── ROOMS ─────────────────────────────────── */}
        <div className={`filter-item ${activeDropdown === 'rooms' ? 'active' : ''}`} onClick={() => toggleDropdown('rooms')}>
          <div className="filter-icon-box"><Home size={18} /></div>
          <div className="filter-text">
            <span className="filter-label">{t('search.rooms')}</span>
            <span className="filter-value">{filters.xonalar_soni ? `${filters.xonalar_soni} ${t('search.rooms')}` : t('search.any_rooms')}</span>
          </div>
          <ChevronDown size={14} className="chevron" />
        </div>

        {/* ── SEARCH BUTTON ─────────────────────────── */}
        <button className="search-trigger-btn" onClick={handleApply}>
          <Search size={20} strokeWidth={3} />
          <span className="btn-text">{t('search.search_btn')}</span>
        </button>

        {/* ── DROPDOWNS ─────────────────────────────── */}
        <AnimatePresence>
          {activeDropdown && (
            <motion.div 
              className="filter-dropdown-portal"
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
            >
              {activeDropdown === 'location' && (
                <div className="dropdown-content">
                  <h3>Hududni tanlang</h3>
                  <div className="options-grid">
                    {['Toshkent', 'Samarqand', 'Andijon', 'Farg\'ona'].map(loc => (
                      <button 
                        key={loc} 
                        className={`opt-btn ${filters.viloyat === loc ? 'selected' : ''}`}
                        onClick={() => setFilters({...filters, viloyat: loc})}
                      >
                        {loc}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {activeDropdown === 'price' && (
                <div className="dropdown-content">
                  <h3>Maksimal narx</h3>
                  <div className="price-inputs">
                    {[200, 500, 1000, 2000].map(p => (
                      <button 
                        key={p} 
                        className={`opt-btn ${filters.narx_max === String(p) ? 'selected' : ''}`}
                        onClick={() => setFilters({...filters, narx_max: String(p)})}
                      >
                        ${p}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {activeDropdown === 'rooms' && (
                <div className="dropdown-content">
                  <h3>Xonalar soni</h3>
                  <div className="rooms-row">
                    {['1', '2', '3', '4+'].map(r => (
                      <button 
                        key={r} 
                        className={`opt-btn ${filters.xonalar_soni === r ? 'selected' : ''}`}
                        onClick={() => setFilters({...filters, xonalar_soni: r})}
                      >
                        {r}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
