import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Armchair, BadgeCheck, ChefHat, Droplets, Flame, Heart, Home, MapPin, Phone, Refrigerator, Send, Snowflake, Sparkles, Tv, Users, WashingMachine, Wifi, Zap } from 'lucide-react'
import { favoritesService } from '../../services/favoritesService'
import { useAuthStore } from '../../store/authStore'
import { FallbackImage } from '../ui/FallbackImage'
import './ListingCard.scss'

const AMENITY_ICONS = { wifi: Wifi, gas: Flame, water: Droplets, air_conditioner: Snowflake, washing_machine: WashingMachine, fridge: Refrigerator, kitchen: ChefHat, tv: Tv }
const AMENITY_LABELS = { air_conditioner: 'ac', washing_machine: 'washer' }

export default function ListingCard({ listing }) {
  const { t } = useTranslation()
  const accessToken = useAuthStore(state => state.accessToken)
  const [saved, setSaved] = useState(Boolean(listing.is_favorite))
  const [saving, setSaving] = useState(false)
  const ownerLabel = t('card.' + (['makler', 'owner'].includes(listing.owner_role) ? listing.owner_role : 'student'))
  const genderLabel = t('card.' + (['male', 'female'].includes(listing.target_gender) ? listing.target_gender : 'mixed'))
  const visibleAmenities = Object.entries(listing.amenities || {}).filter(([, value]) => value).slice(0, 4)
  const phoneLink = listing.owner_phone ? 'tel:' + String(listing.owner_phone).replace(/\s/g, '') : null
  const telegramLink = listing.owner_telegram_url || null
  const detailLink = '/listing/' + listing.id
  const title = listing.address || listing.rooms_count + ' ' + t('card.rooms')

  const handleSave = async () => {
    if (!accessToken || saving) return
    const previous = saved
    setSaved(!previous)
    setSaving(true)
    try {
      const result = await favoritesService.toggleFavorite(listing.id)
      setSaved(result.status === 'added')
    } catch {
      setSaved(previous)
    } finally {
      setSaving(false)
    }
  }

  return (
    <article className={'listing-card-liquid' + (listing.is_premium ? ' is-premium' : '')}>
      <div className="card-media">
        <Link to={detailLink} className="card-image-link" aria-label={title}><FallbackImage src={listing.images?.[0]} alt={title} loading="lazy" decoding="async" /></Link>
        <div className="media-vignette" aria-hidden="true" />
        <div className="media-top">
          {listing.is_premium && <span className="premium-chip"><Sparkles size={12} />{t('listing.premium')}</span>}
          <button type="button" className={'save-orb' + (saved ? ' saved' : '')} onClick={handleSave} disabled={saving || !accessToken} aria-label={t('listing.save')} aria-pressed={saved} title={!accessToken ? t('auth.login_title') : t('listing.save')}><Heart size={16} fill={saved ? 'currentColor' : 'none'} /></button>
        </div>
        <div className="price-glass"><span className="price-value">{'$'}{listing.price}</span><span className="price-unit">{t('card.per_month')}</span></div>
      </div>
      <div className="card-body">
        <Link to={detailLink} className="card-property-link">
          <div className="location-row"><MapPin size={13} /><span>{listing.district}, {listing.region}</span></div><h3>{title}</h3>
        </Link>
        <div className="metrics-row"><span><Home size={13} />{listing.rooms_count} {t('card.rooms')}</span><span><Users size={13} />{listing.available_spaces} {t('card.free')}</span><span><Zap size={13} />{genderLabel}</span></div>
        <div className="amenity-strip">
          {visibleAmenities.map(([key]) => { const Icon = AMENITY_ICONS[key] || Armchair; return <span key={key} title={t('search.' + (AMENITY_LABELS[key] || key))}><Icon size={14} /></span> })}
          {visibleAmenities.length === 0 && <span><Armchair size={14} /></span>}
        </div>
        <div className="card-footer">
          <div className="owner-cluster"><span className="owner-avatar">{listing.owner_full_name?.charAt(0)?.toUpperCase() || 'A'}</span><span><strong>{listing.owner_full_name || ownerLabel}</strong><small>{ownerLabel}</small></span></div>
          {listing.owner_verified && <span className="verified-mark" title={t('card.verified')}><BadgeCheck size={17} /></span>}
        </div>
        <div className="card-contact-actions">
          {phoneLink ? <a href={phoneLink}><Phone size={14} />{t('listing.contact')}</a> : <span aria-disabled="true"><Phone size={14} />{t('listing.contact')}</span>}
          {telegramLink ? <a href={telegramLink} target="_blank" rel="noopener noreferrer"><Send size={14} />Telegram</a> : <span aria-disabled="true"><Send size={14} />Telegram</span>}
        </div>
      </div>
    </article>
  )
}
