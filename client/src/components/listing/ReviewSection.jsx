import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Send, Star, User } from 'lucide-react'
import { api } from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import './ReviewSection.scss'

const spring = { type: 'spring', stiffness: 360, damping: 32, mass: 0.8 }

export function ReviewSection({ listingId }) {
  const navigate = useNavigate()
  const accessToken = useAuthStore((state) => state.accessToken)
  const [reviews, setReviews] = useState([])
  const [newReview, setNewReview] = useState({ baho: 0, matn: '' })
  const [loading, setLoading] = useState(false)

  const fetchReviews = useCallback(async () => {
    try {
      const { data } = await api.get(`/reviews/listing/${listingId}`)
      setReviews(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Reviews load failed', error)
    }
  }, [listingId])

  useEffect(() => {
    if (!listingId) return undefined
    const timer = window.setTimeout(() => {
      void fetchReviews()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [fetchReviews, listingId])

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!accessToken) {
      navigate('/login')
      return
    }

    setLoading(true)
    try {
      await api.post('/reviews/', {
        listing_id: listingId,
        rating: newReview.baho,
        text: newReview.matn,
      })
      setNewReview({ baho: 0, matn: '' })
      await fetchReviews()
    } catch (error) {
      alert(error.response?.data?.detail || 'Xatolik yuz berdi')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.section
      className="review-section"
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={spring}
    >
      <div className="section-heading">
        <span>Social proof</span>
        <h2>Sharhlar ({reviews.length})</h2>
      </div>

      <div className="review-form-card">
        <div className="review-form-head">
          <h3>Sharh qoldiring</h3>
          <span>{newReview.baho || 0}/5</span>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="star-rating" aria-label="Rating">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                type="button"
                key={star}
                onClick={() => setNewReview({ ...newReview, baho: star })}
                className={star <= newReview.baho ? 'active' : ''}
                aria-label={`${star} stars`}
              >
                <Star size={23} fill="currentColor" />
              </button>
            ))}
          </div>
          <textarea
            placeholder="Kvartira haqida fikringiz..."
            value={newReview.matn}
            onChange={(event) => setNewReview({ ...newReview, matn: event.target.value })}
            required
          />
          <button type="submit" className="review-submit" disabled={loading}>
            <Send size={18} />
            {loading ? 'Yuborilmoqda...' : 'Yuborish'}
          </button>
        </form>
      </div>

      <div className="reviews-list">
        {reviews.map((review, index) => (
          <motion.div
            key={review.id}
            className="review-card"
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ ...spring, delay: index * 0.04 }}
          >
            <div className="review-header">
              <div className="user-info">
                <div className="user-avatar">
                  {review.author?.profile_picture_url ? (
                    <img src={review.author.profile_picture_url} alt={review.author.first_name} />
                  ) : (
                    <User size={19} />
                  )}
                </div>
                <span className="username">{review.author?.first_name || review.yozgan?.ism || 'Foydalanuvchi'}</span>
              </div>
              <div className="stars">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    size={14}
                    fill={star <= (review.rating ?? review.baho ?? 0) ? 'currentColor' : 'none'}
                    color={star <= (review.rating ?? review.baho ?? 0) ? 'var(--color-amber)' : 'var(--color-muted)'}
                  />
                ))}
              </div>
            </div>
            <p className="review-text">{review.text ?? review.matn}</p>
            <span className="review-date">{new Date(review.created_at).toLocaleDateString()}</span>
          </motion.div>
        ))}
      </div>
    </motion.section>
  )
}
