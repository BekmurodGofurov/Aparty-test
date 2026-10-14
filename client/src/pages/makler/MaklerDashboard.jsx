import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BadgeCheck,
  Building2,
  CheckCircle2,
  Crown,
  Edit3,
  Eye,
  Home,
  LogOut,
  Megaphone,
  MessageCircle,
  Phone,
  Plus,
  Trash2,
  UserRound,
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
import { indexById, toRequest } from '../../utils/bookingAdapters'
import './MaklerDashboard.scss'
import { getErrorMessage } from '../../utils/auth'
import { FallbackImage } from '../../components/ui/FallbackImage'

const getListingTitle = (listing = {}) => {
  const location = [
    listing.address,
    listing.district,
    listing.region,
  ].filter(Boolean).join(', ')
  return listing.title || location || 'Manzil kiritilmagan'
}

const getListingImages = (listing = {}) => listing.images || []
const getListingRooms = (listing = {}) => listing.rooms_count ?? 0
const getListingSpaces = (listing = {}) => listing.available_spaces ?? 0
const getListingPrice = (listing = {}) => listing.price ?? 0
const isListingActive = (listing = {}) => Boolean(listing.is_active)
const isListingPremium = (listing = {}) => Boolean(listing.is_premium)

export function MaklerDashboard() {
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const clearAuth = useAuthStore((s) => s.clear)
  const basePath = '/makler'
  const roleLabel = 'Makler'
  // Revisiting the dashboard paints the last known profile, listings and requests straight away
  // instead of a blank "yuklanmoqda" screen.
  const cachedProfile = peekCache('/users/me')
  const [broker, setBroker] = useState(() => (cachedProfile ? normalizeUser(cachedProfile) : null))
  const [listings, setListings] = useState(() => peekCache('/listings/me') || [])
  const [bookings, setBookings] = useState(() => peekCache('/bookings/incoming') || [])
  const [loading, setLoading] = useState(!cachedProfile)
  const [activatingId, setActivatingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    const fetchBrokerDashboard = async () => {
      try {
        setLoading(true)
        const [profile, myListings, incoming] = await Promise.allSettled([
          userService.getCurrentUser(),
          getMyListings(),
          getIncomingBookings(),
        ])
        if (profile.status === 'fulfilled') setBroker(profile.value)
        if (myListings.status === 'fulfilled') setListings(Array.isArray(myListings.value) ? myListings.value : [])
        if (incoming.status === 'fulfilled') setBookings(Array.isArray(incoming.value) ? incoming.value : [])
        for (const result of [profile, myListings, incoming]) {
          if (result.status === 'rejected') console.error("Makler ma'lumotlarini yuklashda xatolik:", result.reason)
        }
      } finally {
        setLoading(false)
      }
    }

    if (!accessToken) {
      navigate('/login')
      return
    }

    void fetchBrokerDashboard()
  }, [accessToken, navigate])

  const requests = useMemo(() => bookings.map((booking) => toRequest(booking, indexById(listings))), [bookings, listings])

  const stats = useMemo(() => {
    const activeAds = listings.filter((listing) => isListingActive(listing)).length
    const inactiveAds = listings.filter((listing) => !isListingActive(listing)).length
    const premiumAds = listings.filter((listing) => isListingPremium(listing)).length
    const totalValue = listings.reduce((sum, listing) => sum + Number(getListingPrice(listing) || 0), 0)

    return { activeAds, inactiveAds, premiumAds, totalValue }
  }, [listings])

  const handleLogout = async () => {
    try {
      await authService.logout()
    } catch {
      // Signing out locally must always work, even when the API is unavailable.
    }
    clearAuth()
    navigate('/')
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
    try {
      await (occupied ? markListingOccupied(listing.id) : markListingAvailable(listing.id))
      const listingData = await getMyListings()
      setListings(Array.isArray(listingData) ? listingData : [])
    } catch (error) {
      window.alert(getErrorMessage(error, "Holatni o'zgartirib bo'lmadi."))
    }
  }

  const handleActivateListing = async (listing, premium = false) => {
    try {
      setActivatingId(listing.id)
      if (premium) {
        await upgradeListingToPremium(listing.id)
      } else {
        await activateListingBasic(listing.id)
      }
      setListings((prev) =>
        prev.map((item) =>
          item.id === listing.id
            ? { ...item, is_active: true, is_premium: premium || isListingPremium(item) }
            : item
        )
      )
    } catch (error) {
      window.alert(getErrorMessage(error, "E'lonni yangilab bo'lmadi."))
    } finally {
      setActivatingId(null)
    }
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

  if (loading) {
    return (
      <main className="broker-dashboard">
        <div className="broker-dashboard__shell">
          <div className="broker-dashboard__loading">Makler dashboard yuklanmoqda...</div>
        </div>
      </main>
    )
  }

  return (
    <main className="broker-dashboard">
      <div className="broker-dashboard__shell">
        <section className="broker-profile-hero">
          <div className="broker-avatar" aria-hidden="true">
            <FallbackImage src={broker?.rasm_url} alt="" fallback={<UserRound size={38} />} />
          </div>
          <div className="broker-identity">
            <p className="broker-eyebrow">{roleLabel} account</p>
            <h1>{broker?.full_name || broker?.ism || roleLabel}</h1>
            <div className="broker-badges">
              <span><BadgeCheck size={15} /> {broker?.is_verified ? 'Tasdiqlangan' : 'Tasdiqlanmagan'}</span>
              <span><Phone size={15} /> {broker?.phone || broker?.telefon || '-'}</span>
            </div>
          </div>
          <div className="broker-hero-actions">
            <button className="broker-secondary-btn" onClick={() => navigate(`${basePath}/profile`)}>
              <UserRound size={18} />
              Profil
            </button>
            <button className="broker-secondary-btn" onClick={handleLogout}>
              <LogOut size={18} />
              Chiqish
            </button>
            <button className="broker-primary-btn" onClick={() => navigate(`${basePath}/create`)}>
              <Plus size={18} />
              E'lon qo'shish
            </button>
          </div>
        </section>

        <section className="broker-stats-grid">
          <div className="broker-stat-card">
            <Building2 size={22} />
            <span>Jami e'lonlar</span>
            <strong>{listings.length}</strong>
          </div>
          <div className="broker-stat-card">
            <Megaphone size={22} />
            <span>Reklamada</span>
            <strong>{stats.activeAds}</strong>
          </div>
          <div className="broker-stat-card">
            <Crown size={22} />
            <span>Premium</span>
            <strong>{stats.premiumAds}</strong>
          </div>
          <div className="broker-stat-card">
            <Home size={22} />
            <span>Portfel qiymati</span>
            <strong>${stats.totalValue}</strong>
          </div>
        </section>

        <section className="broker-content-grid">
          <div className="broker-panel broker-panel--wide">
            <div className="broker-panel__header">
              <div>
                <p className="broker-eyebrow">Kvartiralar</p>
                <h2>Mening makler e'lonlarim</h2>
              </div>
              <button className="broker-ghost-btn" onClick={() => navigate(`${basePath}/create`)}>
                <Plus size={16} />
                Yangi
              </button>
            </div>

            {listings.length === 0 ? (
              <div className="broker-empty-state">
                Hali e'lon qo'shilmagan. Birinchi kvartirani qo'shib, mijozlarga ko'rsatishni boshlang.
              </div>
            ) : (
              <div className="broker-listing-stack">
                {listings.map((listing) => {
                  const listingImages = getListingImages(listing)
                  const isOccupied = Number(getListingSpaces(listing)) === 0
                  const listingActive = isListingActive(listing)
                  const listingPremium = isListingPremium(listing)
                  return (
                  <article className="broker-listing-card" key={listing.id}>
                    <div className="broker-listing-card__main">
                      <div className="broker-listing-image">
                        <FallbackImage src={listingImages[0]} alt="" fallback={<Building2 size={24} />} />
                      </div>
                      <div className="broker-listing-info">
                        <div className="broker-listing-title-row">
                          <h3>{getListingTitle(listing)}</h3>
                        </div>
                        <div className="broker-listing-meta">
                          <span>{getListingRooms(listing)} xona</span>
                          <span>{getListingSpaces(listing)} joy</span>
                          <strong>${getListingPrice(listing)}/oy</strong>
                        </div>
                        <div className="broker-status-row">
                          <span className={`broker-status broker-status--${isOccupied ? 'occupied' : listingActive ? 'active' : 'inactive'}`}>
                            {isOccupied ? 'Band' : listingActive ? 'Active' : 'Deactive'}
                          </span>
                          {listingPremium && <span className="broker-status broker-status--premium">Premium</span>}
                        </div>
                      </div>
                    </div>

                    <div className="broker-listing-actions">
                      {!listingActive && !isOccupied && (
                        <button
                          className="broker-primary-btn broker-primary-btn--compact"
                          disabled={activatingId === listing.id}
                          onClick={() => handleActivateListing(listing, false)}
                        >
                          <Megaphone size={16} />
                          {activatingId === listing.id ? 'Chiqarilmoqda...' : 'Reklamaga chiqarish'}
                        </button>
                      )}
                      {listingActive && !listingPremium && !isOccupied && (
                        <button
                          className="broker-icon-btn"
                          disabled={activatingId === listing.id}
                          onClick={() => handleActivateListing(listing, true)}
                        >
                          <Crown size={16} />
                          Premium qilish
                        </button>
                      )}
                      <button className="broker-icon-btn" onClick={() => handleListingOccupancy(listing, !isOccupied)}>
                        <Home size={16} />
                        {isOccupied ? 'Bo\'sh qilish' : 'Band qilish'}
                      </button>
                      <button className="broker-icon-btn" onClick={() => navigate(`${basePath}/listing/${listing.id}/edit`)}>
                        <Edit3 size={16} />
                        Tahrirlash
                      </button>
                      <button className="broker-icon-btn" onClick={() => navigate(`/listing/${listing.id}`)}>
                        <Eye size={16} />
                        Ko'rish
                      </button>
                      {!isOccupied && (
                        <button
                          className="broker-icon-btn broker-icon-btn--danger"
                          disabled={deletingId === listing.id}
                          onClick={() => handleDeleteListing(listing)}
                        >
                          <Trash2 size={16} />
                          {deletingId === listing.id ? "O'chirilmoqda..." : "O'chirish"}
                        </button>
                      )}
                    </div>
                  </article>
                )})}
              </div>
            )}
          </div>

          <aside className="broker-panel">
            <div className="broker-panel__header">
              <div>
                <p className="broker-eyebrow">Mijozlar</p>
                <h2>Band qilish so'rovlari</h2>
              </div>
              <strong>{requests.filter((request) => request.status === 'pending').length}</strong>
            </div>

            {requests.length === 0 ? (
              <div className="broker-empty-state">Hozircha so'rov yo'q.</div>
            ) : (
              <div className="broker-listing-stack">
                {requests.slice(0, 4).map((request) => (
                  <article className="broker-listing-card" key={request.id}>
                    <div className="broker-listing-card__main">
                      <div className="broker-listing-image">
                        <FallbackImage src={request.listing.images?.[0]} alt="" fallback={<MessageCircle size={22} />} />
                      </div>
                      <div>
                        <div className="broker-listing-title-row">
                          <h3>{request.requester.full_name}</h3>
                          <span className={`broker-status broker-status--${request.status === 'pending' ? 'active' : 'inactive'}`}>
                            {request.statusLabel}
                          </span>
                        </div>
                        <p>{request.message || request.requester.phone}</p>
                      </div>
                    </div>
                    {request.status === 'pending' && (
                      <div className="broker-listing-actions">
                        <button className="broker-icon-btn" onClick={() => handleRequestDecision(request.id, 'accept')}>
                          <CheckCircle2 size={16} />
                          Qabul
                        </button>
                        <button className="broker-icon-btn" onClick={() => handleRequestDecision(request.id, 'reject')}>
                          <XCircle size={16} />
                          Rad
                        </button>
                      </div>
                    )}
                  </article>
                ))}
              </div>
            )}
          </aside>

          <aside className="broker-panel">
            <div className="broker-panel__header">
              <div>
                <p className="broker-eyebrow">Hisobot</p>
                <h2>E'lonlar holati</h2>
              </div>
            </div>

            <div className="broker-mini-list">
              <div>
                <span>Nofaol e'lonlar</span>
                <strong>{stats.inactiveAds}</strong>
              </div>
              <div>
                <span>Makler ID</span>
            <strong>#{broker?.user_id || broker?.id || '-'}</strong>
              </div>
            </div>
          </aside>
        </section>
      </div>
    </main>
  )
}
