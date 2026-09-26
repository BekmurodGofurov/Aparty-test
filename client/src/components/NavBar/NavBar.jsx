import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useThemeStore } from '../../store/themeStore'
import { useTranslation } from 'react-i18next'
import { userService } from '../../services/userService'
import { notificationService } from '../../services/notificationService'
import { formatTimeAgo } from '../../utils/time'
import { api } from '../../services/api'
import { useCacheStore } from '../../store/cacheStore'
import { Bell, Home, LogOut, MessageCircle, Sun, Moon, User, Search, Menu, X, ChevronDown, MapPinned, Plus, Crown, LayoutDashboard } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import './NavBar.scss'

export function NavBar() {
  const { role, clear, accessToken } = useAuthStore()
  const clearCache = useCacheStore((s) => s.clearCache)
  const { t, i18n } = useTranslation()
  const { theme, toggleTheme } = useThemeStore()
  const location = useLocation()
  const navigate = useNavigate()

  const [userData,   setUserData]   = useState(null)
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifOpen, setNotifOpen] = useState(false)
  const [accountOpen, setAccountOpen] = useState(false)
  const [scrolled,   setScrolled]   = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [langOpen,   setLangOpen]   = useState(false)
  const isHomePage = location.pathname === '/'
  const isOnHero   = isHomePage && !scrolled

  const navRef      = useRef(null)
  const langRef     = useRef(null)
  const notifRef    = useRef(null)
  const accountRef  = useRef(null)
  const scrolledRef = useRef(false)

  // Close mobile menu on route change
  useEffect(() => { setMobileOpen(false) }, [location.pathname])

  // Scroll detection
  useEffect(() => {
    const onScroll = () => {
      const next = window.scrollY > 16
      if (next !== scrolledRef.current) {
        scrolledRef.current = next
        setScrolled(next)
      }
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Fetch user
  useEffect(() => {
    if (!accessToken) {
      setUserData(null)
      return
    }

    if (!userData) {
      userService.getCurrentUser()
        .then(data => setUserData(data))
        .catch(() => {})
    }
  }, [accessToken, userData])

  useEffect(() => {
    if (!accessToken) {
      setNotifications([])
      setUnreadCount(0)
      return undefined
    }

    let active = true
    const loadNotifications = () => {
      notificationService.getMyNotifications()
        .then((data) => {
          if (!active) return
          setNotifications(data.notifications || [])
          setUnreadCount(data.unread_count || 0)
        })
        .catch(() => {})
    }
    loadNotifications()
    const timer = window.setInterval(loadNotifications, 30000)
    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [accessToken, location.pathname])

  // Listen for user updates
  useEffect(() => {
    const handleUserUpdate = (e) => setUserData(e.detail)
    window.addEventListener('user-updated', handleUserUpdate)
    return () => window.removeEventListener('user-updated', handleUserUpdate)
  }, [])

  // Close language dropdown on outside click
  useEffect(() => {
    const handler = e => {
      if (langRef.current && !langRef.current.contains(e.target)) {
        setLangOpen(false)
      }
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotifOpen(false)
      }
      if (accountRef.current && !accountRef.current.contains(e.target)) {
        setAccountOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const changeLanguage = (lang) => {
    i18n.changeLanguage(lang)
    setLangOpen(false)
  }

  const currentLang = i18n.language?.substring(0, 2)?.toUpperCase() || 'UZ'

  const navClass = ({ isActive }) => isActive ? 'nav-link active' : 'nav-link'

  const currentRole = (userData?.rol || role || '').toLowerCase()
  const isBrokerRole = currentRole === 'makler' || currentRole === 'broker'
  const brokerBasePath = currentRole === 'broker' ? '/broker' : '/makler'
  const roleLink = currentRole === 'owner'  ? { to: '/owner',  label: t('nav.owner',  'Dashboard') }
                 : isBrokerRole ? { to: brokerBasePath, label: currentRole === 'broker' ? t('nav.broker', 'Broker') : t('nav.makler', 'Makler') }
                 : currentRole === 'admin'  ? { to: '/admin',  label: t('nav.admin',  'Admin') }
                 : currentRole === 'student' ? { to: '/my-bookings', label: t('nav.bookings', 'Bronlarim') }
                 : null
  const profilePath = currentRole === 'admin' ? '/admin/profile' : currentRole === 'owner' ? '/owner/profile' : isBrokerRole ? `${brokerBasePath}/profile` : '/profile'
  const dashboardPath = roleLink?.to || '/'

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout')
    } catch {
      // Local logout must always complete even when the API is unavailable.
    }
    setAccountOpen(false)
    setNotifOpen(false)
    setNotifications([])
    setUnreadCount(0)
    setUserData(null)
    clearCache()
    clear()
    navigate('/login', { replace: true })
  }

  const openNotification = async (notification) => {
    try {
      if (!notification.is_read) {
        await notificationService.markRead(notification.id)
      }
    } catch {
      // keep navigation responsive even if read-state update fails
    }
    setNotifOpen(false)
    setUnreadCount((count) => Math.max(0, count - (notification.is_read ? 0 : 1)))
    navigate(notification.target_url || '/messages')
  }

  return (
    <>
      {/* ── DESKTOP / TABLET NAVBAR ────────────────────────────────────── */}
      <header
        ref={navRef}
        className={`navbar ${scrolled ? 'scrolled' : ''} ${mobileOpen ? 'menu-open' : ''} ${isOnHero ? 'on-hero' : ''}`}
      >
        <div className="navbar-inner">
          {/* Brand */}
          <NavLink to="/" className="navbar-brand" aria-label="Aparty.uz — Home">
            <span className="brand-text">Aparty</span>
            <span className="brand-dot" aria-hidden />
            <span className="brand-suffix">.uz</span>
          </NavLink>

          {/* Desktop Links */}
          <nav className="navbar-links" aria-label="Main navigation">
            {currentRole && roleLink && (
              <NavLink 
                to={roleLink.to} 
                className={({ isActive }) => `role-badge ${currentRole} ${isActive ? 'active' : ''}`}
              >
                <span className="role-dot" aria-hidden="true" />
                {roleLink.label}
              </NavLink>
            )}
            {isBrokerRole && (
              <NavLink
                to={`${brokerBasePath}/subscription`}
                className={({ isActive }) => `role-badge subscription ${isActive ? 'active' : ''}`}
              >
                <Crown size={14} />
                {t('nav.subscription', 'Obuna')}
              </NavLink>
            )}
          </nav>

          {/* Desktop Controls */}
          <div className="navbar-controls">
            {/* Search shortcut */}
            <NavLink to="/search" className="ctrl-icon-btn search-btn-liquid" aria-label="Search">
              <Search size={18} />
            </NavLink>

            {/* Map shortcut */}
            <NavLink
              to="/map"
              className={({ isActive }) => `ctrl-icon-btn search-btn-liquid ${isActive ? 'active' : ''}`}
              aria-label="Map"
              title={t('nav.map', 'Xarita')}
            >
              <MapPinned size={18} />
            </NavLink>

            {/* Language switcher */}
            <div className="lang-dropdown" ref={langRef}>
              <button
                className="ctrl-lang-btn"
                onClick={() => setLangOpen(v => !v)}
                aria-label="Change language"
                aria-expanded={langOpen}
              >
                <span>{currentLang}</span>
                <ChevronDown size={14} className={langOpen ? 'rotated' : ''} />
              </button>
              <AnimatePresence>
                {langOpen && (
                  <motion.div
                    className="lang-menu"
                    initial={{ opacity: 0, y: -8, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0,  scale: 1 }}
                    exit={{    opacity: 0, y: -8, scale: 0.96 }}
                    transition={{ duration: 0.18, ease: [0.23, 1, 0.32, 1] }}
                  >
                    {['uz', 'ru', 'en'].map(lang => (
                      <button
                        key={lang}
                        className={`lang-option ${currentLang.toLowerCase() === lang ? 'active' : ''}`}
                        onClick={() => changeLanguage(lang)}
                      >
                        {lang.toUpperCase()}
                        {lang === 'uz' && <span className="lang-name">O'zbek</span>}
                        {lang === 'ru' && <span className="lang-name">Русский</span>}
                        {lang === 'en' && <span className="lang-name">English</span>}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Theme toggle */}
            <motion.button
              className="ctrl-icon-btn theme-btn"
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.92 }}
            >
              <AnimatePresence mode="wait">
                {theme === 'dark' ? (
                  <motion.span key="sun" initial={{ rotate: -30, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 30, opacity: 0 }} transition={{ duration: 0.2 }}>
                    <Sun size={18} />
                  </motion.span>
                ) : (
                  <motion.span key="moon" initial={{ rotate: 30, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -30, opacity: 0 }} transition={{ duration: 0.2 }}>
                    <Moon size={18} />
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>

            {currentRole && (
              <>
                <NavLink to="/messages" className="ctrl-icon-btn messages-nav-btn" aria-label="Messages">
                  <MessageCircle size={18} />
                </NavLink>
                <div className="notification-dropdown" ref={notifRef}>
                  <button className="ctrl-icon-btn notification-btn" type="button" onClick={() => setNotifOpen((v) => !v)} aria-label="Notifications">
                    <Bell size={18} />
                    {unreadCount > 0 && <span className="notification-count">{unreadCount > 9 ? '9+' : unreadCount}</span>}
                  </button>
                  <AnimatePresence>
                    {notifOpen && (
                      <motion.div
                        className="notification-menu"
                        initial={{ opacity: 0, y: 15, scale: 0.95, filter: 'blur(10px)' }}
                        animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
                        exit={{ opacity: 0, y: 15, scale: 0.95, filter: 'blur(10px)' }}
                        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                      >
                        <div className="notification-menu__head">
                          <div className="head-left">
                            <Bell size={16} className="head-icon" />
                            <strong>{t('nav.notifications', 'Bildirishnomalar')}</strong>
                            {unreadCount > 0 && <span className="head-badge">{unreadCount}</span>}
                          </div>
                          {unreadCount > 0 && (
                            <button 
                              type="button" 
                              className="mark-all-btn"
                              onClick={() => notificationService.markAllRead().then(() => setUnreadCount(0))}
                            >
                              O'qildi
                            </button>
                          )}
                        </div>

                        <div className="notification-list">
                          {notifications.length === 0 ? (
                            <div className="notification-empty">
                              <div className="empty-icon-shell">
                                <Bell size={32} />
                                <div className="pulse-ring" />
                              </div>
                              <strong>Hozircha bo'sh</strong>
                              <p>Yangi bildirishnomalar shu yerda ko'rinadi</p>
                            </div>
                          ) : (
                            notifications.slice(0, 8).map((item) => (
                              <button
                                type="button"
                                className={`notification-item ${item.is_read ? '' : 'unread'}`}
                                key={item.id}
                                onClick={() => openNotification(item)}
                              >
                                <div className="notif-accent" />
                                <div className="notif-content">
                                  <div className="notif-top">
                                    <span className="notif-title">{item.title}</span>
                                    <span className="notif-time">{formatTimeAgo(item.created_at)}</span>
                                  </div>
                                  {item.body && <p className="notif-body">{item.body}</p>}
                                </div>
                              </button>
                            ))
                          )}
                        </div>

                        <div className="notification-footer">
                          <button className="view-all-notif">Barchasini ko'rish</button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </>
            )}

            {/* Auth area */}
            {!currentRole ? (
              <div className="auth-btns">
                <NavLink to="/login" className="btn-nav-ghost">
                  {t('nav.login', 'Kirish')}
                </NavLink>
                <NavLink to="/register" className="btn-nav-primary">
                  {t('nav.register', "Ro'yxatdan o'tish")}
                </NavLink>
              </div>
            ) : (
              <div className="user-area" ref={accountRef}>
                <button
                  type="button"
                  className="user-chip"
                  aria-label="Account menu"
                  aria-expanded={accountOpen}
                  onClick={() => setAccountOpen((value) => !value)}
                >
                  <div className="user-avatar">
                    {userData?.rasm_url
                      ? <img src={userData.rasm_url} alt={userData.ism} />
                      : <span>{userData?.ism?.charAt(0)?.toUpperCase() || <User size={16} />}</span>
                    }
                  </div>
                  <span className="user-name">
                    {currentRole === 'admin' 
                      ? 'Administrator' 
                      : (userData?.ism || t('nav.profile', 'Profil'))
                    }
                  </span>
                  <ChevronDown size={14} className={accountOpen ? 'rotated' : ''} />
                </button>
                <AnimatePresence>
                  {accountOpen && (
                    <motion.div
                      className="account-menu"
                      initial={{ opacity: 0, y: -8, scale: 0.96 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -8, scale: 0.96 }}
                      transition={{ duration: 0.18 }}
                    >
                      <NavLink to={dashboardPath} onClick={() => setAccountOpen(false)}>
                        <LayoutDashboard size={16} />
                        Dashboard
                      </NavLink>
                      <NavLink to={profilePath} onClick={() => setAccountOpen(false)}>
                        <User size={16} />
                        {t('nav.profile', 'Profil')}
                      </NavLink>
                    </motion.div>
                  )}
                </AnimatePresence>
                <motion.button
                  className="ctrl-icon-btn logout-btn"
                  onClick={handleLogout}
                  aria-label="Logout"
                  whileHover={{ scale: 1.08 }}
                  whileTap={{ scale: 0.92 }}
                >
                  <LogOut size={18} />
                </motion.button>
              </div>
            )}

            {/* Hamburger */}
            <motion.button
              className="ctrl-icon-btn hamburger"
              onClick={() => setMobileOpen(v => !v)}
              aria-label="Toggle menu"
              aria-expanded={mobileOpen}
              whileTap={{ scale: 0.9 }}
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </motion.button>
          </div>
        </div>

        {/* ── MOBILE MENU ─────────────────────────────────────────────── */}
        <AnimatePresence>
          {mobileOpen && (
            <motion.div
              className="mobile-menu"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{    opacity: 0, height: 0 }}
              transition={{ duration: 0.28, ease: [0.23, 1, 0.32, 1] }}
            >
              <div className="mobile-menu-inner">
                <NavLink to="/search" className={navClass} onClick={() => setMobileOpen(false)}>
                  <Search size={16} /> {t('nav.search', 'Qidiruv')}
                </NavLink>
                {currentRole && roleLink && (
                  <NavLink to={roleLink.to} className={navClass} onClick={() => setMobileOpen(false)}>
                    {roleLink.label}
                  </NavLink>
                )}
                {isBrokerRole && (
                  <NavLink to={`${brokerBasePath}/subscription`} className={navClass} onClick={() => setMobileOpen(false)}>
                    <Crown size={16} /> {t('nav.subscription', 'Obuna')}
                  </NavLink>
                )}
                {currentRole && (
                  <NavLink to="/messages" className={navClass} onClick={() => setMobileOpen(false)}>
                    <MessageCircle size={16} /> Messages
                  </NavLink>
                )}
                {!currentRole ? (
                  <>
                    <NavLink to="/login"    className="nav-link" onClick={() => setMobileOpen(false)}>{t('nav.login',    'Kirish')}</NavLink>
                    <NavLink to="/register" className="nav-link mobile-cta" onClick={() => setMobileOpen(false)}>{t('nav.register', "Ro'yxatdan o'tish")}</NavLink>
                  </>
                ) : (
                  <>
                    <NavLink to={profilePath} className={navClass} onClick={() => setMobileOpen(false)}>
                      <User size={16} /> {t('nav.profile', 'Profil')}
                    </NavLink>
                    <button className="nav-link nav-logout" onClick={() => { handleLogout(); setMobileOpen(false) }}>
                      <LogOut size={16} /> {t('nav.logout', 'Chiqish')}
                    </button>
                  </>
                )}

                {/* Mobile lang switcher */}
                <div className="mobile-langs">
                  {['uz', 'ru', 'en'].map(lang => (
                    <button
                      key={lang}
                      className={`mobile-lang-btn ${currentLang.toLowerCase() === lang ? 'active' : ''}`}
                      onClick={() => changeLanguage(lang)}
                    >
                      {lang.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* ── MOBILE BOTTOM NAV ──────────────────────────────────────────── */}
      <nav className="bottom-nav" aria-label="Mobile navigation">
        <NavLink className={({ isActive }) => `bottom-item ${isActive ? 'active' : ''}`} to="/" end>
          <Home className="bottom-icon" size={21} />
          <span>{t('nav.home', 'Bosh')}</span>
        </NavLink>
        <NavLink className={({ isActive }) => `bottom-item ${isActive ? 'active' : ''}`} to="/search">
          <Search className="bottom-icon" size={21} />
          <span>{t('nav.search', 'Qidiruv')}</span>
        </NavLink>
        <NavLink className={({ isActive }) => `bottom-item ${isActive ? 'active' : ''}`} to="/map">
          <MapPinned className="bottom-icon" size={21} />
          <span>{t('nav.map', 'Xarita')}</span>
        </NavLink>
        {(currentRole === 'owner' || isBrokerRole) && (
          <NavLink
            className={({ isActive }) => `bottom-item ${isActive ? 'active' : ''}`}
            to={isBrokerRole ? `${brokerBasePath}/create` : '/owner/create'}
          >
            <Plus className="bottom-icon add-icon" size={23} />
            <span>{t('nav.listing', "E'lon")}</span>
          </NavLink>
        )}
        {currentRole && (
          <NavLink className={({ isActive }) => `bottom-item ${isActive ? 'active' : ''}`} to="/messages">
            <MessageCircle className="bottom-icon" size={21} />
            <span>Messages</span>
          </NavLink>
        )}
        <NavLink
          className={({ isActive }) => `bottom-item ${isActive ? 'active' : ''}`}
          to={currentRole ? profilePath : '/login'}
        >
          <div className="bottom-avatar">
            {currentRole && userData?.rasm_url
              ? <img src={userData.rasm_url} alt="" />
              : <User className="bottom-icon" size={20} />
            }
          </div>
          <span>{currentRole ? t('nav.profile', 'Profil') : t('nav.login', 'Kirish')}</span>
        </NavLink>
      </nav>
    </>
  )
}
