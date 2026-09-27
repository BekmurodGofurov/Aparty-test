import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Phone, ShieldCheck, Edit2, LogOut, Camera,
  Home, Send, Heart, ChevronRight,
  Monitor, Cpu, Clock,
  MessageSquare, UserCheck
} from 'lucide-react'
import { useAuthStore } from '../../../store/authStore'
import { Button, ScrollReveal, StaggerContainer, StaggerItem, GlassCard, Badge } from '../../../components/ui/PremiumComponents'
import PremiumLoader from '../../../components/shared/PremiumLoader/PremiumLoader'
import { authService } from '../../../services/authService'
import { userService } from '../../../services/userService'
import { favoritesService } from '../../../services/favoritesService'
import { getMyBookings } from '../../../services/listingService'
import { activeRentals, toRequest } from '../../../utils/bookingAdapters'
import { profileStats } from '../../../utils/profileStats'
import { ProfileEditModal } from './ProfileEditModal'
import './UserProfile.scss'

const formatDate = (value) => {
  if (!value) return '-'
  return new Intl.DateTimeFormat('uz-UZ', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

const getListingTitle = (listing = {}) => (
  [listing.address, listing.district, listing.region]
    .filter(Boolean)
    .join(', ') || 'Manzil kiritilmagan'
)

const getCurrentSession = () => {
  const agent = navigator.userAgent
  const browser = agent.includes('Chrome') ? 'Chrome' : agent.includes('Safari') ? 'Safari' : agent.includes('Firefox') ? 'Firefox' : 'Browser'
  const device = /iPhone|Android|Mobile/i.test(agent) ? 'Mobile device' : navigator.platform || 'Current device'
  return {
    id: 'current',
    name: device,
    browser,
    location: 'Aparty web',
    time: 'Hozir faol',
    current: true,
  }
}

export function UserProfile() {
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const role = useAuthStore((s) => s.role)
  const clearAuth = useAuthStore((s) => s.clear)

  const initialData = {
    id: localStorage.getItem('userId') || '',
    ism: localStorage.getItem('userName') || '',
    telefon: localStorage.getItem('userPhone') || '',
    tg_connected: false,
    verified: false,
    created_at: null,
    stats: { saved: 0, requests: 0, rooms: 0 },
  }

  const [userData, setUserData] = useState(initialData)
  const [sessions] = useState([getCurrentSession()])
  const [savedHomes, setSavedHomes] = useState([])
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [showEditModal, setShowEditModal] = useState(false)

  const fetchProfile = async () => {
    try {
      setLoading(true)
      const [data, favorites, myBookings] = await Promise.all([
        userService.getCurrentUser().catch(() => null),
        favoritesService.getMyFavorites().catch(() => []),
        getMyBookings().catch(() => []),
      ])
      const savedList = Array.isArray(favorites) ? favorites : []
      const bookingList = Array.isArray(myBookings) ? myBookings : []
      if (data) {
        setUserData(prev => ({
          ...prev,
          ...data,
          join_date: formatDate(data.created_at),
          stats: profileStats({ favorites: savedList, bookings: bookingList }),
        }))
        // Cache basic info for next instant load
        if (data.ism) localStorage.setItem('userName', data.ism)
        if (data.telefon) localStorage.setItem('userPhone', data.telefon)
      }
      setSavedHomes(savedList)
      setBookings(bookingList)
    } catch (err) {
      console.error('Fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!accessToken) {
      navigate('/login')
      return
    }

    fetchProfile()
  }, [accessToken, navigate, role])

  // Listen for user updates from modal or other components
  useEffect(() => {
    const handleUpdate = (e) => {
      if (e.detail) {
        setUserData(prev => ({ ...prev, ...e.detail }))
      } else {
        fetchProfile()
      }
    }
    window.addEventListener('user-updated', handleUpdate)
    return () => window.removeEventListener('user-updated', handleUpdate)
  }, [])

  const handleLogout = async () => {
    try {
      await authService.logout()
    } catch {
      // Signing out locally must always work, even when the API is unavailable.
    }
    clearAuth()
    navigate('/')
  }

  const activeRoom = useMemo(() => activeRentals(bookings)[0], [bookings])
  const hasRoom = Boolean(activeRoom)
  const sentRequestsPreview = bookings.slice(0, 4)
  const savedHomesPreview = savedHomes.slice(0, 4)

  if (loading && !userData.ism) return <PremiumLoader />

  return (
    <main className="user-profile-premium">
      <div className="profile-content-wrapper">

        {/* ── HERO SECTION ──────────────────────────── */}
        <section className="hero-profile-section">
          <ScrollReveal>
            <div className="unified-profile-card">
              <div className="card-inner">
                <div className="user-identity">
                  <div className="avatar-container" onClick={() => setShowEditModal(true)}>
                    <div className="avatar-ring">
                      {userData?.rasm_url ? (
                        <img src={userData.rasm_url} alt={userData.ism} />
                      ) : (
                        <div className="avatar-placeholder">{userData?.ism?.charAt(0)}</div>
                      )}
                      <div className="avatar-overlay">
                        <Camera size={24} />
                      </div>
                    </div>
                  </div>

                  <div className="user-details">
                    <div className="name-row">
                      <h1>{userData?.ism}</h1>
                      <div className="badges-row">
                        {userData?.verified && (
                          <Badge variant="success" className="verified-badge">
                            <ShieldCheck size={14}/> <span>Tasdiqlangan</span>
                          </Badge>
                        )}
                        <Badge variant="outline" className="role-badge">
                          <UserCheck size={14}/>
                      <span>
                            {role === 'owner' ? 'Uy egasi' : role === 'makler' ? 'Makler' : 'Guest user'}
                          </span>
                        </Badge>
                      </div>
                    </div>
                    <div className="meta-grid">
                      <div className="meta-item"><Phone size={14}/> <span>{userData?.telefon}</span></div>
                      <div className="meta-item"><Clock size={14}/> <span>A'zo: {userData?.join_date || formatDate(userData?.created_at)}</span></div>
                    </div>
                  </div>
                </div>

                <div className="card-actions">
                  <Button variant="primary" className="btn-edit" onClick={() => setShowEditModal(true)}>
                    <Edit2 size={16}/> <span>Tahrirlash</span>
                  </Button>
                </div>
              </div>
            </div>
          </ScrollReveal>
        </section>

        {/* ── STATS SECTION ─────────────────────────── */}
        <section className="stats-cards-section">
          <StaggerContainer className="stats-grid">
            <StaggerItem>
              <div className="premium-stat-card neon-blue">
                <div className="icon-box"><Heart size={24}/></div>
                <div className="stat-info">
                  <span className="number">{userData?.stats.saved}</span>
                  <p className="label">Saqlangan uylar</p>
                </div>
                <div className="card-glow"></div>
              </div>
            </StaggerItem>
            <StaggerItem>
              <div className="premium-stat-card neon-purple">
                <div className="icon-box"><MessageSquare size={24}/></div>
                <div className="stat-info">
                  <span className="number">{userData?.stats.requests}</span>
                  <p className="label">Yuborilgan so'rovlar</p>
                </div>
                <div className="card-glow"></div>
              </div>
            </StaggerItem>
            <StaggerItem>
              <div className={`premium-stat-card neon-cyan ${hasRoom ? '' : 'is-disabled'}`} onClick={() => hasRoom && navigate(`/listing/${activeRoom.listing_id}`)}>
                <div className="icon-box"><Home size={24}/></div>
                <div className="stat-info">
                  <span className="number">{userData?.stats.rooms}</span>
                  <p className="label">Mening kvartiram</p>
                </div>
                <div className="card-glow"></div>
              </div>
            </StaggerItem>
          </StaggerContainer>
        </section>

        {/* ── MAIN GRID ─────────────────────────────── */}
        <div className="main-content-layout">

          <div className="content-primary-col">
            {/* ACTIVE SESSIONS */}
            <section className="content-block">
              <div className="block-header">
                <h2><Monitor size={20}/> Kirilgan qurilmalar</h2>
              </div>
              <div className="devices-grid">
                {sessions.map(session => (
                  <GlassCard className="session-card" key={session.id}>
                    <div className="session-icon">
                      <Cpu size={20}/>
                    </div>
                    <div className="session-body">
                      <div className="top">
                        <span className="device-name">{session.name}</span>
                        {session.current && <span className="status-badge">Hozirgi</span>}
                      </div>
                      <div className="meta">
                        <span>{session.browser}</span>
                        <span className="sep">•</span>
                        <span>{session.location}</span>
                        <span className="sep">•</span>
                        <span className="time">{session.time}</span>
                      </div>
                    </div>
                  </GlassCard>
                ))}
              </div>
            </section>

            {/* SAVED HOMES */}
            <section className="content-block">
              <div className="block-header">
                <h2><Heart size={20}/> Saqlangan uylar</h2>
              </div>
              <div className="devices-grid">
                {savedHomesPreview.length === 0 ? (
                  <GlassCard className="profile-empty-card">
                    Hali saqlangan uy yo'q. Yoqtirgan kvartirangizni yurakcha orqali saqlang.
                  </GlassCard>
                ) : savedHomesPreview.map((listing) => (
                  <GlassCard className="session-card profile-listing-card" key={listing.id} onClick={() => navigate(`/listing/${listing.id}`)}>
                    <div className="session-icon listing-thumb">
                      {listing.images?.[0] ? <img src={listing.images[0]} alt="" /> : <Home size={20}/>}
                    </div>
                    <div className="session-body">
                      <div className="top">
                        <span className="device-name">{getListingTitle(listing)}</span>
                        {listing.is_premium && <span className="status-badge">Premium</span>}
                      </div>
                      <div className="meta">
                        <span>{listing.rooms_count} xona</span>
                        <span className="sep">•</span>
                        <span>{listing.available_spaces} bo'sh joy</span>
                        <span className="sep">•</span>
                        <span className="time">${listing.price}/oy</span>
                      </div>
                    </div>
                    <ChevronRight size={18} />
                  </GlassCard>
                ))}
              </div>
            </section>

            {/* REQUESTS SECTION */}
            <section className="content-block reviews-section">
              <div className="block-header">
                <h2><MessageSquare size={20}/> Yuborilgan so'rovlar</h2>
              </div>
              <div className="reviews-stack">
                {sentRequestsPreview.length === 0 ? (
                  <GlassCard className="profile-empty-card">
                    Hali hech qaysi reklamaga so'rov yuborilmagan.
                  </GlassCard>
                ) : sentRequestsPreview.map(booking => {
                  const { status, statusLabel } = toRequest(booking)
                  return (
                    <GlassCard className="mini-review-card request-preview-card" key={booking.id} onClick={() => navigate('/my-bookings')}>
                      <div className="rev-top">
                        <div className="apt-info">
                          <Home size={14} className="apt-icon"/>
                          <strong className="apt-name">{booking.listing_title || "E'lon"}</strong>
                        </div>
                        <span className={`request-status request-status--${status}`}>{statusLabel}</span>
                      </div>
                      <p className="rev-comment">"{booking.message || 'So‘rov yuborilgan'}"</p>
                      <div className="rev-footer">
                        <span>{formatDate(booking.start_date)} — {formatDate(booking.end_date)}</span>
                      </div>
                    </GlassCard>
                  )
                })}
              </div>
            </section>

            <section className="content-block reviews-section">
              <div className="block-header">
                <h2><Home size={20}/> Mening kvartiram</h2>
              </div>
              <GlassCard className={`mini-review-card my-room-profile-card ${hasRoom ? '' : 'disabled'}`}>
                {hasRoom ? (
                  <>
                    <div className="rev-top">
                      <div className="apt-info">
                        <Home size={14} className="apt-icon"/>
                        <strong className="apt-name">{activeRoom.listing.address || "E'lon"}</strong>
                      </div>
                      <button className="btn-terminate" type="button" onClick={() => navigate(`/listing/${activeRoom.listing_id}`)}>Ochish</button>
                    </div>
                    <div className="room-profile-meta">
                      <span><Clock size={14}/> {formatDate(activeRoom.start_date)} — {formatDate(activeRoom.end_date)}</span>
                    </div>
                  </>
                ) : (
                  <div className="disabled-room-copy">
                    <Home size={22}/>
                    <div>
                      <strong>Mening kvartiram hozircha yo'q</strong>
                      <p>Owner yoki broker so'rovingizni qabul qilsa, bu bo'lim avtomatik ochiladi.</p>
                    </div>
                  </div>
                )}
              </GlassCard>
            </section>
          </div>

          <aside className="sticky-sidebar-col">
            <section className="sidebar-group">
              <h3 className="sidebar-title">Aloqa</h3>
              <div className="settings-stack">
                <div className="setting-action-card">
                  <div className="icon-wrap"><Send size={18}/></div>
                  <div className="text-wrap">
                    <span>Telegram</span>
                    <p>
                      {userData?.telegram_username
                        ? `@${userData.telegram_username}`
                        : "Username yo'q: e'lonlarda faqat telefon ko'rinadi"}
                    </p>
                  </div>
                  <Badge variant={userData?.telegram_username ? 'success' : 'outline'} size="sm">
                    {userData?.telegram_username ? 'Ulangan' : "Yo'q"}
                  </Badge>
                </div>
              </div>
            </section>

            <section className="sidebar-group danger-zone-group">
              <h3 className="sidebar-title">Hisob</h3>
              <div className="danger-zone-card">
                <div className="danger-item" onClick={handleLogout}>
                  <LogOut size={18}/> <span>Tizimdan chiqish</span>
                </div>
              </div>
            </section>
          </aside>

        </div>
      </div>

      <ProfileEditModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        userData={userData}
        onUpdate={(u) => setUserData(prev => ({...prev, ...u}))}
      />
    </main>
  )
}
