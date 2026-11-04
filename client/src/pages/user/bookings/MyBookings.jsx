import './MyBookings.scss'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  CalendarCheck,
  Calendar,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Phone,
  Send,
  Home,
  MapPin,
  ExternalLink,
  ShieldCheck,
  MessageSquare,
  Search,
  Check,
  X,
  Sparkles,
  Inbox,
  Users,
  Coins,
  DoorOpen,
} from 'lucide-react'
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
import { FallbackImage } from '../../../components/ui/FallbackImage'
import { GlassCard, Button } from '../../../components/ui/PremiumComponents'

const formatDate = (value) => {
  if (!value) return '-'
  try {
    return new Intl.DateTimeFormat('uz-UZ', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value))
  } catch {
    return String(value)
  }
}

const calculateDays = (start, end) => {
  if (!start || !end) return null
  const s = new Date(start)
  const e = new Date(end)
  const diffTime = e.getTime() - s.getTime()
  if (diffTime <= 0) return 1
  return Math.max(1, Math.round(diffTime / (1000 * 60 * 60 * 24)))
}

const isLive = (ad) => ad.is_active && (!ad.expires_at || new Date(ad.expires_at) > new Date())

const replaceById = (list, updated) => list.map((item) => (item.id === updated.id ? { ...item, ...updated } : item))

