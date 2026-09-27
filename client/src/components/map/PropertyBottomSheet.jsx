import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  BedDouble,
  ChevronLeft,
  ChevronRight,
  Eye,
  Heart,
  Home,
  MapPin,
  Maximize2,
  Phone,
  X,
} from 'lucide-react'
import { formatDistance } from '../../utils/geo'

export function PropertyBottomSheet({ property, onClose }) {
  const [activeImage, setActiveImage] = useState(0)
  const [favorite, setFavorite] = useState(false)

  const images = useMemo(() => property?.images?.length ? property.images : property ? [property.image] : [], [property])

  useEffect(() => {
    setActiveImage(0)
    setFavorite(false)
  }, [property?.id])

  const nextImage = () => setActiveImage(index => (index + 1) % images.length)
  const prevImage = () => setActiveImage(index => (index - 1 + images.length) % images.length)

  return (
    <AnimatePresence>
      {property && (
        <motion.div
          className="property-modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.aside
            className="property-premium-modal"
            initial={{ y: 36, scale: 0.92, opacity: 0, filter: 'blur(12px)' }}
            animate={{ y: 0, scale: 1, opacity: 1, filter: 'blur(0px)' }}
            exit={{ y: 32, scale: 0.94, opacity: 0, filter: 'blur(10px)' }}
            transition={{ type: 'spring', stiffness: 260, damping: 28 }}
            onClick={event => event.stopPropagation()}
            aria-label="Tanlangan uy ma'lumotlari"
          >
            <button className="sheet-close" type="button" onClick={onClose} aria-label="Yopish">
              <X size={18} />
            </button>
            <button
              className={`sheet-favorite ${favorite ? 'active' : ''}`}
              type="button"
              onClick={() => setFavorite(value => !value)}
              aria-label="Saqlash"
            >
              <Heart size={18} fill={favorite ? 'currentColor' : 'none'} />
            </button>

            <div className="sheet-gallery">
              <img className="sheet-image" src={images[activeImage]} alt={property.title} loading="lazy" />
              <div className="sheet-image-gradient" />
              <div className="sheet-badges">
                {property.badges?.map(badge => <span key={badge}>{badge}</span>)}
              </div>
              {images.length > 1 && (
                <>
                  <button className="gallery-nav prev" type="button" onClick={prevImage} aria-label="Oldingi rasm">
                    <ChevronLeft size={19} />
                  </button>
                  <button className="gallery-nav next" type="button" onClick={nextImage} aria-label="Keyingi rasm">
                    <ChevronRight size={19} />
                  </button>
                  <div className="gallery-dots">
                    {images.map((image, index) => (
                      <button
                        key={image}
                        type="button"
                        className={index === activeImage ? 'active' : ''}
                        onClick={() => setActiveImage(index)}
                        aria-label={`${index + 1}-rasm`}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="sheet-body">
              <div className="sheet-title-row">
                <div>
                  <span className="sheet-kicker">Aparty Premium Map</span>
                  <h2>{property.title}</h2>
                  <p><MapPin size={15} /> {property.address}</p>
                </div>
                <strong>{property.currency}{property.price}<small>/oy</small></strong>
              </div>

              <div className="sheet-signal-row">
                <span><Eye size={16} /> {(property.views || 0).toLocaleString()} ko'rish</span>
                <span><Home size={16} /> {formatDistance(property.distanceKm)}</span>
              </div>

              <div className="sheet-stats">
                <span><BedDouble size={17} /> {property.rooms} xona</span>
                {property.area && <span><Maximize2 size={17} /> {property.area} m2</span>}
                {property.floor != null && <span><Home size={17} /> {property.floor}-qavat</span>}
              </div>

              {property.description && <p className="sheet-description">{property.description}</p>}

              <div className="sheet-actions">
                <Link className="sheet-details-btn" to={`/listing/${property.id}`}>
                  Batafsil
                </Link>
                {property.phone && (
                  <a className="sheet-call-btn" href={`tel:${property.phone}`}>
                    <Phone size={18} />
                    Qo'ng'iroq
                  </a>
                )}
              </div>
            </div>
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
