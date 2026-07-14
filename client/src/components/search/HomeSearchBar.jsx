import { useState } from 'react'
import { MapPin, Home, DollarSign, Search, Sparkles, Users } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { REGIONS_DATA } from '../../data/regions'
import { PremiumSelect } from '../ui/PremiumSelect'
import './HomeSearchBar.scss'

export function HomeSearchBar() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    region: '',
    district: '',
    rooms_count: '',
    price_min: '',
    price_max: ''
  })

  const handleSearch = () => {
    const p = new URLSearchParams()
    if (form.region) p.append('region', form.region)
    if (form.district) p.append('district', form.district)
    if (form.rooms_count) p.append('rooms_count', form.rooms_count)
    if (form.price_min) p.append('price_min', form.price_min)
    if (form.price_max) p.append('price_max', form.price_max)
    navigate(`/search?${p}`)
  }

  const districts = form.region ? REGIONS_DATA[form.region] || [] : []

  return (
    <div className="home-search-container">
      <div className="search-grid">
        {/* VILOYAT */}
        <div className="search-box">
          <div className="box-label">
            <MapPin size={14} />
            <span>VILOYAT</span>
          </div>
          <div className="box-input">
            <PremiumSelect
              value={form.region}
              onChange={(val) => setForm({ ...form, region: val, district: '' })}
              placeholder="Barcha viloyatlar"
              options={[
                { value: '', label: 'Barcha viloyatlar' },
                ...Object.keys(REGIONS_DATA).map(r => ({ value: r, label: r }))
              ]}
            />
          </div>
        </div>

        {/* TUMAN */}
        <div className="search-box">
          <div className="box-label">
            <Home size={14} />
            <span>TUMAN</span>
          </div>
          <div className="box-input">
            <PremiumSelect
              value={form.district}
              onChange={(val) => setForm({ ...form, district: val })}
              disabled={!form.region}
              placeholder={form.region ? 'Barcha tumanlar' : 'Avval viloyat tanlang'}
              options={[
                { value: '', label: form.region ? 'Barcha tumanlar' : 'Avval viloyat tanlang' },
                ...districts.map(d => ({ value: d, label: d }))
              ]}
            />
          </div>
        </div>

        {/* XONALAR SONI */}
        <div className="search-box">
          <div className="box-label">
            <Users size={14} />
            <span>XONALAR SONI</span>
          </div>
          <div className="box-input">
            <PremiumSelect
              value={form.rooms_count}
              onChange={(val) => setForm({ ...form, rooms_count: val })}
              placeholder="Istalgan"
              options={[
                { value: '', label: 'Istalgan' },
                { value: '1', label: '1 xona' },
                { value: '2', label: '2 xona' },
                { value: '3', label: '3 xona' },
                { value: '4', label: '4+ xona' }
              ]}
            />
          </div>
        </div>

        {/* NARX */}
        <div className="search-box">
          <div className="box-label">
            <DollarSign size={14} />
            <span>NARX ($/OY)</span>
          </div>
          <div className="box-input price-inputs">
            <input 
              type="number" 
              placeholder="Min" 
              value={form.price_min}
              onChange={(e) => setForm({...form, price_min: e.target.value})}
            />
            <span className="separator">—</span>
            <input 
              type="number" 
              placeholder="Max" 
              value={form.price_max}
              onChange={(e) => setForm({...form, price_max: e.target.value})}
            />
          </div>
        </div>
      </div>

      <div className="search-buttons">
        <button className="btn-search-main" onClick={handleSearch}>
          <Search size={18} />
          Qidiruvni boshlash
        </button>
        <button className="btn-ai-search" onClick={() => document.querySelector('.chat-toggle-btn')?.click()}>
          <Sparkles size={18} />
          AI yordamchidan so'rash
        </button>
      </div>
    </div>
  )
}
