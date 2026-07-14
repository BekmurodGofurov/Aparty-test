import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Building2, CalendarDays, MessageSquare, Phone, Star, UserRound } from 'lucide-react'
import { api } from '../../services/api'
import { normalizeUser } from '../../services/userService'
import { AdminBreadcrumb } from './AdminBreadcrumb'
import './AdminDetail.scss'

export function AdminListingDetail() {
  const { listingId } = useParams()
  const navigate = useNavigate()
  const [listing, setListing] = useState(null)
  const [owner, setOwner] = useState(null)
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchListingDetail = async () => {
      try {
        const { data } = await api.get(`/admin/listings/${listingId}/detail`)
        setListing(data.listing)
        setOwner(data.owner ? normalizeUser(data.owner) : null)
        setReviews(data.reviews || [])
      } finally {
        setLoading(false)
      }
    }

    void fetchListingDetail()
  }, [listingId])

  const toggleStatus = async () => {
    if (!listing) return
    const { data } = await api.patch(`/admin/listings/${listing.id}/status`, { is_active: !listing.is_active })
    setListing(data.listing)
  }

  const deleteReview = async (reviewId) => {
    await api.delete(`/admin/reviews/${reviewId}`)
    setReviews((items) => items.filter((item) => item.id !== reviewId))
    setListing((item) => item ? { ...item, reviews_count: Math.max(0, (item.reviews_count || 1) - 1) } : item)
  }

  const formatDate = (value) => value
    ? new Intl.DateTimeFormat('uz-UZ', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
    : '-'

  if (loading) {
    return (
      <main className="admin-detail">
        <div className="page-container">
          <AdminBreadcrumb current="E'lon" />
          <div className="detail-loading">E'lon ma'lumotlari yuklanmoqda...</div>
        </div>
      </main>
    )
  }

  return (
    <main className="admin-detail">
      <div className="page-container">
        <AdminBreadcrumb current={`E'lonlar / ${String(listing?.id || listingId).slice(0, 8)}`} />

        <section className="detail-hero">
          <div className="detail-avatar"><Building2 size={34} /></div>
          <div>
            <p className="eyebrow">E'lon tafsilotlari</p>
            <h1>{listing?.address || `${listing?.district || ''}, ${listing?.region || ''}`}</h1>
            <div className="meta-row">
              <span>{Number(listing?.price_usd || 0).toLocaleString('uz-UZ')} USD</span>
              <span><CalendarDays size={15} /> {formatDate(listing?.created_at)}</span>
              <span><MessageSquare size={15} /> {reviews.length} izoh</span>
            </div>
          </div>
          <button className={`status-action ${listing?.is_active ? 'deactivate' : 'activate'}`} onClick={toggleStatus}>
            {listing?.is_active ? 'Nofaol qilish' : 'Faol qilish'}
          </button>
        </section>

        <section className="detail-grid">
          <div className="detail-panel">
            <div className="panel-title">
              <UserRound size={20} />
              <h2>Kim qo'ygan</h2>
            </div>
            <button className="owner-card" onClick={() => owner && navigate(`/admin/users/${owner.id}`)}>
              <UserRound size={24} />
              <div>
                <strong>{owner?.ism || '-'}</strong>
                <span><Phone size={14} /> {owner?.telefon || '-'}</span>
                <span>{owner?.rol || '-'}</span>
              </div>
            </button>
          </div>

          <div className="detail-panel">
            <div className="panel-title">
              <Building2 size={20} />
              <h2>Reklama ma'lumotlari</h2>
            </div>
            <dl className="info-list">
              <div><dt>Holati</dt><dd>{listing?.is_active ? 'Faol' : 'Nofaol'}</dd></div>
              <div><dt>Turi</dt><dd>{listing?.is_premium ? 'Premium' : 'Oddiy'}</dd></div>
              <div><dt>Xona</dt><dd>{listing?.rooms_count || '-'}</dd></div>
              <div><dt>Ko'rishlar</dt><dd>{listing?.views_count || 0}</dd></div>
            </dl>
          </div>
        </section>

        <section className="detail-panel">
          <div className="panel-title">
            <MessageSquare size={20} />
            <h2>Izohlar</h2>
            <span>{reviews.length} ta</span>
          </div>
          <div className="review-list">
            {reviews.length === 0 ? (
              <div className="empty">Izoh yo'q</div>
            ) : reviews.map((review) => (
              <article className="review-item" key={review.id}>
                <div>
                  <strong>{review.author_name}</strong>
                  <span>{formatDate(review.created_at)}</span>
                  <p>{review.text || '-'}</p>
                  <div className="rating"><Star size={14} /> {review.rating}/5</div>
                </div>
                <button className="danger-btn" onClick={() => deleteReview(review.id)}>O'chirish</button>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  )
}
