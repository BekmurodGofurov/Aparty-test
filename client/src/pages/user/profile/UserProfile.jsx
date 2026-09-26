import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import {
  User, Phone, ShieldCheck,
  Edit2, LogOut, Camera, Star,
  Home, Send, Lock, Heart,
  ChevronRight, Smartphone,
  Monitor, Cpu, MapPin, Clock, Trash2,
  Settings, HelpCircle, AlertCircle,
  MessageSquare, Bell, UserCheck, DollarSign
} from 'lucide-react'
import { useAuthStore } from '../../../store/authStore'
import { Button, ScrollReveal, StaggerContainer, StaggerItem, GlassCard, Badge } from '../../../components/ui/PremiumComponents'
import PremiumLoader from '../../../components/shared/PremiumLoader/PremiumLoader'
import { userService } from '../../../services/userService'
import { favoritesService } from '../../../services/favoritesService'
import { getMyRentalRequests, getMyRooms, getRentalRequestMessages } from '../../../services/listingService'
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
  const { t } = useTranslation()
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
  const [sentRequests, setSentRequests] = useState([])
  const [requestMessages, setRequestMessages] = useState([])
  const [rooms, setRooms] = useState([])
  const [loading, setLoading] = useState(true)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editMode, setEditMode] = useState('all')

  const fetchProfile = async () => {
    try {
      setLoading(true)
      const [data, favorites, requests, roomData] = await Promise.all([
        userService.getCurrentUser().catch(() => null),
        favoritesService.getMyFavorites().catch(() => []),
        getMyRentalRequests().catch(() => []),
        getMyRooms().catch(() => []),
      ])
      if (data) {
        setUserData(prev => ({
          ...prev,
          ...data,
          join_date: formatDate(data.created_at),
          stats: {
            saved: Array.isArray(favorites) ? favorites.length : 0,
            requests: Array.isArray(requests) ? requests.length : 0,
            rooms: Array.isArray(roomData) ? roomData.length : 0,
          },
        }))
        // Cache basic info for next instant load
        if (data.ism) localStorage.setItem('userName', data.ism)
        if (data.telefon) localStorage.setItem('userPhone', data.telefon)
      }
      setSavedHomes(Array.isArray(favorites) ? favorites : [])
      setSentRequests(Array.isArray(requests) ? requests : [])
      setRooms(Array.isArray(roomData) ? roomData : [])
      const messageGroups = await Promise.all(
        (Array.isArray(requests) ? requests : [])
          .slice(0, 6)
          .map((request) => getRentalRequestMessages(request.id).catch(() => []))
      )
      setRequestMessages(
        messageGroups
          .flat()
          .filter((message) => Number(message.sender_id) !== Number(data?.id ?? localStorage.getItem('userId')))
          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
          .slice(0, 6)
      )
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

    if (role === 'admin') {
      navigate('/admin/profile', { replace: true })
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

  const handleLogout = () => {
    clearAuth()
    navigate('/')
  }

  const openEdit = (mode = 'all') => {
    setEditMode(mode)
    setShowEditModal(true)
  }

  const activeRoom = useMemo(() => rooms.find((room) => room.is_active) || rooms[0], [rooms])
  const hasRoom = Boolean(activeRoom)
  const sentRequestsPreview = sentRequests.slice(0, 4)
  const savedHomesPreview = savedHomes.slice(0, 4)

  return (
    <main className="user-profile-premium">
      <div className="profile-content-wrapper">

        {/* ── HERO SECTION ──────────────────────────── */}
        <section className="hero-profile-section">
          <ScrollReveal>
            <div className="unified-profile-card">
              <div className="card-inner">
                <div className="user-identity">
                  <div className="avatar-container" onClick={() => openEdit('all')}>
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
                  <Button variant="primary" className="btn-edit" onClick={() => openEdit('all')}>
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
              <div className={`premium-stat-card neon-cyan ${hasRoom ? '' : 'is-disabled'}`} onClick={() => hasRoom && navigate('/my-room')}>
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

            <section className="content-block reviews-section">
              <div className="block-header">
                <h2><MessageSquare size={20}/> Xabarlar</h2>
              </div>
              <div className="reviews-stack">
                {requestMessages.length === 0 ? (
                  <GlassCard className="profile-empty-card">
                    Hali owner yoki brokerdan xabar kelmagan.
                  </GlassCard>
                ) : requestMessages.map(message => (
                  <GlassCard className="mini-review-card request-preview-card" key={message.id}>
                    <div className="rev-top">
                      <div className="apt-info">
                        <MessageSquare size={14} className="apt-icon"/>
                        <strong className="apt-name">{message.sender_name}</strong>
                      </div>
                      <span>{formatDate(message.created_at)}</span>
                    </div>
                    <p className="rev-comment">"{message.text}"</p>
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
                ) : sentRequestsPreview.map(request => (
                  <GlassCard className="mini-review-card request-preview-card" key={request.id} onClick={() => navigate(`/listing/${request.listing_id}`)}>
                    <div className="rev-top">
                      <div className="apt-info">
                        <Home size={14} className="apt-icon"/>
                        <strong className="apt-name">{getListingTitle(request.listing)}</strong>
                      </div>
                      <span className={`request-status request-status--${request.status}`}>{request.status}</span>
                    </div>
                    <p className="rev-comment">"{request.message || 'So‘rov yuborilgan'}"</p>
                    <div className="rev-footer">
                      <span>{formatDate(request.created_at)}</span>
                      <span>${request.listing?.price}/oy</span>
                    </div>
                  </GlassCard>
                ))}
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
                        <strong className="apt-name">{getListingTitle(activeRoom.listing)}</strong>
                      </div>
                      <button className="btn-terminate" type="button" onClick={() => navigate('/my-room')}>Ochish</button>
                    </div>
                    <div className="room-profile-meta">
                      <span><DollarSign size={14}/> ${activeRoom.price}/oy</span>
                      <span><Clock size={14}/> To'lovga {activeRoom.payment_days_left} kun qoldi</span>
                      <span><UserCheck size={14}/> {activeRoom.owner.full_name}</span>
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
              <h3 className="sidebar-title">Sozlamalar</h3>
              <div className="settings-stack">
                <div className="setting-action-card" onClick={() => openEdit('password')}>
                  <div className="icon-wrap"><Lock size={18}/></div>
                  <div className="text-wrap">
                    <span>Parolni o'zgartirish</span>
                    <p>Hisobingizni himoyalang</p>
                  </div>
                  <ChevronRight size={16} className="chevron"/>
                </div>
                <div className="setting-action-card" onClick={() => openEdit('phone')}>
                  <div className="icon-wrap"><Smartphone size={18}/></div>
                  <div className="text-wrap">
                    <span>Telefonni yangilash</span>
                    <p>Yangi raqamga o'tish</p>
                  </div>
                  <ChevronRight size={16} className="chevron"/>
                </div>
                <div className="setting-action-card">
                  <div className="icon-wrap"><Send size={18}/></div>
                  <div className="text-wrap">
                    <span>Telegram Status</span>
                    <p>Bot bilan bog'lanish: {userData?.tg_connected ? 'Faol' : 'O\'chirilgan'}</p>
                  </div>
                  <Badge variant={userData?.tg_connected ? "success" : "outline"} size="sm">
                    {userData?.tg_connected ? "Uzluksiz" : "Bog'lanmagan"}
                  </Badge>
                </div>
              </div>
            </section>

            <section className="sidebar-group help-section">
              <h3 className="sidebar-title">Yordam</h3>
              <div className="support-card-premium">
                <div className="support-bg"></div>
                <h4>Yordam kerakmi?</h4>
                <p>AI yordamchimiz sizning barcha savollaringizga javob beradi.</p>
                <button className="btn-chat-ai" onClick={() => window.dispatchEvent(new CustomEvent('open-ai-chat'))}>
                  <MessageSquare size={18}/> <span>AI Chat Bot</span>
                </button>
              </div>
            </section>

            <section className="sidebar-group danger-zone-group">
              <h3 className="sidebar-title">Havfli hudud</h3>
              <div className="danger-zone-card">
                <div className="danger-item" onClick={handleLogout}>
                  <LogOut size={18}/> <span>Tizimdan chiqish</span>
                </div>
                <div className="danger-item delete">
                  <Trash2 size={18}/> <span>Hisobni o'chirish</span>
                </div>
                <div className="warning-note">
                  <AlertCircle size={12}/>
                  <span>Diqqat! Hisobni o'chirishni ortga qaytarib bo'lmaydi.</span>
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
        mode={editMode}
      />
    </main>
  )
}
