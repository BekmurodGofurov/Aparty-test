import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useModalDialog } from '../../hooks/useModalDialog'
import { useNavigate } from 'react-router-dom'
import {
  BadgeCheck,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Crown,
  Edit3,
  Eye,
  Trash2,
  Home,
  MessageCircle,
  Megaphone,
  Phone,
  Plus,
  UserRound,
  Wallet,
  XCircle,
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import {
  activateListingBasic,
  deleteListing,
  getIncomingBookings,
  getMyListings,
  markListingAvailable,
  markListingOccupied,
  updateBookingStatus,
  upgradeListingToPremium,
} from '../../services/listingService'
import { authService } from '../../services/authService'
import { normalizeUser, userService } from '../../services/userService'
import { peekCache } from '../../services/browserCache'
import { activeRentals, indexById, toRequest } from '../../utils/bookingAdapters'
import './OwnerDashboard.scss'
import { getErrorMessage } from '../../utils/auth'
import { FallbackImage } from '../../components/ui/FallbackImage'

const formatDate = (value) => {
  if (!value) return '-'
  return new Intl.DateTimeFormat('uz-UZ', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

const getNextPaymentDate = (startDate) => {
  if (!startDate) return '-'

  const start = new Date(startDate)
  const today = new Date()
  const next = new Date(today.getFullYear(), today.getMonth(), start.getDate())

  if (next < today) {
    next.setMonth(next.getMonth() + 1)
  }

  return formatDate(next)
}

const getListingTitle = (listing = {}) => {
  const location = [
    listing.address,
    listing.district,
    listing.region,
  ].filter(Boolean).join(', ')
  return location || 'Manzil kiritilmagan'
}

const getListingImages = (listing = {}) => listing.images || []
const getListingRooms = (listing = {}) => listing.rooms_count ?? 0
const getListingSpaces = (listing = {}) => listing.available_spaces ?? 0
const getListingPrice = (listing = {}) => listing.price ?? 0
const isListingActive = (listing = {}) => Boolean(listing.is_active)
const getRentalStudent = (rental = {}) => rental.student || rental.tenant || {}

export function OwnerDashboard() {
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const clearAuth = useAuthStore((s) => s.clear)
  // Revisiting the dashboard (e.g. after opening a listing and coming back) paints the last
  // known profile, listings and requests straight away instead of a blank "yuklanmoqda" screen.
  const cachedProfile = peekCache('/users/me')
  const [owner, setOwner] = useState(() => (cachedProfile ? normalizeUser(cachedProfile) : null))
  const [listings, setListings] = useState(() => peekCache('/listings/me') || [])
  const [bookings, setBookings] = useState(() => peekCache('/bookings/incoming') || [])
  const [loading, setLoading] = useState(!cachedProfile)
  const [activatingId, setActivatingId] = useState(null)
  const [promoListing, setPromoListing] = useState(null)
  const promoRef = useRef(null)
  useModalDialog({ open: Boolean(promoListing), onClose: () => setPromoListing(null), dialogRef: promoRef, initialFocus: '.owner-promo-modal__cancel' })
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    const fetchOwnerDashboard = async () => {
      try {
        setLoading(true)
        const [profile, myListings, incoming] = await Promise.allSettled([
          userService.getCurrentUser(),
          getMyListings(),
          getIncomingBookings(),
        ])
        if (profile.status === 'fulfilled') setOwner(profile.value)
        if (myListings.status === 'fulfilled') setListings(Array.isArray(myListings.value) ? myListings.value : [])
        if (incoming.status === 'fulfilled') setBookings(Array.isArray(incoming.value) ? incoming.value : [])
        for (const result of [profile, myListings, incoming]) {
          if (result.status === 'rejected') console.error('Error fetching owner dashboard:', result.reason)
        }
      } finally {
        setLoading(false)
      }
    }

    if (!accessToken) {
      navigate('/login')
      return
    }

    void fetchOwnerDashboard()
  }, [accessToken, navigate])

  const listingsById = useMemo(() => indexById(listings), [listings])
  const requests = useMemo(() => bookings.map((booking) => toRequest(booking, listingsById)), [bookings, listingsById])
  const rentals = useMemo(() => activeRentals(bookings, listingsById), [bookings, listingsById])

  const rentalsByListingId = useMemo(() => {
    return rentals.reduce((acc, rental) => {
      if (rental.is_active) {
        acc[rental.listing_id] = rental
      }
      return acc
    }, {})
  }, [rentals])

  const stats = useMemo(() => {
    const activeAds = listings.filter((listing) => isListingActive(listing)).length
    const inactiveAds = listings.filter((listing) => !isListingActive(listing)).length
    const occupied = rentals.filter((rental) => rental.is_active).length
    const monthlyRevenue = rentals
      .filter((rental) => rental.is_active)
      .reduce((sum, rental) => sum + Number(rental.price || 0), 0)

    return { activeAds, inactiveAds, occupied, monthlyRevenue }
  }, [listings, rentals])

  const handleActivate = async (type) => {
    if (!promoListing) return

    try {
      setActivatingId(promoListing.id)
      if (type === 'premium') {
        await upgradeListingToPremium(promoListing.id)
      } else {
        await activateListingBasic(promoListing.id)
      }
      setListings((prev) =>
        prev.map((listing) =>
          listing.id === promoListing.id
            ? { ...listing, is_active: true, is_premium: type === 'premium' }
            : listing
        )
      )
      setPromoListing(null)
    } catch (error) {
      console.error('Error activating listing:', error)
    } finally {
      setActivatingId(null)
    }
  }

  const handleRequestDecision = async (requestId, action) => {
    try {
      const updated = await updateBookingStatus(requestId, action === 'accept' ? 'confirmed' : 'rejected')
      setBookings((prev) => prev.map((item) => (item.id === requestId ? { ...item, ...updated } : item)))
    } catch (error) {
      window.alert(getErrorMessage(error, "Holatni o'zgartirib bo'lmadi."))
    }
  }

  const handleListingOccupancy = async (listing, occupied) => {
    if (occupied) {
      await markListingOccupied(listing.id)
    } else {
      await markListingAvailable(listing.id)
    }
    const listingData = await getMyListings()
    setListings(Array.isArray(listingData) ? listingData : [])
  }

  const handleDeleteListing = async (listing) => {
    const confirmed = window.confirm(`${getListingTitle(listing)} e'lonini o'chirib yuboraymi?`)
    if (!confirmed) return

    try {
      setDeletingId(listing.id)
      await deleteListing(listing.id)
      setListings((prev) => prev.filter((item) => item.id !== listing.id))
    } catch (error) {
      window.alert(getErrorMessage(error, "E'lonni o'chirishda xatolik bo'ldi."))
    } finally {
      setDeletingId(null)
    }
  }

  const handleLogout = async () => {
    try {
      await authService.logout()
    } catch {
      // Signing out locally must always work, even when the API is unavailable.
    }
    clearAuth()
    navigate('/')
  }

  if (loading) {
    return (
      <main className="owner-dashboard">
        <div className="owner-dashboard__shell">
          <div className="owner-dashboard__loading">Uy egasi profili yuklanmoqda...</div>
        </div>
      </main>
    )
  }

  return (
    <main className="owner-dashboard">
      <div className="owner-dashboard__shell">
        <section className="owner-profile-hero">
          <div className="owner-avatar" aria-hidden="true">
            <FallbackImage src={owner?.rasm_url} alt="" fallback={<UserRound size={38} />} />
          </div>
          <div className="owner-identity">
            <p className="owner-eyebrow">Uy egasi hisobi</p>
            <h1>{owner?.full_name || owner?.ism || 'Uy egasi'}</h1>
            <div className="owner-badges">
              <span><BadgeCheck size={15} /> {owner?.is_verified ? 'Tasdiqlangan' : 'Tasdiqlanmagan'}</span>
              <span><Phone size={15} /> {owner?.phone || owner?.telefon || '-'}</span>
            </div>
          </div>
          <div className="owner-hero-actions">
            <button className="owner-secondary-btn" onClick={() => navigate('/owner/profile')}>
              <UserRound size={18} />
              Profil
            </button>
            <button className="owner-secondary-btn" onClick={handleLogout}>
              Chiqish
            </button>
            <button className="owner-primary-btn" onClick={() => navigate('/owner/create')}>
              <Plus size={18} />
              Kvartira qo'shish
            </button>
          </div>
        </section>

        <section className="owner-stats-grid">
          <div className="owner-stat-card">
            <Home size={22} />
            <span>Jami kvartiralar</span>
            <strong>{listings.length}</strong>
          </div>
          <div className="owner-stat-card">
            <Megaphone size={22} />
            <span>Reklamada</span>
            <strong>{stats.activeAds}</strong>
          </div>
          <div className="owner-stat-card">
            <Clock3 size={22} />
            <span>Nofaol</span>
            <strong>{stats.inactiveAds}</strong>
          </div>
          <div className="owner-stat-card">
            <Wallet size={22} />
            <span>Oylik ijara</span>
            <strong>${stats.monthlyRevenue}</strong>
          </div>
        </section>

        <section className="owner-content-grid">
          <div className="owner-panel owner-panel--wide">
            <div className="owner-panel__header">
              <div>
                <p className="owner-eyebrow">Kvartiralar</p>
                <h2>Mening e'lonlarim</h2>
              </div>
              <button className="owner-ghost-btn" onClick={() => navigate('/owner/create')}>
                <Plus size={16} />
                Yangi
              </button>
            </div>

            {listings.length === 0 ? (
              <div className="owner-empty-state">
                Hali kvartira qo'shilmagan. Birinchi kvartirani qo'shib, reklama tayyorlab qo'ying.
              </div>
            ) : (
              <div className="owner-listing-stack">
                {listings.map((listing) => {
                  const activeRental = rentalsByListingId[listing.id]
                  const activeStudent = getRentalStudent(activeRental)
                  const listingImages = getListingImages(listing)
                  const isOccupied = Boolean(activeRental) || Number(getListingSpaces(listing)) === 0
                  const isVisible = isListingActive(listing)

                  return (
                    <article className="owner-listing-card" key={listing.id}>
                      <div className="owner-listing-card__main">
                        <div className="owner-listing-image">
                          <FallbackImage src={listingImages[0]} alt="" fallback={<Home size={24} />} />
                        </div>
                        <div className="owner-listing-info">
                          <div className="owner-listing-title-row">
                            <h3>{getListingTitle(listing)}</h3>
                          </div>
                          <div className="owner-listing-meta">
                            <span>{getListingRooms(listing)} xona</span>
                            <span>{getListingSpaces(listing)} joy</span>
                            <strong>${getListingPrice(listing)}/oy</strong>
                          </div>
                          <div className="owner-status-row">
                            <span className={`owner-status owner-status--${isOccupied ? 'occupied' : isVisible ? 'active' : 'inactive'}`}>
                              {isOccupied ? 'Band' : isVisible ? 'Faol' : 'Nofaol'}
                            </span>
                          </div>
                          {activeRental && (
                            <div className="owner-renter-inline">
                              <UserRound size={15} />
                              {activeStudent.full_name || 'Student'} olgan, keyingi to'lov: {getNextPaymentDate(activeRental.start_date)}
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="owner-listing-actions">
                        {!isVisible && !isOccupied && (
                          <button
                            className="owner-primary-btn owner-primary-btn--compact"
                            disabled={activatingId === listing.id}
                            onClick={() => setPromoListing(listing)}
                          >
                            <Megaphone size={16} />
                            {activatingId === listing.id ? 'Chiqarilmoqda...' : 'Reklamaga chiqarish'}
                          </button>
                        )}
                        {isVisible && !isOccupied && (
                          <button
                            className="owner-icon-btn"
                            disabled={activatingId === listing.id}
                            onClick={() => setPromoListing(listing)}
                          >
                            <Megaphone size={16} />
                            Reklamani o'zgartirish
                          </button>
                        )}
                        {!activeRental && (
                          <button
                            className="owner-icon-btn"
                            onClick={() => handleListingOccupancy(listing, !isOccupied)}
                          >
                            <Home size={16} />
                            {isOccupied ? 'Bo\'sh qilish' : 'Band qilish'}
                          </button>
                        )}
                        <button className="owner-icon-btn" onClick={() => navigate(`/owner/listing/${listing.id}/edit`)}>
                          <Edit3 size={16} />
                          Tahrirlash
                        </button>
                        <button className="owner-icon-btn" onClick={() => navigate(`/listing/${listing.id}`)}>
                          <Eye size={16} />
                          Ko'rish
                        </button>
                        {!activeRental && (
                          <button
                            className="owner-icon-btn owner-icon-btn--danger"
                            disabled={deletingId === listing.id}
                            onClick={() => handleDeleteListing(listing)}
                          >
                            <Trash2 size={16} />
                            {deletingId === listing.id ? "O'chirilmoqda..." : "O'chirish"}
                          </button>
                        )}
                      </div>
                    </article>
                  )
                })}
              </div>
            )}
          </div>

          <aside className="owner-panel">
            <div className="owner-panel__header">
              <div>
                <p className="owner-eyebrow">So'rovlar</p>
                <h2>Band qilish</h2>
              </div>
              <strong>{requests.filter((request) => request.status === 'pending').length}</strong>
            </div>

            {requests.length === 0 ? (
              <div className="owner-empty-state owner-empty-state--small">
                Hozircha band qilish so'rovi yo'q.
              </div>
            ) : (
              <div className="owner-rental-stack">
                {requests.slice(0, 4).map((request) => (
                  <article className="owner-rental-card" key={request.id}>
                    <div className="owner-rental-card__top">
                      <div>
                        <h3>{request.requester.full_name}</h3>
                        <p>{request.requester.phone}</p>
                      </div>
                      <span className={`owner-status owner-status--${request.status === 'pending' ? 'active' : request.status === 'accepted' ? 'occupied' : 'inactive'}`}>
                        {request.statusLabel}
                      </span>
                    </div>
                    <div className="owner-rental-meta">
                      <span><Home size={14} /> {request.listing.address || [request.listing.district, request.listing.region].filter(Boolean).join(', ')}</span>
                      {request.message && <span><MessageCircle size={14} /> {request.message}</span>}
                    </div>
                    {request.status === 'pending' && (
                      <div className="owner-listing-actions owner-listing-actions--inline">
                        <button className="owner-primary-btn owner-primary-btn--compact" onClick={() => handleRequestDecision(request.id, 'accept')}>
                          <CheckCircle2 size={16} />
                          Qabul qilish
                        </button>
                        <button className="owner-icon-btn" onClick={() => handleRequestDecision(request.id, 'reject')}>
                          <XCircle size={16} />
                          Rad etish
                        </button>
                      </div>
                    )}
                  </article>
                ))}
              </div>
            )}
          </aside>

          <aside className="owner-panel">
            <div className="owner-panel__header">
              <div>
                <p className="owner-eyebrow">Ijara</p>
                <h2>Band kvartiralar</h2>
              </div>
              <strong>{stats.occupied}</strong>
            </div>

            {rentals.filter((rental) => rental.is_active).length === 0 ? (
              <div className="owner-empty-state owner-empty-state--small">
                Hozircha band qilingan kvartira yo'q.
              </div>
            ) : (
              <div className="owner-rental-stack">
                {rentals.filter((rental) => rental.is_active).map((rental) => (
                  <article className="owner-rental-card" key={rental.id}>
                    <div className="owner-rental-card__top">
                      <div>
                        <h3>{getRentalStudent(rental).full_name || 'Student'}</h3>
                        <p>{getRentalStudent(rental).phone || '-'}</p>
                      </div>
                      {(getRentalStudent(rental).is_verified || getRentalStudent(rental).verified) && <CheckCircle2 size={18} />}
                    </div>
                    <div className="owner-rental-meta">
                      <span><Home size={14} /> {rental.listing.address || `${rental.listing.district}, ${rental.listing.region}`}</span>
                      <span><CalendarDays size={14} /> Berilgan: {formatDate(rental.start_date)}</span>
                      <span><Wallet size={14} /> Pul olish: {getNextPaymentDate(rental.start_date)}</span>
                    </div>
                    <strong>${rental.price}/oy</strong>
                  </article>
                ))}
              </div>
            )}
          </aside>
        </section>
      </div>

      {promoListing && createPortal(
        <div className="owner-promo-modal">
          <div className="owner-promo-modal__backdrop" onClick={() => setPromoListing(null)} />
          <div className="owner-promo-modal__card" ref={promoRef} role="dialog" aria-modal="true" aria-label="E’lonni faollashtirish" tabIndex={-1}>
            <p className="owner-eyebrow">Reklama turi</p>
            <h2>{getListingTitle(promoListing)}</h2>
            <p className="owner-promo-modal__copy">
              E'lonni oddiy ro'yxatda chiqarasizmi yoki premium sifatida yuqoriroqda ko'rsatamizmi?
            </p>

            <div className="owner-promo-options">
              <button
                type="button"
                className="owner-promo-option"
                disabled={activatingId === promoListing.id}
                onClick={() => handleActivate('basic')}
              >
                <Megaphone size={22} />
                <span>Oddiy reklama</span>
                <strong className="owner-promo-price">$9</strong>
                <small>30 kun standart ko'rinish, basic statistika va tezroq moderatsiya.</small>
              </button>
              <button
                type="button"
                className="owner-promo-option owner-promo-option--premium"
                disabled={activatingId === promoListing.id}
                onClick={() => handleActivate('premium')}
              >
                <Crown size={22} />
                <span>Premium reklama</span>
                <strong className="owner-promo-price">$49</strong>
                <small>Boosted visibility, AI matching, yuqori joylashuv va premium support.</small>
              </button>
            </div>

            <button className="owner-secondary-btn owner-promo-modal__cancel" onClick={() => setPromoListing(null)}>
              Bekor qilish
            </button>
          </div>
        </div>, document.body,
      )}
    </main>
  )
}
