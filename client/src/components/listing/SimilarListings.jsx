import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { searchListings } from '../../services/listingService'
import { FallbackImage } from '../ui/FallbackImage'

const SIMILAR_COUNT = 4
const SPRING = { type: 'spring', stiffness: 340, damping: 28, mass: 0.75 }

// Other active listings in the same district (or region when the district is unknown).
export function SimilarListings({ listing }) {
  const { t } = useTranslation()
  const [items, setItems] = useState([])

  useEffect(() => {
    let cancelled = false
    const area = listing.district ? { district: listing.district } : { region: listing.region }
    searchListings(area, 1, SIMILAR_COUNT + 1)
      .then((data) => {
        if (cancelled) return
        setItems((data.listings || []).filter((item) => item.id !== listing.id).slice(0, SIMILAR_COUNT))
      })
      .catch(() => { if (!cancelled) setItems([]) })
    return () => { cancelled = true }
  }, [listing.id, listing.district, listing.region])

  if (items.length === 0) return null

  return (
    <motion.section
      className="similar-section similar-section--full"
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={SPRING}
    >
      <div className="section-heading">
        <span>{t('listing.explore')}</span>
        <h2>{t('listing.similar_listings')}</h2>
      </div>
      <div className="similar-grid">
        {items.map((item) => (
          <Link className="similar-card" to={`/listing/${item.id}`} key={item.id}>
            <FallbackImage src={item.images?.[0]} fallback={null} alt="" loading="lazy" decoding="async" />
            <div>
              <strong>{item.address || item.title}</strong>
              <small>{[item.district, item.region].filter(Boolean).join(', ')}</small>
              <span>${item.price} / oy</span>
            </div>
          </Link>
        ))}
      </div>
    </motion.section>
  )
}
