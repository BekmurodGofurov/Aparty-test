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
  ShieldCheck,
  Trash2,
  UserRound,
  WalletCards,
  XCircle,
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import {
  acceptRentalRequest,
  activateListingBasic,
  deleteListing,
  getMyListings,
  getRentalRequestInbox,
  markListingAvailable,
  markListingOccupied,
  rejectRentalRequest,
  sendRentalRequestMessage,
  upgradeListingToPremium,
} from '../../services/listingService'
import { userService } from '../../services/userService'
import { api } from '../../services/api'
import './MaklerDashboard.scss'

const getListingTitle = (listing = {}) => {
  const location = [listing.manzil, listing.tuman, listing.viloyat].filter(Boolean).join(', ')
  return listing.nomi || location || 'Manzil kiritilmagan'
}

const getSubscriptionStatus = (subscription) => {
  if (!subscription) return true
  return Boolean(subscription.faol ?? subscription.is_active ?? true)
}

export function MaklerDashboard() {
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const role = useAuthStore((s) => s.role)
  const clearAuth = useAuthStore((s) => s.clear)
  const basePath = role === 'broker' ? '/broker' : '/makler'
  const roleLabel = role === 'broker' ? 'Broker' : 'Makler'
  const [broker, setBroker] = useState(null)
  const [listings, setListings] = useState([])
  const [requests, setRequests] = useState([])
  const [requestReplies, setRequestReplies] = useState({})
  const [subscription, setSubscription] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activatingId, setActivatingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    const fetchBrokerDashboard = async () => {
      try {
        setLoading(true)
        const [profileData, listingData, subscriptionResponse, requestData] = await Promise.all([
          userService.getCurrentUser(),
          getMyListings(),
          api.get('/subscriptions/me'),
          getRentalRequestInbox(),
        ])
        setBroker(profileData)
        setListings(Array.isArray(listingData) ? listingData : [])
        setSubscription(subscriptionResponse.data?.[0] || { faol: true, limit: 5, plan: 'Bepul' })
        setRequests(Array.isArray(requestData) ? requestData : [])
      } catch (error) {
        console.error("Makler ma'lumotlarini yuklashda xatolik:", error)
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

  const stats = useMemo(() => {
    const activeAds = listings.filter((listing) => listing.faol).length
    const inactiveAds = listings.filter((listing) => !listing.faol).length
    const premiumAds = listings.filter((listing) => listing.premium).length
    const totalValue = listings.reduce((sum, listing) => sum + Number(listing.narx_usd || 0), 0)

    return { activeAds, inactiveAds, premiumAds, totalValue }
  }, [listings])

  const subscriptionActive = getSubscriptionStatus(subscription)
  const listingLimit = Math.max(Number(subscription?.limit ?? subscription?.listings_limit ?? 5), 1)

  const handleLogout = () => {
    clearAuth()
    navigate('/')
  }

  const handleRequestDecision = async (requestId, action) => {
    const updated = action === 'accept'
      ? await acceptRentalRequest(requestId)
      : await rejectRentalRequest(requestId)
    setRequests((prev) => prev.map((item) => (item.id === requestId ? updated : item)))
  }

  const handleRequestReply = async (requestId) => {
    const text = requestReplies[requestId]?.trim()
    if (!text) return
    await sendRentalRequestMessage(requestId, text)
    setRequestReplies((prev) => ({ ...prev, [requestId]: '' }))
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
            ? { ...item, faol: true, premium: premium || item.premium }
            : item
        )
      )
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
      window.alert(error.response?.data?.detail || "E'lonni o'chirishda xatolik bo'ldi.")
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
            {broker?.rasm_url ? <img src={broker.rasm_url} alt="" /> : <UserRound size={38} />}
          </div>
          <div className="broker-identity">
            <p className="broker-eyebrow">{roleLabel} account</p>
            <h1>{broker?.ism || roleLabel}</h1>
            <div className="broker-badges">
              <span><BadgeCheck size={15} /> {broker?.verified ? 'Tasdiqlangan' : 'Tasdiqlanmagan'}</span>
              <span><Phone size={15} /> {broker?.telefon || '-'}</span>
              <span><WalletCards size={15} /> {subscription?.plan || 'Bepul'} plan</span>
            </div>
          </div>
          <div className="broker-hero-actions">
            <button className="broker-secondary-btn" onClick={() => navigate(`${basePath}/profile`)}>
              <UserRound size={18} />
              Profil
            </button>
            <button className="broker-secondary-btn" onClick={() => navigate(`${basePath}/payments`)}>
              <WalletCards size={18} />
              Tolovlar
            </button>
            <button className="broker-secondary-btn" onClick={handleLogout}>
              <LogOut size={18} />
              Chiqish
            </button>
            <button className="broker-primary-btn" onClick={() => navigate(`${basePath}/create`)} disabled={!subscriptionActive}>
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
              <button className="broker-ghost-btn" onClick={() => navigate(`${basePath}/create`)} disabled={!subscriptionActive}>
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
                  const isOccupied = Number(listing.bosh_joy) === 0
                  return (
                  <article className="broker-listing-card" key={listing.id}>
                    <div className="broker-listing-card__main">
                      <div className="broker-listing-image">
                        {listing.rasmlar?.[0] ? <img src={listing.rasmlar[0]} alt="" /> : <Building2 size={24} />}
                      </div>
                      <div className="broker-listing-info">
                        <div className="broker-listing-title-row">
                          <h3>{getListingTitle(listing)}</h3>
                        </div>
                        <div className="broker-listing-meta">
                          <span>{listing.xonalar_soni || 0} xona</span>
                          <span>{listing.bosh_joy || 0} joy</span>
                          <strong>${listing.narx_usd || 0}/oy</strong>
                        </div>
                        <div className="broker-status-row">
                          <span className={`broker-status broker-status--${isOccupied ? 'occupied' : listing.faol ? 'active' : 'inactive'}`}>
                            {isOccupied ? 'Band' : listing.faol ? 'Active' : 'Deactive'}
                          </span>
                          {listing.premium && <span className="broker-status broker-status--premium">Premium</span>}
                        </div>
                      </div>
                    </div>

                    <div className="broker-listing-actions">
                      {!listing.faol && !isOccupied && (
                        <button
                          className="broker-primary-btn broker-primary-btn--compact"
                          disabled={activatingId === listing.id}
                          onClick={() => handleActivateListing(listing, false)}
                        >
                          <Megaphone size={16} />
                          {activatingId === listing.id ? 'Chiqarilmoqda...' : 'Reklamaga chiqarish'}
                        </button>
                      )}
                      {listing.faol && !listing.premium && !isOccupied && (
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
                        {request.listing.images?.[0] ? <img src={request.listing.images[0]} alt="" /> : <MessageCircle size={22} />}
                      </div>
                      <div>
                        <div className="broker-listing-title-row">
                          <h3>{request.requester.full_name}</h3>
                          <span className={`broker-status broker-status--${request.status === 'pending' ? 'active' : 'inactive'}`}>
                            {request.status}
                          </span>
                        </div>
                        <p>{request.message || request.requester.phone}</p>
                      </div>
                    </div>
                    <div className="broker-request-reply">
                      <input
                        value={requestReplies[request.id] || ''}
                        onChange={(event) => setRequestReplies((prev) => ({ ...prev, [request.id]: event.target.value }))}
                        placeholder="Guest userga xabar..."
                      />
                      <button className="broker-icon-btn" type="button" onClick={() => handleRequestReply(request.id)}>
                        <MessageCircle size={16} />
                        Yuborish
                      </button>
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
                <p className="broker-eyebrow">Obuna</p>
                <h2>Makler limiti</h2>
              </div>
              <ShieldCheck size={28} />
            </div>

            <div className="broker-subscription-card">
              <span className={`broker-subscription-card__status ${subscriptionActive ? 'active' : 'inactive'}`}>
                {subscriptionActive ? 'Faol' : 'Nofaol'}
              </span>
              <h3>{subscription?.plan || 'Bepul'} plan</h3>
              <p>{listings.length} / {listingLimit} ta e'lon ishlatilgan</p>
              <div className="broker-limit-bar" aria-hidden="true">
                <span style={{ width: `${Math.min((listings.length / listingLimit) * 100, 100)}%` }} />
              </div>
              <button className="broker-primary-btn broker-primary-btn--full" onClick={() => navigate(`${basePath}/subscription`)}>
                <Crown size={18} />
                Obunani boshqarish
              </button>
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
