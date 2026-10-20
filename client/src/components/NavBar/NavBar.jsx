import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useThemeStore } from '../../store/themeStore'
import { useTranslation } from 'react-i18next'
import { userService } from '../../services/userService'
import { notificationService } from '../../services/notificationService'
import { formatTimeAgo } from '../../utils/time'
import { api } from '../../services/api'
import { FallbackImage } from '../ui/FallbackImage'
import { ArrowUpRight, Bell, Globe2, Home, LogOut, Sun, Moon, User, Search, Menu, X, ChevronDown, MapPinned, Plus, LayoutDashboard } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import './NavBar.scss'

const NOTIFICATION_POLL_MS = 60000

export function NavBar() {
  const role = useAuthStore((state) => state.role)
  const clear = useAuthStore((state) => state.clear)
  const accessToken = useAuthStore((state) => state.accessToken)
  const { t, i18n } = useTranslation()
  const { theme, toggleTheme } = useThemeStore()
  const location = useLocation()
  const navigate = useNavigate()
  const reduceMotion = useReducedMotion()

  const [userData,   setUserData]   = useState(null)
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifOpen, setNotifOpen] = useState(false)
  const [accountOpen, setAccountOpen] = useState(false)
  const [scrolled,   setScrolled]   = useState(false)
  const [heroInView, setHeroInView] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [langOpen,   setLangOpen]   = useState(false)
  const isHomePage = location.pathname === '/'
  const isOnHero   = isHomePage && heroInView

  const navRef      = useRef(null)
  const langRef     = useRef(null)
  const notifRef    = useRef(null)
  const accountRef  = useRef(null)
  const scrolledRef = useRef(false)
  const menuButtonRef = useRef(null)

  // Close mobile menu on route change
  useEffect(() => { setMobileOpen(false) }, [location.pathname])

  useEffect(() => {
    const mobileViewport = window.matchMedia('(max-width: 1100px)')
    const closeOnDesktop = (event) => { if (!event.matches) setMobileOpen(false) }
    mobileViewport.addEventListener('change', closeOnDesktop)
    return () => mobileViewport.removeEventListener('change', closeOnDesktop)
  }, [])

  useEffect(() => {
    if (!mobileOpen) return undefined
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = previousOverflow }
  }, [mobileOpen])

  useEffect(() => {
    const closeOnEscape = (event) => {
      if (event.key !== 'Escape') return
      setMobileOpen(false)
      setLangOpen(false)
      setNotifOpen(false)
      setAccountOpen(false)
      if (mobileOpen) menuButtonRef.current?.focus()
      else if (langOpen) langRef.current?.querySelector('button')?.focus()
      else if (accountOpen) accountRef.current?.querySelector('button')?.focus()
      else if (notifOpen) notifRef.current?.querySelector('button')?.focus()
    }
    document.addEventListener('keydown', closeOnEscape)
    return () => document.removeEventListener('keydown', closeOnEscape)
  }, [mobileOpen, langOpen, accountOpen, notifOpen])

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

  // Follow the actual photo boundary, including when the home route loads lazily.
  useEffect(() => {
    if (!isHomePage) return undefined
    let heroObserver
    let hero
    const updateObserver = () => {
      if (!hero) return
      heroObserver?.disconnect()
      const navBottom = Math.ceil(navRef.current?.getBoundingClientRect().bottom || 80)
      heroObserver = new IntersectionObserver(([entry]) => setHeroInView(entry.isIntersecting), {
        rootMargin: '-' + navBottom + 'px 0px 0px 0px',
      })
      heroObserver.observe(hero)
    }
    const findHero = () => {
      hero = document.querySelector('.home-premium .hero')
      if (!hero) return
      mountingObserver.disconnect()
      updateObserver()
    }
    const mountingObserver = new MutationObserver(findHero)
    findHero()
    if (!hero) mountingObserver.observe(document.querySelector('.route-transition-wrapper') || document.getElementById('root'), { childList: true, subtree: true })
    window.addEventListener('resize', updateObserver)
    return () => {
      mountingObserver.disconnect()
      heroObserver?.disconnect()
      window.removeEventListener('resize', updateObserver)
    }
  }, [isHomePage])

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
      if (document.hidden) return
      notificationService.getMyNotifications()
        .then((data) => {
          if (!active) return
          setNotifications(data.notifications || [])
          setUnreadCount(data.unread_count || 0)
        })
        .catch(() => {})
    }
    loadNotifications()
    const timer = window.setInterval(loadNotifications, NOTIFICATION_POLL_MS)
    document.addEventListener('visibilitychange', loadNotifications)
    return () => {
      active = false
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', loadNotifications)
    }
  }, [accessToken])

  // Listen for user updates
  useEffect(() => {
    const handleUserUpdate = (e) => setUserData(e.detail)
    window.addEventListener('user-updated', handleUserUpdate)
    return () => window.removeEventListener('user-updated', handleUserUpdate)
  }, [])

  // Close language dropdown on outside click
  useEffect(() => {
    const handler = e => {
      if (navRef.current && !navRef.current.contains(e.target)) setMobileOpen(false)
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
    document.addEventListener('pointerdown', handler)
    return () => document.removeEventListener('pointerdown', handler)
  }, [])

  const changeLanguage = (lang) => {
    i18n.changeLanguage(lang)
    setLangOpen(false)
  }

  const currentLang = i18n.language?.substring(0, 2)?.toUpperCase() || 'UZ'

  const navClass = ({ isActive }) => isActive ? 'nav-link active' : 'nav-link'

  const currentRole = (userData?.rol || role || '').toLowerCase()
  const isBrokerRole = currentRole === 'makler'
  const roleLink = currentRole === 'owner'  ? { to: '/owner',  label: t('nav.owner',  'Dashboard') }
                 : isBrokerRole ? { to: '/makler', label: t('nav.makler', 'Makler') }
                 : currentRole === 'student' ? { to: '/my-bookings', label: t('nav.bookings', 'Bronlarim') }
                 : null
  const profilePath = currentRole === 'owner' ? '/owner/profile' : isBrokerRole ? '/makler/profile' : '/profile'
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
    navigate(notification.target_url || '/my-bookings')
  }

  return (
    <>
      {/* ── DESKTOP / TABLET NAVBAR ────────────────────────────────────── */}
      <header
        ref={navRef}
        className={`navbar ${isHomePage ? 'home-nav' : ''} ${scrolled ? 'scrolled' : ''} ${mobileOpen ? 'menu-open' : ''} ${isOnHero ? 'on-hero' : ''}`}
      >
        <div className="navbar-progress" aria-hidden="true" />
        <div className="navbar-inner">
          {/* Brand */}
          <NavLink to="/" className="navbar-brand" aria-label="Aparty.uz — Home">
            <span className="brand-emblem" aria-hidden="true"><Home size={21} strokeWidth={1.8} /></span>
            <span className="brand-wordmark"><span className="brand-text">Aparty</span><span className="brand-suffix">.uz</span></span>
          </NavLink>

          {/* Desktop Links */}
          <nav className="navbar-links" aria-label="Main navigation">
            <NavLink to="/" end className={navClass}><Home size={15} />{t('nav.home', 'Bosh sahifa')}</NavLink>
            <NavLink to="/search" className={navClass}><Search size={15} />{t('nav.search', 'Qidiruv')}</NavLink>
            <NavLink to="/map" className={navClass}><MapPinned size={15} />{t('nav.map', 'Xarita')}</NavLink>
            {currentRole && roleLink && (
              <NavLink 
                to={roleLink.to} 
                className={({ isActive }) => `role-badge ${currentRole} ${isActive ? 'active' : ''}`}
              >
                <span className="role-dot" aria-hidden="true" />
                {roleLink.label}
              </NavLink>
            )}
          </nav>

          {/* Desktop Controls */}
          <div className="navbar-controls">
            {/* Language switcher */}
            <div className="lang-dropdown" ref={langRef}>
              <button
                className="ctrl-lang-btn"
                onClick={() => setLangOpen(v => !v)}
                aria-label="Change language"
                aria-expanded={langOpen}
                aria-controls="navbar-language-menu"
                type="button"
              >
                <Globe2 size={15} aria-hidden="true" />
                <span>{currentLang}</span>
                <ChevronDown size={14} className={langOpen ? 'rotated' : ''} />
              </button>
              <AnimatePresence>
                {langOpen && (
                  <motion.div
                    className="lang-menu"
                    id="navbar-language-menu"
                    initial={{ opacity: 0, y: -8, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0,  scale: 1 }}
                    exit={{    opacity: 0, y: -8, scale: 0.96 }}
                    transition={{ duration: reduceMotion ? 0 : 0.18 }}
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
              whileHover={reduceMotion ? undefined : { scale: 1.06 }}
              whileTap={reduceMotion ? undefined : { scale: 0.94 }}
            >
              <AnimatePresence mode="wait">
                {theme === 'dark' ? (
                  <motion.span key="sun" initial={{ rotate: -30, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 30, opacity: 0 }} transition={{ duration: reduceMotion ? 0 : 0.2 }}>
                    <Sun size={18} />
                  </motion.span>
                ) : (
                  <motion.span key="moon" initial={{ rotate: 30, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -30, opacity: 0 }} transition={{ duration: reduceMotion ? 0 : 0.2 }}>
                    <Moon size={18} />
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>

            {currentRole && (
              <>
                <div className="notification-dropdown" ref={notifRef}>
                  <button className="ctrl-icon-btn notification-btn" type="button" onClick={() => setNotifOpen((v) => !v)} aria-label="Notifications" aria-expanded={notifOpen} aria-controls="navbar-notification-menu">
                    <Bell size={18} />
                    {unreadCount > 0 && <span className="notification-count">{unreadCount > 9 ? '9+' : unreadCount}</span>}
                  </button>
                  <AnimatePresence>
                    {notifOpen && (
                      <motion.div
                        className="notification-menu"
                        id="navbar-notification-menu"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        transition={{ duration: reduceMotion ? 0 : 0.18 }}
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
                          <button className="view-all-notif" onClick={() => { setNotifOpen(false); navigate(dashboardPath) }}>{t('nav.view_dashboard', 'Kabinetga o‘tish')}<ArrowUpRight size={15} /></button>
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
                <NavLink to="/login" className="btn-nav-primary">
                  {t('nav.register', "Ro'yxatdan o'tish")}
                  <ArrowUpRight size={16} aria-hidden="true" />
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
                    <FallbackImage
                      src={userData?.rasm_url}
                      alt={userData?.ism}
                      fallback={<span>{userData?.ism?.charAt(0)?.toUpperCase() || <User size={16} />}</span>}
                    />
                  </div>
                  <span className="user-name">
                    {userData?.ism || t('nav.profile', 'Profil')}
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
                      transition={{ duration: reduceMotion ? 0 : 0.18 }}
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
                  whileHover={reduceMotion ? undefined : { scale: 1.06 }}
                  whileTap={reduceMotion ? undefined : { scale: 0.94 }}
                >
                  <LogOut size={18} />
                </motion.button>
              </div>
            )}

            {/* Hamburger */}
            <motion.button
              ref={menuButtonRef}
              className="ctrl-icon-btn hamburger"
              onClick={() => setMobileOpen(v => !v)}
              aria-label="Toggle menu"
              aria-expanded={mobileOpen}
              aria-controls="navbar-mobile-menu"
              whileTap={reduceMotion ? undefined : { scale: 0.94 }}
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
              id="navbar-mobile-menu"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: reduceMotion ? 0 : 0.18 }}
            >
              <nav className="mobile-menu-inner" aria-label="Expanded navigation">
                <NavLink to="/" end className={navClass} onClick={() => setMobileOpen(false)}><Home size={16} />{t('nav.home', 'Bosh sahifa')}</NavLink>
                <NavLink to="/search" className={navClass} onClick={() => setMobileOpen(false)}>
                  <Search size={16} /> {t('nav.search', 'Qidiruv')}
                </NavLink>
                <NavLink to="/map" className={navClass} onClick={() => setMobileOpen(false)}><MapPinned size={16} />{t('nav.map', 'Xarita')}</NavLink>
                {currentRole && roleLink && (
                  <NavLink to={roleLink.to} className={navClass} onClick={() => setMobileOpen(false)}>
                    {roleLink.label}
                  </NavLink>
                )}
                {!currentRole ? (
                  <>
                    <NavLink to="/login"    className="nav-link" onClick={() => setMobileOpen(false)}>{t('nav.login',    'Kirish')}</NavLink>
                    <NavLink to="/login" className="nav-link mobile-cta" onClick={() => setMobileOpen(false)}>{t('nav.register', "Ro'yxatdan o'tish")}</NavLink>
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
              </nav>
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
            to={isBrokerRole ? '/makler/create' : '/owner/create'}
          >
            <Plus className="bottom-icon add-icon" size={23} />
            <span>{t('nav.listing', "E'lon")}</span>
          </NavLink>
        )}
        <NavLink
          className={({ isActive }) => `bottom-item ${isActive ? 'active' : ''}`}
          to={currentRole ? profilePath : '/login'}
        >
          <div className="bottom-avatar">
            <FallbackImage
              src={currentRole ? userData?.rasm_url : null}
              alt=""
              fallback={<User className="bottom-icon" size={20} />}
            />
          </div>
          <span>{currentRole ? t('nav.profile', 'Profil') : t('nav.login', 'Kirish')}</span>
        </NavLink>
      </nav>
    </>
  )
}
