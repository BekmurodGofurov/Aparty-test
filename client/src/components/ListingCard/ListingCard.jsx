import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import {
  Armchair,
  BadgeCheck,
  ChefHat,
  Droplets,
  Flame,
  Heart,
  Home,
  MapPin,
  Phone,
  Refrigerator,
  Send,
  Snowflake,
  Sparkles,
  Star,
  Tv,
  Users,
  WashingMachine,
  Wifi,
  Zap,
} from 'lucide-react'
import { favoritesService } from '../../services/favoritesService'
import { useAuthStore } from '../../store/authStore'
import './ListingCard.scss'

const FALLBACK_IMG = 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=900&q=80'

const spring = { type: 'spring', stiffness: 340, damping: 28, mass: 0.75 }

export default function ListingCard({ listing, onUnfavorite = null }) {
  const { t } = useTranslation()
  const { user, isAuthenticated } = useAuthStore()
  const accessToken = useAuthStore((s) => s.accessToken)
  const [saved, setSaved] = useState(Boolean(listing.is_favorite))
  const [saving, setSaving] = useState(false)
  const [spotlight, setSpotlight] = useState({ x: 50, y: 20 })

  const isOwnerVerified = listing.owner_verified ?? false
  const isPremium = listing.is_premium || false

  const ownerLabel = listing.owner_role === 'makler'
    ? t('card.makler')
    : listing.owner_role === 'owner'
      ? t('card.owner')
      : t('card.student')

  const roomsText = listing.rooms_count > 0 ? `${listing.rooms_count} ${t('card.rooms')}` : t('card.studio')
  const genderLabel = listing.target_gender === 'male'
    ? t('card.male')
    : listing.target_gender === 'female'
      ? t('card.female')
      : t('card.mixed')

  const amenityIcons = {
    wifi: <Wifi size={15} />,
    gas: <Flame size={15} />,
    water: <Droplets size={15} />,
    ac: <Snowflake size={15} />,
    washer: <WashingMachine size={15} />,
    fridge: <Refrigerator size={15} />,
    kitchenware: <ChefHat size={15} />,
    tv: <Tv size={15} />,
  }

  const visibleAmenities = Object.entries(listing.amenities || {})
    .filter(([, value]) => value)
    .slice(0, 4)

  const rating = typeof listing.rating === 'number' ? listing.rating.toFixed(1) : t('listing.new')
  const phoneLink = listing.owner_phone ? `tel:${String(listing.owner_phone).replace(/\s/g, '')}` : null
  const telegramId = Number(listing.owner_telegram_id)
  const hasLikelyTelegramId = Number.isFinite(telegramId) && telegramId >= 10000 && telegramId < 10000000000
  const telegramLink = listing.owner_telegram_url || (hasLikelyTelegramId ? `tg://user?id=${telegramId}` : null)

  const handleMouseMove = (event) => {
    const bounds = event.currentTarget.getBoundingClientRect()
    setSpotlight({
      x: ((event.clientX - bounds.left) / bounds.width) * 100,
      y: ((event.clientY - bounds.top) / bounds.height) * 100,
    })
  }

  const handleSave = async (event) => {
    event.preventDefault()
    event.stopPropagation()
    if (!accessToken || saving) return

    const previous = saved
    setSaved(!previous)
    setSaving(true)
    try {
      const result = await favoritesService.toggleFavorite(listing.id)
      setSaved(result.status === 'added')
    } catch (error) {
      setSaved(previous)
      console.error('Favorite toggle failed:', error)
    } finally {
      setSaving(false)
    }
  }

  return (
    <motion.article
      className={`listing-card-liquid ${listing.is_premium ? 'is-premium' : ''}`}
      onMouseMove={handleMouseMove}
      style={{ '--spot-x': `${spotlight.x}%`, '--spot-y': `${spotlight.y}%` }}
      whileHover={{ y: -6 }}
      transition={spring}
    >
      <Link to={`/listing/${listing.id}`} className="card-hit-area" aria-label={`${listing.district}, ${listing.region}`}>
        <div className="card-ambient" aria-hidden="true" />

        <div className="card-media">
          <motion.img
            src={listing.images?.[0] || FALLBACK_IMG}
            alt={listing.address || "E'lon rasmi"}
            loading="lazy"
            onError={(event) => { event.currentTarget.src = FALLBACK_IMG }}
            whileHover={{ scale: 1.075 }}
            transition={{ duration: 0.75, ease: [0.16, 1, 0.3, 1] }}
          />
          <div className="media-vignette" />
          <div className="media-reflection" />

          <div className="media-top">
            {listing.is_premium && (
              <motion.span
                className="premium-chip"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={spring}
              >
                <Sparkles size={12} />
                {t('listing.premium')}
              </motion.span>
            )}
            <button
              type="button"
              className={`save-orb ${saved ? 'saved' : ''}`}
              onClick={handleSave}
              disabled={saving}
              aria-label={t('listing.save')}
            >
              <Heart size={16} fill={saved ? 'currentColor' : 'none'} />
            </button>
          </div>

          <div className="price-glass">
            <span className="price-value">${listing.price}</span>
            <span className="price-unit">{t('card.per_month')}</span>
          </div>
        </div>

        <div className="card-body">
          <div className="location-row">
            <span className="location-icon"><MapPin size={15} /></span>
            <span>{listing.district}, {listing.region}</span>
            <span className="rating-pill">
              <Star size={13} fill="currentColor" />
              {rating}
            </span>
          </div>

          <div className="title-row">
            <h3>{listing.address || `${listing.rooms_count} ${t('card.rooms')} kvartira`}</h3>
          </div>

          <div className="metrics-row">
            <span><Home size={15} /> {listing.rooms_count} {t('card.rooms')}</span>
            <span><Users size={15} /> {listing.available_spaces} {t('card.free')}</span>
            <span><Zap size={15} /> {genderLabel}</span>
          </div>

          <div className="amenity-strip">
            {visibleAmenities.map(([key]) => (
              <span key={key} title={key}>
                {amenityIcons[key] || <Armchair size={15} />}
              </span>
            ))}
            {visibleAmenities.length === 0 && <span><Armchair size={15} /></span>}
          </div>

          <div className="card-footer">
            <div className="owner-cluster">
              <span className="owner-avatar">{listing.owner_full_name?.charAt(0)?.toUpperCase() || 'A'}</span>
              <span>
                <strong>{listing.owner_full_name || ownerLabel}</strong>
                <small>{ownerLabel}</small>
              </span>
            </div>
            {listing.owner_verified && (
              <span className="verified-mark">
                <BadgeCheck size={15} />
              </span>
            )}
          </div>
          <div className="card-contact-actions">
            <button
              type="button"
              disabled={!phoneLink}
              onClick={(event) => {
                event.preventDefault()
                event.stopPropagation()
                if (phoneLink) window.location.assign(phoneLink)
              }}
              aria-label="Telefon qilish"
            >
              <Phone size={14} />
              Contact
            </button>
            <button
              type="button"
              disabled={!telegramLink}
              onClick={(event) => {
                event.preventDefault()
                event.stopPropagation()
                if (telegramLink) window.location.assign(telegramLink)
              }}
              aria-label="Telegram orqali yozish"
            >
              <Send size={14} />
              Telegram
            </button>
          </div>
        </div>
      </Link>
    </motion.article>
  )
}