export function MyBookings() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const role = useAuthStore((s) => s.role)

  const cachedBookings = peekCache('/bookings')
  const [bookings, setBookings] = useState(() => (Array.isArray(cachedBookings) ? cachedBookings : []))
  const [incoming, setIncoming] = useState(() => {
    const cached = peekCache('/bookings/incoming')
    return Array.isArray(cached) ? cached : []
  })
  const [loading, setLoading] = useState(!Array.isArray(cachedBookings))
  const [actionLoadingId, setActionLoadingId] = useState(null)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [myAds, setMyAds] = useState(() => {
    const cached = peekCache('/listings/me')
    return Array.isArray(cached) ? cached.filter((item) => item?.parent_listing_id) : []
  })

  const [activeTab, setActiveTab] = useState(() => {
    const params = new URLSearchParams(window.location.search)
    const tabParam = params.get('tab')
    if (tabParam && ['mine', 'incoming', 'myAds'].includes(tabParam)) return tabParam
    if (role === 'owner' || role === 'makler') return 'incoming'
    return 'mine'
  })
  const [statusFilter, setStatusFilter] = useState('all') // 'all' | 'pending' | 'confirmed' | 'cancelled' | 'rejected'
  const [searchQuery, setSearchQuery] = useState('')

  const [confirmModal, setConfirmModal] = useState({
    isOpen: false,
    title: '',
    text: '',
    actionText: '',
    danger: false,
    onConfirm: null,
  })

  useEffect(() => {
    const loadBookings = async () => {
      try {
        const [mine, requests, listings] = await Promise.all([
          getMyBookings().catch(() => []),
          getIncomingBookings().catch(() => []),
          getMyListings().catch(() => []),
        ])
        const safeMine = Array.isArray(mine) ? mine : []
        const safeRequests = Array.isArray(requests) ? requests : []
        const safeListings = Array.isArray(listings) ? listings : []

        setBookings(safeMine)
        setIncoming(safeRequests)
        setMyAds(safeListings.filter((item) => item?.parent_listing_id))

        // If the user has incoming requests but no bookings of their own, and hasn't explicitly
        // picked a tab in the URL, automatically switch to 'incoming' so they see the request immediately.
        const tabParam = new URLSearchParams(window.location.search).get('tab')
        if (!tabParam && safeMine.length === 0 && safeRequests.length > 0) {
          setActiveTab('incoming')
        }
      } catch (error) {
        setMessage({ type: 'error', text: getErrorMessage(error, t('bookings.fetch_error', "Bronlarni yuklab bo'lmadi.")) })
      } finally {
        setLoading(false)
      }
    }

    if (!accessToken) {
      navigate('/login')
      return
    }
    void loadBookings()
  }, [accessToken, navigate, t])

  // KPIs
  const stats = useMemo(() => {
    const mineTotal = bookings.length
    const mineConfirmed = bookings.filter((b) => b.status === 'confirmed').length
    const minePending = bookings.filter((b) => b.status === 'pending').length
    const incomingPending = incoming.filter((b) => b.status === 'pending').length
    return {
      mineTotal,
      mineConfirmed,
      minePending,
      incomingPending,
      incomingTotal: incoming.length,
      adsTotal: myAds.length,
    }
  }, [bookings, incoming, myAds])

  const changeStatus = async (id, status) => {
    setMessage({ type: '', text: '' })
    setActionLoadingId(id)
    try {
      const updated = await updateBookingStatus(id, status)
      setBookings((prev) => replaceById(prev, updated))
      setIncoming((prev) => replaceById(prev, updated))
      const statusMap = {
        confirmed: t('bookings.status_confirmed', 'Tasdiqlangan'),
        rejected: t('bookings.status_rejected', 'Rad etilgan'),
        cancelled: t('bookings.status_cancelled', 'Bekor qilingan'),
      }
      setMessage({
        type: 'success',
        text: `Holat "${statusMap[status] || status}" ga muvaffaqiyatli o'zgartirildi.`,
      })
    } catch (error) {
      setMessage({ type: 'error', text: getErrorMessage(error, "Holatni o'zgartirib bo'lmadi.") })
    } finally {
      setActionLoadingId(null)
      setConfirmModal({ isOpen: false, title: '', text: '', actionText: '', danger: false, onConfirm: null })
    }
  }

  const handleCancelBooking = (booking) => {
    setConfirmModal({
      isOpen: true,
      title: t('bookings.confirm_cancel_title', 'Bronni bekor qilishni xohlaysizmi?'),
      text: t('bookings.confirm_cancel_text', 'Ushbu amalni ortga qaytarib bo‘lmaydi. Broningiz bekor qilinadi.'),
      actionText: t('bookings.btn_cancel_booking', 'Bekor qilish'),
      danger: true,
      onConfirm: () => changeStatus(booking.id, 'cancelled'),
    })
  }

  const handleRejectBooking = (booking) => {
    setConfirmModal({
      isOpen: true,
      title: t('bookings.confirm_reject_title', 'So‘rovni rad etishni xohlaysizmi?'),
      text: t('bookings.confirm_reject_text', 'Ijarachiga so‘rov rad etilganligi haqida xabar beriladi.'),
      actionText: t('bookings.btn_reject', 'Rad etish'),
      danger: true,
      onConfirm: () => changeStatus(booking.id, 'rejected'),
    })
  }

  const closeAd = async (id) => {
    setMessage({ type: '', text: '' })
    setActionLoadingId(id)
    try {
      await deleteListing(id)
      setMyAds((prev) => prev.filter((ad) => ad.id !== id))
      setMessage({ type: 'success', text: t('bookings.ad_closed_success', "Sherik e'loni yopildi.") })
    } catch (error) {
      setMessage({ type: 'error', text: getErrorMessage(error, "E'lonni yopib bo'lmadi.") })
    } finally {
      setActionLoadingId(null)
      setConfirmModal({ isOpen: false, title: '', text: '', actionText: '', danger: false, onConfirm: null })
    }
  }

  const handleCloseAdConfirm = (ad) => {
    setConfirmModal({
      isOpen: true,
      title: "Sherik e'lonini yopish",
      text: "Haqiqatan ham ushbu sheriklik e'lonini yopmoqchimisiz?",
      actionText: t('bookings.btn_close_ad', "E'lonni yopish"),
      danger: true,
      onConfirm: () => closeAd(ad.id),
    })
  }

  // Filtered lists
  const filteredBookings = useMemo(() => {
    return bookings.filter((b) => {
      if (statusFilter !== 'all' && b.status !== statusFilter) return false
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        const titleMatch = (b.listing_title || '').toLowerCase().includes(query)
        const addrMatch = (b.listing?.address || '').toLowerCase().includes(query)
        const hostMatch = (b.host?.full_name || '').toLowerCase().includes(query)
        if (!titleMatch && !addrMatch && !hostMatch) return false
      }
      return true
    })
  }, [bookings, statusFilter, searchQuery])

  const filteredIncoming = useMemo(() => {
    return incoming.filter((b) => {
      if (statusFilter !== 'all' && b.status !== statusFilter) return false
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        const titleMatch = (b.listing_title || '').toLowerCase().includes(query)
        const addrMatch = (b.listing?.address || '').toLowerCase().includes(query)
        const reqMatch = (b.requester?.full_name || '').toLowerCase().includes(query)
        if (!titleMatch && !addrMatch && !reqMatch) return false
      }
      return true
    })
  }, [incoming, statusFilter, searchQuery])

  const filteredMyAds = useMemo(() => {
    return myAds.filter((ad) => {
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        const titleMatch = (ad.title || '').toLowerCase().includes(query)
        const addrMatch = (ad.address || '').toLowerCase().includes(query)
        if (!titleMatch && !addrMatch) return false
      }
      return true
    })
  }, [myAds, searchQuery])

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'confirmed':
        return (
          <span className="booking-status-badge booking-status-badge--confirmed">
            <CheckCircle2 size={13} />
            <span>{t('bookings.status_confirmed', 'Tasdiqlangan')}</span>
          </span>
        )
      case 'pending':
        return (
          <span className="booking-status-badge booking-status-badge--pending">
            <span className="pulse-dot" />
            <Clock size={13} />
            <span>{t('bookings.status_pending', 'Kutilmoqda')}</span>
          </span>
        )
      case 'rejected':
        return (
          <span className="booking-status-badge booking-status-badge--rejected">
            <AlertCircle size={13} />
            <span>{t('bookings.status_rejected', 'Rad etilgan')}</span>
          </span>
        )
      case 'cancelled':
      default:
        return (
          <span className="booking-status-badge booking-status-badge--cancelled">
            <XCircle size={13} />
            <span>{t('bookings.status_cancelled', 'Bekor qilingan')}</span>
          </span>
        )
    }
  }

  return (
    <main className="my-bookings-page">
      <div className="my-bookings-container">
        {/* HERO / HEADER SECTION */}
        <header className="my-bookings-hero">
          <div className="hero-text-wrap">
            <div className="hero-badge">
              <CalendarCheck size={15} />
              <span>{t('bookings.badge', 'Bron boshqaruvi')}</span>
            </div>
            <h1 className="hero-title">{t('bookings.title', 'Mening bronlarim')}</h1>
            <p className="hero-subtitle">
              {t('bookings.subtitle', 'Band qilingan kvartiralar, kelgan so‘rovlar va ijaralar tarixi')}
            </p>
          </div>
          <div className="hero-actions">
            <Button
              variant="primary"
              size="sm"
              className="btn-browse-homes"
              onClick={() => navigate('/search')}
            >
              <Search size={15} />
              <span>{t('bookings.btn_explore', 'Uylarni qidirish')}</span>
            </Button>
          </div>
        </header>

        {/* FEEDBACK TOAST / MESSAGE */}
        {message.text && (
          <div className={`bookings-banner bookings-banner--${message.type}`}>
            <div className="banner-content">
              {message.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
              <span>{message.text}</span>
            </div>
            <button
              type="button"
              className="banner-close"
              onClick={() => setMessage({ type: '', text: '' })}
              aria-label="Yopish"
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* STATS OVERVIEW */}
        <section className="bookings-stats-grid">
          <GlassCard className="stat-card">
            <div className="stat-card__icon stat-card__icon--blue">
              <Home size={22} />
            </div>
            <div className="stat-card__content">
              <span className="stat-card__value">{stats.mineTotal}</span>
              <span className="stat-card__label">{t('bookings.stat_total', 'Jami bronlar')}</span>
            </div>
          </GlassCard>

          <GlassCard className="stat-card">
            <div className="stat-card__icon stat-card__icon--emerald">
              <CheckCircle2 size={22} />
            </div>
            <div className="stat-card__content">
              <span className="stat-card__value">{stats.mineConfirmed}</span>
              <span className="stat-card__label">{t('bookings.stat_confirmed', 'Tasdiqlangan')}</span>
            </div>
          </GlassCard>

          <GlassCard className="stat-card">
            <div className="stat-card__icon stat-card__icon--amber">
              <Clock size={22} />
            </div>
            <div className="stat-card__content">
              <span className="stat-card__value">{stats.minePending}</span>
              <span className="stat-card__label">{t('bookings.stat_pending', 'Kutilmoqda')}</span>
            </div>
          </GlassCard>

          <GlassCard className="stat-card">
            <div className="stat-card__icon stat-card__icon--purple">
              <Inbox size={22} />
            </div>
            <div className="stat-card__content">
              <div className="stat-card__value-wrap">
                <span className="stat-card__value">{stats.incomingTotal}</span>
                {stats.incomingPending > 0 && (
                  <span className="stat-badge-pulse">{stats.incomingPending} yangi</span>
                )}
              </div>
              <span className="stat-card__label">{t('bookings.stat_incoming', 'Kelgan so‘rovlar')}</span>
            </div>
          </GlassCard>
        </section>

        {/* TABS CONTROLLER */}
        <div className="bookings-tabs-nav">
          <button
            type="button"
            className={`tab-btn ${activeTab === 'mine' ? 'active' : ''}`}
            onClick={() => setActiveTab('mine')}
          >
            <Calendar size={17} />
            <span>{t('bookings.tab_mine', 'Mening bronlarim')}</span>
            <span className="tab-count">{bookings.length}</span>
          </button>

          <button
            type="button"
            className={`tab-btn ${activeTab === 'incoming' ? 'active' : ''}`}
            onClick={() => setActiveTab('incoming')}
          >
            <Inbox size={17} />
            <span>{t('bookings.tab_incoming', 'Kelgan so‘rovlar')}</span>
            <span className={`tab-count ${stats.incomingPending > 0 ? 'highlight' : ''}`}>
              {incoming.length}
            </span>
          </button>

          {myAds.length > 0 && (
            <button
              type="button"
              className={`tab-btn ${activeTab === 'myAds' ? 'active' : ''}`}
              onClick={() => setActiveTab('myAds')}
            >
              <Users size={17} />
              <span>{t('bookings.tab_ads', 'Sherik e‘lonlarim')}</span>
              <span className="tab-count">{myAds.length}</span>
            </button>
          )}
        </div>

        {/* CONTROLS (SEARCH & STATUS FILTERS) */}
        {activeTab !== 'myAds' && (
          <div className="bookings-toolbar">
            <div className="filter-pills-wrap">
              {[
                { id: 'all', label: t('bookings.filter_all', 'Barchasi') },
                { id: 'pending', label: t('bookings.filter_pending', 'Kutilmoqda') },
                { id: 'confirmed', label: t('bookings.filter_confirmed', 'Tasdiqlangan') },
                { id: 'cancelled', label: t('bookings.filter_cancelled', 'Bekor qilingan') },
                { id: 'rejected', label: t('bookings.filter_rejected', 'Rad etilgan') },
              ].map((f) => (
                <button
                  key={f.id}
                  type="button"
                  className={`filter-pill ${statusFilter === f.id ? 'active' : ''}`}
                  onClick={() => setStatusFilter(f.id)}
                >
                  {f.label}
                </button>
              ))}
            </div>

            <div className="search-input-wrap">
              <Search size={16} className="search-icon" />
              <input
                type="text"
                placeholder={t('bookings.search_placeholder', 'Manzil yoki nom bo‘yicha qidirish...')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  className="search-clear-btn"
                  onClick={() => setSearchQuery('')}
                  aria-label="Tozalash"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          </div>
        )}

        {/* LOADING SKELETON */}
        {loading && (
          <div className="bookings-cards-stack">
            {[1, 2, 3].map((n) => (
              <GlassCard className="booking-card-skeleton" key={n}>
                <div className="skeleton-thumb" />
                <div className="skeleton-content">
                  <div className="skeleton-line skeleton-line--title" />
                  <div className="skeleton-line skeleton-line--meta" />
                  <div className="skeleton-line skeleton-line--details" />
                  <div className="skeleton-line skeleton-line--contact" />
                </div>
              </GlassCard>
            ))}
          </div>
        )}

        {/* TAB CONTENT: MENING BRONLARIM */}
        {!loading && activeTab === 'mine' && (
          <div className="bookings-cards-stack">
            {filteredBookings.length === 0 ? (
              <GlassCard className="bookings-empty-state">
                <div className="empty-icon-wrap">
                  <CalendarCheck size={42} />
                </div>
                <h3>{t('bookings.empty_mine_title', 'Hali bron qilmagansiz')}</h3>
                <p>
                  {t(
                    'bookings.empty_mine_desc',
                    'O‘zingizga mos kvartira yoki xonani toping va bron qilish so‘rovini yuboring.'
                  )}
                </p>
                <Button
                  variant="primary"
                  size="md"
                  className="empty-cta-btn"
                  onClick={() => navigate('/search')}
                >
                  <Search size={16} />
                  <span>{t('bookings.btn_explore', 'Kvartiralarni ko‘rish')}</span>
                </Button>
              </GlassCard>
            ) : (
              filteredBookings.map((booking) => {
                const days = calculateDays(booking.start_date, booking.end_date)
                const listing = booking.listing || {}
                const host = booking.host || {}
                const title = listing.address || booking.listing_title || "Kvartira e'loni"
                const location = [listing.district, listing.region].filter(Boolean).join(', ')
                const imageUrl = listing.images?.[0]?.image_url || listing.images?.[0] || listing.image_url

                return (
                  <GlassCard className="booking-card" key={booking.id}>
                    {/* LEFT / THUMBNAIL */}
                    <div className="booking-card__media" onClick={() => navigate(`/listing/${booking.listing_id}`)}>
                      <FallbackImage
                        src={imageUrl}
                        alt={title}
                        fallback={<Home size={28} />}
                        className="booking-card__img"
                      />
                      <div className="booking-card__badge-tag">
                        {booking.is_roommate_request ? (
                          <span className="type-tag type-tag--roommate">
                            <Users size={12} /> {t('bookings.roommate_tag', 'Sheriklik')}
                          </span>
                        ) : (
                          <span className="type-tag type-tag--full">
                            <Home size={12} /> {t('bookings.full_unit_tag', 'Kvartira')}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* MAIN INFO BODY */}
                    <div className="booking-card__body">
                      {/* TOP ROW: TITLE & STATUS */}
                      <div className="card-top-row">
                        <div className="title-area">
                          <Link to={`/listing/${booking.listing_id}`} className="listing-link">
                            <h2>{title}</h2>
                          </Link>
                          {location && (
                            <p className="location-text">
                              <MapPin size={13} />
                              <span>{location}</span>
                            </p>
                          )}
                        </div>
                        <div className="status-area">
                          {renderStatusBadge(booking.status)}
                        </div>
                      </div>

                      {/* MIDDLE ROW: DATES, DURATION & PRICE CHIPS */}
                      <div className="booking-meta-chips">
                        <div className="meta-chip">
                          <Calendar size={14} className="chip-icon" />
                          <div className="chip-content">
                            <span className="chip-label">Sanalar:</span>
                            <span className="chip-value">
                              {formatDate(booking.start_date)} — {formatDate(booking.end_date)}
                              {days && <strong className="duration-tag">({days} {t('bookings.duration_days', 'kun')})</strong>}
                            </span>
                          </div>
                        </div>

                        <div className="meta-chip meta-chip--price">
                          <Coins size={14} className="chip-icon" />
                          <div className="chip-content">
                            <span className="chip-label">{t('bookings.total_sum', 'Jami narx')}:</span>
                            <span className="chip-value price-highlight">
                              ${Number(booking.total_price || 0).toLocaleString('uz-UZ')}
                              {listing.price && (
                                <span className="monthly-sub">(${listing.price}{t('bookings.monthly', '/oy')})</span>
                              )}
                            </span>
                          </div>
                        </div>

                        {listing.rooms_count && (
                          <div className="meta-chip meta-chip--rooms">
                            <DoorOpen size={14} className="chip-icon" />
                            <div className="chip-content">
                              <span className="chip-label">Xonalar:</span>
                              <span className="chip-value">{listing.rooms_count} xona</span>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* HOST CONTACT CARD */}
                      <div className="host-contact-panel">
                        <div className="host-info">
                          <div className="host-avatar">
                            {(host.full_name || 'U').charAt(0).toUpperCase()}
                          </div>
                          <div className="host-details">
                            <div className="host-name-row">
                              <span className="host-label">{t('bookings.host_title', 'Uy egasi')}:</span>
                              <strong className="host-name">{host.full_name || `Foydalanuvchi #${booking.listing_owner_id}`}</strong>
                              {host.is_verified && (
                                <span className="verified-badge" title="Tasdiqlangan foydalanuvchi">
                                  <ShieldCheck size={14} />
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="host-actions">
                          {host.phone && (
                            <a
                              href={`tel:${String(host.phone).replace(/\s/g, '')}`}
                              className="contact-pill contact-pill--phone"
                              title="Qo‘ng‘iroq qilish"
                            >
                              <Phone size={14} />
                              <span>{host.phone}</span>
                            </a>
                          )}
                          {host.telegram_username && (
                            <a
                              href={`https://t.me/${host.telegram_username.replace('@', '')}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="contact-pill contact-pill--telegram"
                              title="Telegram orqali yozish"
                            >
                              <Send size={14} />
                              <span>@{host.telegram_username.replace('@', '')}</span>
                            </a>
                          )}
                        </div>
                      </div>

                      {/* USER REQUEST NOTE */}
                      {booking.message && (
                        <div className="booking-note-quote">
                          <MessageSquare size={14} className="quote-icon" />
                          <p className="quote-text">"{booking.message}"</p>
                        </div>
                      )}

                      {/* HELPER TEXT BASED ON STATUS */}
                      {booking.status === 'confirmed' && (
                        <div className="status-tip status-tip--confirmed">
                          <Sparkles size={14} />
                          <span>
                            Ushbu bron tasdiqlangan. Ko‘chib o‘tish va kalitlarni olish uchun uy egasi bilan bog‘laning.
                          </span>
                        </div>
                      )}

                      {booking.status === 'pending' && (
                        <div className="status-tip status-tip--pending">
                          <Clock size={14} />
                          <span>
                            So‘rovingiz yuborilgan. Uy egasi tasdiqlashi bilan sizga bildirishnoma yuboriladi.
                          </span>
                        </div>
                      )}

                      {/* CARD ACTIONS FOOTER */}
                      <div className="card-actions-footer">
                        <Link
                          to={`/listing/${booking.listing_id}`}
                          className="action-btn action-btn--view"
                        >
                          <ExternalLink size={14} />
                          <span>{t('bookings.btn_view_listing', "E'lonni ochish")}</span>
                        </Link>

                        {['pending', 'confirmed'].includes(booking.status) && (
                          <button
                            type="button"
                            className="action-btn action-btn--cancel"
                            disabled={actionLoadingId === booking.id}
                            onClick={() => handleCancelBooking(booking)}
                          >
                            <X size={14} />
                            <span>
                              {actionLoadingId === booking.id
                                ? 'Yuklanmoqda...'
                                : t('bookings.btn_cancel_booking', 'Bronni bekor qilish')}
                            </span>
                          </button>
                        )}
                      </div>
                    </div>
                  </GlassCard>
                )
              })
            )}
          </div>
        )}

        {/* TAB CONTENT: KELGAN SO'ROVLAR (INCOMING) */}
        {!loading && activeTab === 'incoming' && (
          <div className="bookings-cards-stack">
            {filteredIncoming.length === 0 ? (
              <GlassCard className="bookings-empty-state">
                <div className="empty-icon-wrap">
                  <Inbox size={42} />
                </div>
                <h3>{t('bookings.empty_incoming_title', 'Kelgan so‘rovlar yo‘q')}</h3>
                <p>
                  {t(
                    'bookings.empty_incoming_desc',
                    'Sizning e‘lonlaringizga hozircha yangi so‘rovlar kelib tushmagan.'
                  )}
                </p>
              </GlassCard>
            ) : (
              filteredIncoming.map((booking) => {
                const days = calculateDays(booking.start_date, booking.end_date)
                const listing = booking.listing || {}
                const requester = booking.requester || {}
                const title = listing.address || booking.listing_title || "Kvartira e'loni"
                const location = [listing.district, listing.region].filter(Boolean).join(', ')
                const imageUrl = listing.images?.[0]?.image_url || listing.images?.[0] || listing.image_url

                return (
                  <GlassCard className="booking-card incoming-card" key={booking.id}>
                    {/* LEFT / THUMBNAIL */}
                    <div className="booking-card__media" onClick={() => navigate(`/listing/${booking.listing_id}`)}>
                      <FallbackImage
                        src={imageUrl}
                        alt={title}
                        fallback={<Home size={28} />}
                        className="booking-card__img"
                      />
                      <div className="booking-card__badge-tag">
                        {booking.is_roommate_request ? (
                          <span className="type-tag type-tag--roommate">
                            <Users size={12} /> {t('bookings.roommate_tag', 'Sheriklik')}
                          </span>
                        ) : (
                          <span className="type-tag type-tag--full">
                            <Home size={12} /> {t('bookings.full_unit_tag', 'Kvartira')}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* MAIN INFO BODY */}
                    <div className="booking-card__body">
                      {/* TOP ROW: TITLE & STATUS */}
                      <div className="card-top-row">
                        <div className="title-area">
                          <Link to={`/listing/${booking.listing_id}`} className="listing-link">
                            <h2>{title}</h2>
                          </Link>
                          {location && (
                            <p className="location-text">
                              <MapPin size={13} />
                              <span>{location}</span>
                            </p>
                          )}
                        </div>
                        <div className="status-area">
                          {renderStatusBadge(booking.status)}
                        </div>
                      </div>

                      {/* REQUESTER PROFILE BAR */}
                      <div className="host-contact-panel requester-panel">
                        <div className="host-info">
                          <div className="host-avatar requester-avatar">
                            {(requester.full_name || 'F').charAt(0).toUpperCase()}
                          </div>
                          <div className="host-details">
                            <div className="host-name-row">
                              <span className="host-label">{t('bookings.requester_title', 'Mijoz')}:</span>
                              <strong className="host-name">{requester.full_name || `Foydalanuvchi #${booking.user_id}`}</strong>
                              {requester.is_verified && (
                                <span className="verified-badge" title="Tasdiqlangan ijarachi">
                                  <ShieldCheck size={14} />
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="host-actions">
                          {requester.phone && (
                            <a
                              href={`tel:${String(requester.phone).replace(/\s/g, '')}`}
                              className="contact-pill contact-pill--phone"
                              title="Qo‘ng‘iroq qilish"
                            >
                              <Phone size={14} />
                              <span>{requester.phone}</span>
                            </a>
                          )}
                          {requester.telegram_username && (
                            <a
                              href={`https://t.me/${requester.telegram_username.replace('@', '')}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="contact-pill contact-pill--telegram"
                              title="Telegram"
                            >
                              <Send size={14} />
                              <span>@{requester.telegram_username.replace('@', '')}</span>
                            </a>
                          )}
                        </div>
                      </div>

                      {/* DATES & FINANCIALS */}
                      <div className="booking-meta-chips">
                        <div className="meta-chip">
                          <Calendar size={14} className="chip-icon" />
                          <div className="chip-content">
                            <span className="chip-label">Muddat:</span>
                            <span className="chip-value">
                              {formatDate(booking.start_date)} — {formatDate(booking.end_date)}
                              {days && <strong className="duration-tag">({days} {t('bookings.duration_days', 'kun')})</strong>}
                            </span>
                          </div>
                        </div>

                        <div className="meta-chip meta-chip--price">
                          <Coins size={14} className="chip-icon" />
                          <div className="chip-content">
                            <span className="chip-label">{t('bookings.total_sum', 'Jami summa')}:</span>
                            <span className="chip-value price-highlight">
                              ${Number(booking.total_price || 0).toLocaleString('uz-UZ')}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* NOTE */}
                      {booking.message && (
                        <div className="booking-note-quote">
                          <MessageSquare size={14} className="quote-icon" />
                          <p className="quote-text">"{booking.message}"</p>
                        </div>
                      )}

                      {/* ACTIONS */}
                      <div className="card-actions-footer incoming-actions">
                        <Link
                          to={`/listing/${booking.listing_id}`}
                          className="action-btn action-btn--view"
                        >
                          <ExternalLink size={14} />
                          <span>{t('bookings.btn_view_listing', "E'lonni ochish")}</span>
                        </Link>

                        {booking.status === 'pending' && (
                          <div className="incoming-decision-btns">
                            <button
                              type="button"
                              className="action-btn action-btn--accept"
                              disabled={actionLoadingId === booking.id}
                              onClick={() => changeStatus(booking.id, 'confirmed')}
                            >
                              <Check size={15} />
                              <span>
                                {actionLoadingId === booking.id
                                  ? 'Yuklanmoqda...'
                                  : t('bookings.btn_accept', 'Qabul qilish')}
                              </span>
                            </button>

                            <button
                              type="button"
                              className="action-btn action-btn--reject"
                              disabled={actionLoadingId === booking.id}
                              onClick={() => handleRejectBooking(booking)}
                            >
                              <X size={15} />
                              <span>{t('bookings.btn_reject', 'Rad etish')}</span>
                            </button>
                          </div>
                        )}

                        {booking.status === 'confirmed' && (
                          <button
                            type="button"
                            className="action-btn action-btn--cancel"
                            disabled={actionLoadingId === booking.id}
                            onClick={() => handleCancelBooking(booking)}
                          >
                            <X size={14} />
                            <span>{t('bookings.btn_cancel_booking', 'Bekor qilish')}</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </GlassCard>
                )
              })
            )}
          </div>
        )}

        {/* TAB CONTENT: MENING SHERIK E'LONLARIM */}
        {!loading && activeTab === 'myAds' && (
          <div className="bookings-cards-stack">
            {filteredMyAds.length === 0 ? (
              <GlassCard className="bookings-empty-state">
                <div className="empty-icon-wrap">
                  <Users size={42} />
                </div>
                <h3>{t('bookings.empty_ads_title', 'Sherik e‘lonlari yo‘q')}</h3>
                <p>
                  {t(
                    'bookings.empty_ads_desc',
                    'Hozircha birorta xonadoshlik yoki sheriklik e‘loni joylashtirmagansiz.'
                  )}
                </p>
              </GlassCard>
            ) : (
              filteredMyAds.map((ad) => {
                const live = isLive(ad)
                return (
                  <GlassCard className="booking-card my-ad-card" key={ad.id}>
                    <div className="booking-card__media" onClick={() => navigate(`/listing/${ad.id}`)}>
                      <FallbackImage
                        src={ad.images?.[0]?.image_url || ad.images?.[0]}
                        alt={ad.title}
                        fallback={<Users size={28} />}
                        className="booking-card__img"
                      />
                      <div className="booking-card__badge-tag">
                        <span className="type-tag type-tag--roommate">
                          <Users size={12} /> {t('bookings.roommate_tag', 'Sheriklik e‘loni')}
                        </span>
                      </div>
                    </div>

                    <div className="booking-card__body">
                      <div className="card-top-row">
                        <div className="title-area">
                          <Link to={`/listing/${ad.id}`} className="listing-link">
                            <h2>{ad.title || "Sheriklik e'loni"}</h2>
                          </Link>
                          {ad.address && (
                            <p className="location-text">
                              <MapPin size={13} />
                              <span>{[ad.district, ad.region, ad.address].filter(Boolean).join(', ')}</span>
                            </p>
                          )}
                        </div>
                        <div className="status-area">
                          <span className={`booking-status-badge booking-status-badge--${live ? 'confirmed' : 'cancelled'}`}>
                            {live ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                            <span>{live ? t('bookings.active', 'Faol') : t('bookings.closed', 'Yopiq')}</span>
                          </span>
                        </div>
                      </div>

                      <div className="booking-meta-chips">
                        <div className="meta-chip">
                          <Users size={14} className="chip-icon" />
                          <div className="chip-content">
                            <span className="chip-label">{t('bookings.spaces', 'Bo‘sh joy')}:</span>
                            <span className="chip-value"><strong>{ad.available_spaces} ta o‘rin</strong></span>
                          </div>
                        </div>

                        {ad.price && (
                          <div className="meta-chip meta-chip--price">
                            <Coins size={14} className="chip-icon" />
                            <div className="chip-content">
                              <span className="chip-label">Oylik to‘lov:</span>
                              <span className="chip-value price-highlight">${ad.price}/oy</span>
                            </div>
                          </div>
                        )}

                        {ad.expires_at && (
                          <div className="meta-chip">
                            <Calendar size={14} className="chip-icon" />
                            <div className="chip-content">
                              <span className="chip-label">Amal qilish muddati:</span>
                              <span className="chip-value">{formatDate(ad.expires_at)} gacha</span>
                            </div>
                          </div>
                        )}
                      </div>

                      {ad.description && (
                        <div className="booking-note-quote">
                          <MessageSquare size={14} className="quote-icon" />
                          <p className="quote-text">{ad.description}</p>
                        </div>
                      )}

                      <div className="card-actions-footer">
                        <Link
                          to={`/listing/${ad.id}`}
                          className="action-btn action-btn--view"
                        >
                          <ExternalLink size={14} />
                          <span>{t('bookings.btn_view_listing', "E'lonni ko‘rish")}</span>
                        </Link>

                        <button
                          type="button"
                          className="action-btn action-btn--cancel"
                          disabled={actionLoadingId === ad.id}
                          onClick={() => handleCloseAdConfirm(ad)}
                        >
                          <X size={14} />
                          <span>
                            {actionLoadingId === ad.id
                              ? 'Yuklanmoqda...'
                              : t('bookings.btn_close_ad', "E'lonni yopish")}
                          </span>
                        </button>
                      </div>
                    </div>
                  </GlassCard>
                )
              })
            )}
          </div>
        )}
      </div>

      {/* CONFIRMATION MODAL */}
      {confirmModal.isOpen && (
        <div className="bookings-modal-overlay" onClick={() => setConfirmModal({ ...confirmModal, isOpen: false })}>
          <div className="bookings-modal" onClick={(e) => e.stopPropagation()}>
            <div className="bookings-modal__icon">
              <AlertCircle size={28} />
            </div>
            <h3>{confirmModal.title}</h3>
            <p>{confirmModal.text}</p>
            <div className="bookings-modal__actions">
              <button
                type="button"
                className="modal-btn modal-btn--secondary"
                onClick={() => setConfirmModal({ ...confirmModal, isOpen: false })}
              >
                {t('bookings.confirm_no', 'Orqaga')}
              </button>
              <button
                type="button"
                className={`modal-btn modal-btn--primary ${confirmModal.danger ? 'modal-btn--danger' : ''}`}
                onClick={confirmModal.onConfirm}
              >
                {confirmModal.actionText || t('bookings.confirm_yes', 'Ha, davom etish')}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}