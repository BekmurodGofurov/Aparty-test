import { useState } from 'react'
import { DollarSign, Home, MapPin, MapPinned, Search, Users } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { REGIONS_DATA } from '../../data/regions'
import './HomeSearchBar.scss'

export function HomeSearchBar() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [form, setForm] = useState({ region: '', district: '', rooms_count: '', price_min: '', price_max: '' })
  const districts = form.region ? REGIONS_DATA[form.region] || [] : []

  const searchParams = () => {
    const params = new URLSearchParams()
    Object.entries(form).forEach(([key, value]) => { if (value !== '') params.set(key, value) })
    return params.toString()
  }

  const handleSearch = (event) => {
    event.preventDefault()
    navigate('/search?' + searchParams())
  }

  return (
    <form className="home-search-container" onSubmit={handleSearch} aria-label={t('home.experience.search_form')}>
      <div className="search-grid">
        <label className="search-box">
          <span className="box-label"><MapPin size={13} aria-hidden="true" />{t('search.region', 'Hudud')}</span>
          <select value={form.region} onChange={(event) => setForm({ ...form, region: event.target.value, district: '' })}>
            <option value="">{t('home.experience.all_regions')}</option>
            {Object.keys(REGIONS_DATA).map(region => <option key={region} value={region}>{region}</option>)}
          </select>
        </label>
        <label className="search-box">
          <span className="box-label"><Home size={13} aria-hidden="true" />{t('home.experience.district')}</span>
          <select value={form.district} onChange={(event) => setForm({ ...form, district: event.target.value })} disabled={!form.region}>
            <option value="">{form.region ? t('home.experience.all_districts') : t('home.experience.choose_region')}</option>
            {districts.map(district => <option key={district} value={district}>{district}</option>)}
          </select>
        </label>
        <label className="search-box">
          <span className="box-label"><Users size={13} aria-hidden="true" />{t('search.rooms', 'Xonalar')}</span>
          <select value={form.rooms_count} onChange={(event) => setForm({ ...form, rooms_count: event.target.value })}>
            <option value="">{t('home.experience.any_rooms')}</option>
            {['1', '2', '3', '4'].map(count => <option key={count} value={count}>{count === '4' ? '4+' : count}</option>)}
          </select>
        </label>
        <fieldset className="search-box price-box">
          <legend className="box-label"><DollarSign size={13} aria-hidden="true" />{t('home.experience.monthly_price')}</legend>
          <div className="price-inputs">
            <input type="number" min="0" inputMode="numeric" placeholder={t('search.min', 'Min')} aria-label={t('home.experience.minimum_price')} value={form.price_min} onChange={(event) => setForm({ ...form, price_min: event.target.value })} />
            <span aria-hidden="true">–</span>
            <input type="number" min="0" inputMode="numeric" placeholder={t('search.max', 'Max')} aria-label={t('home.experience.maximum_price')} value={form.price_max} onChange={(event) => setForm({ ...form, price_max: event.target.value })} />
          </div>
        </fieldset>
        <button type="submit" className="btn-search-main"><Search size={19} aria-hidden="true" /><span>{t('home.experience.search_action')}</span></button>
      </div>
      <div className="search-caption">
        <span><span className="search-caption-dot" />{t('home.experience.search_caption')}</span>
        <button type="button" className="btn-map-search" onClick={() => navigate('/map')}>
          <MapPinned size={13} aria-hidden="true" />{t('home.experience.map_action')}
        </button>
      </div>
    </form>
  )
}
