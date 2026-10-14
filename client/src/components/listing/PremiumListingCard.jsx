import { useState } from 'react'
import { motion } from 'framer-motion'
import { Heart, MapPin, Zap } from 'lucide-react'
import { Badge } from '../ui/PremiumComponents'
import { FallbackImage } from '../ui/FallbackImage'
import { favoritesService } from '../../services/favoritesService'
import { useAuthStore } from '../../store/authStore'
import './PremiumListingCard.scss'

export function PremiumListingCard({
  id,
  image,
  title,
  location,
  price,
  rooms,
  isPremium = false,
  isVerified = false,
  isFavorite = false,
  onFavoriteToggle,
  onClick,
}) {
  const accessToken = useAuthStore((s) => s.accessToken)
  const [favorited, setFavorited] = useState(isFavorite)
  const [loadingFav, setLoadingFav] = useState(false)

  const toggleFav = async (event) => {
    event.stopPropagation()
    if (!accessToken) return

    setLoadingFav(true)
    try {
      const res = await favoritesService.toggleFavorite(id)
      setFavorited(res.status === 'added')
      onFavoriteToggle?.(id, res.status === 'added')
    } catch (err) {
      console.error('Favorite toggle failed:', err)
    } finally {
      setLoadingFav(false)
    }
  }

  return (
    <motion.div
      className="premium-listing-card glass-card"
      onClick={onClick}
    >
      <div className="card-image-wrapper">
        <FallbackImage
          src={image}
          alt={title}
          className="card-image"
          loading="lazy"
        />

        <div className="card-image-overlay">
          <button className="overlay-btn" type="button">
            <span>Galereya</span>
          </button>
        </div>

        <div className="card-badges">
          {isPremium && <Badge variant="premium">Premium</Badge>}
          {isVerified && <Badge variant="success">Tasdiqlangan</Badge>}
        </div>

        <motion.button
          className={`favorite-btn ${favorited ? 'active' : ''} ${loadingFav ? 'loading' : ''}`}
          onClick={toggleFav}
          whileTap={{ scale: 0.9 }}
          disabled={loadingFav}
          type="button"
        >
          <Heart size={20} fill={favorited ? 'currentColor' : 'none'} />
        </motion.button>
      </div>

      <div className="card-content">
        <h3 className="card-title">{title}</h3>

        <div className="card-location">
          <MapPin size={16} />
          <span>{location}</span>
        </div>

        <div className="card-quick-info">
          <span className="info-item">
            <span>{rooms} xona</span>
          </span>
        </div>

        <div className="card-footer">
          <div className="price-section">
            <span className="price-label">Narx</span>
            <span className="price-value">${Number(price || 0).toLocaleString()}</span>
            <span className="price-period">/ oy</span>
          </div>
          <motion.button
            className="card-cta-btn"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="button"
          >
            <Zap size={18} />
          </motion.button>
        </div>
      </div>
    </motion.div>
  )
}
