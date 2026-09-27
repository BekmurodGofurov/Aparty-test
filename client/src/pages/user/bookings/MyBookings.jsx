import './MyBookings.scss'
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  deleteListing,
  getIncomingBookings,
  getMyBookings,
  getMyListings,
  updateBookingStatus,
} from '../../../services/listingService'
import { useAuthStore } from '../../../store/authStore'
import { getErrorMessage } from '../../../utils/auth'
import { peekCache } from '../../../services/browserCache'

const STATUS_LABELS = {
  pending: 'Kutilmoqda',
  confirmed: 'Tasdiqlangan',
  cancelled: 'Bekor qilingan',
  rejected: 'Rad etilgan',
}

const formatDate = (value) =>
  new Intl.DateTimeFormat('uz-UZ', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value))

const isLive = (ad) => ad.is_active && (!ad.expires_at || new Date(ad.expires_at) > new Date())

const replaceById = (list, updated) => list.map((item) => (item.id === updated.id ? { ...item, ...updated } : item))

function BookingSummary({ booking }) {
  return (
    <>
      <div className="booking-card__head">
        <Link to={`/listing/${booking.listing_id}`}>{booking.listing_title || "E'lonni ochish"}</Link>
        <span className={`booking-status booking-status--${booking.status}`}>{STATUS_LABELS[booking.status]}</span>
      </div>
      <p>
        {formatDate(booking.start_date)} — {formatDate(booking.end_date)} · {Number(booking.total_price).toLocaleString('uz-UZ')}
        {booking.is_roommate_request && <span className="booking-tag">Sherik so'rovi</span>}
      </p>
    </>
  )
}

export function MyBookings() {
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  // Revisiting this page (e.g. after opening a listing and coming back) paints the last known
  // bookings and requests straight away instead of a blank "yuklanmoqda" screen.
  const cachedBookings = peekCache('/bookings')
  const [bookings, setBookings] = useState(() => cachedBookings || [])
  const [incoming, setIncoming] = useState(() => peekCache('/bookings/incoming') || [])
  const [loading, setLoading] = useState(!cachedBookings)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [myAds, setMyAds] = useState(() => (peekCache('/listings/me') || []).filter((item) => item.parent_listing_id))

  useEffect(() => {
    const loadBookings = async () => {
      try {
        const [mine, requests, listings] = await Promise.all([getMyBookings(), getIncomingBookings(), getMyListings()])
        setBookings(Array.isArray(mine) ? mine : [])
        setIncoming(Array.isArray(requests) ? requests : [])
        setMyAds((Array.isArray(listings) ? listings : []).filter((item) => item.parent_listing_id))
      } catch (error) {
        setMessage({ type: 'error', text: getErrorMessage(error, "Bronlarni yuklab bo'lmadi.") })
      } finally {
        setLoading(false)
      }
    }

    if (!accessToken) {
      navigate('/login')
      return
    }
    void loadBookings()
  }, [accessToken, navigate])

  const changeStatus = async (id, status) => {
    setMessage({ type: '', text: '' })
    try {
      const updated = await updateBookingStatus(id, status)
      setBookings((prev) => replaceById(prev, updated))
      setIncoming((prev) => replaceById(prev, updated))
    } catch (error) {
      setMessage({ type: 'error', text: getErrorMessage(error, "Holatni o'zgartirib bo'lmadi.") })
    }
  }

  const closeAd = async (id) => {
    setMessage({ type: '', text: '' })
    try {
      await deleteListing(id)
      setMyAds((prev) => prev.filter((ad) => ad.id !== id))
      setMessage({ type: 'success', text: "Sherik e'loni yopildi." })
    } catch (error) {
      setMessage({ type: 'error', text: getErrorMessage(error, "E'lonni yopib bo'lmadi.") })
    }
  }

  if (loading) return <main className="my-bookings"><p>Yuklanmoqda...</p></main>

  return (
    <main className="my-bookings">
      <h1>Bronlarim</h1>
      {message.text && <div className={`my-bookings__message my-bookings__message--${message.type}`}>{message.text}</div>}

      {myAds.length > 0 && (
        <section>
          <h2>Mening sherik e'lonim</h2>
          {myAds.map((ad) => (
            <article className="booking-card" key={ad.id}>
              <div className="booking-card__head">
                <Link to={`/listing/${ad.id}`}>{ad.title || "Sherik e'loni"}</Link>
                <span className={`booking-status booking-status--${isLive(ad) ? 'confirmed' : 'cancelled'}`}>
                  {isLive(ad) ? 'Faol' : 'Yopiq'}
                </span>
              </div>
              <p>
                Bo'sh joy: {ad.available_spaces}
                {ad.expires_at && <> · {formatDate(ad.expires_at)} gacha</>}
              </p>
              <div className="booking-card__actions">
                <button type="button" onClick={() => closeAd(ad.id)}>E'lonni yopish</button>
              </div>
            </article>
          ))}
        </section>
      )}

      <section>
        <h2>Mening bronlarim</h2>
        {bookings.length === 0 && <p className="my-bookings__empty">Hali bron qilmagansiz.</p>}
        {bookings.map((booking) => (
          <article className="booking-card" key={booking.id}>
            <BookingSummary booking={booking} />
            {booking.message && <p className="booking-card__note">{booking.message}</p>}
            <div className="booking-card__actions">
              {['pending', 'confirmed'].includes(booking.status) && (
                <button type="button" onClick={() => changeStatus(booking.id, 'cancelled')}>Bekor qilish</button>
              )}
            </div>

          </article>
        ))}
      </section>

      <section>
        <h2>Kelgan so'rovlar</h2>
        {incoming.length === 0 && <p className="my-bookings__empty">Hozircha so'rov yo'q.</p>}
        {incoming.map((booking) => (
          <article className="booking-card" key={booking.id}>
            <BookingSummary booking={booking} />
            <p className="booking-card__note">
              {booking.requester?.full_name || `Foydalanuvchi #${booking.user_id}`}
              {booking.requester?.phone && <> · <a href={`tel:${booking.requester.phone}`}>{booking.requester.phone}</a></>}
            </p>
            {booking.message && <p className="booking-card__note">"{booking.message}"</p>}
            {booking.status === 'pending' && (
              <div className="booking-card__actions">
                <button type="button" onClick={() => changeStatus(booking.id, 'confirmed')}>Qabul qilish</button>
                <button type="button" onClick={() => changeStatus(booking.id, 'rejected')}>Rad etish</button>
              </div>
            )}
          </article>
        ))}
      </section>
    </main>
  )
}
