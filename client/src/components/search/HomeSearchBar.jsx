import { useState } from 'react'
import { MapPin, Home, DollarSign, Search, Sparkles, Users } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { REGIONS_DATA } from '../../data/regions'
import { PremiumSelect } from '../ui/PremiumSelect'
import './HomeSearchBar.scss'

export function HomeSearchBar() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    viloyat: '',
    tuman: '',
    xonalar_soni: '',
    narx_min: '',
    narx_max: ''
  })

  const handleSearch = () => {
    const p = new URLSearchParams()
    if (form.viloyat) p.append('viloyat', form.viloyat)
    if (form.tuman) p.append('tuman', form.tuman)
    if (form.xonalar_soni) p.append('xonalar_soni', form.xonalar_soni)
    if (form.narx_min) p.append('narx_min', form.narx_min)
    if (form.narx_max) p.append('narx_max', form.narx_max)
    navigate(`/search?${p}`)
  }

  const districts = form.viloyat ? REGIONS_DATA[form.viloyat] || [] : []

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
              value={form.viloyat}
              onChange={(val) => setForm({ ...form, viloyat: val, tuman: '' })}
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
              value={form.tuman}
              onChange={(val) => setForm({ ...form, tuman: val })}
              disabled={!form.viloyat}
              placeholder={form.viloyat ? 'Barcha tumanlar' : 'Avval viloyat tanlang'}
              options={[
                { value: '', label: form.viloyat ? 'Barcha tumanlar' : 'Avval viloyat tanlang' },
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
              value={form.xonalar_soni}
              onChange={(val) => setForm({ ...form, xonalar_soni: val })}
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
              value={form.narx_min}
              onChange={(e) => setForm({...form, narx_min: e.target.value})}
            />
            <span className="separator">—</span>
            <input 
              type="number" 
              placeholder="Max" 
              value={form.narx_max}
              onChange={(e) => setForm({...form, narx_max: e.target.value})}
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
