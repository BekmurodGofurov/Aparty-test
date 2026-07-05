import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { motion, AnimatePresence, MotionConfig } from 'framer-motion'
import { NavBar } from './components/NavBar/NavBar'
import { RoleRoute } from './components/RoleRoute/RoleRoute'
import { ProtectedAuthRoute } from './components/ProtectedAuthRoute/ProtectedAuthRoute'
import { useThemeStore } from './store/themeStore'
import { useAuthStore } from './store/authStore'
import { AIChatAssistant } from './components/ai/AIChatAssistant'
import { Footer } from './components/Footer/Footer'
import { AdminComplaints } from './pages/admin/AdminComplaints'
import { AdminDashboard } from './pages/admin/AdminDashboard'
import { AdminListingDetail } from './pages/admin/AdminListingDetail'
import { AdminListings } from './pages/admin/AdminListings'
import { AdminProfile } from './pages/admin/AdminProfile'
import { AdminRevenue } from './pages/admin/AdminRevenue'
import { AdminUserDetail } from './pages/admin/AdminUserDetail'
import { AdminUsers } from './pages/admin/AdminUsers'
import { HomePremium } from './pages/shared/home/HomePremium'
import { Listing } from './pages/shared/listing/Listing'
import { LoginPage } from './pages/shared/auth/LoginPage'
import { Messages } from './pages/shared/messages/Messages'
import { MaklerCreate } from './pages/makler/MaklerCreate'
import { MaklerDashboard } from './pages/makler/MaklerDashboard'
import { MaklerPayments } from './pages/makler/MaklerPayments'
import { MaklerProfile } from './pages/makler/MaklerProfile'
import { MaklerSubscription } from './pages/makler/MaklerSubscription'
import { MyRoom } from './pages/user/my-room/MyRoom'
import { OwnerCreate } from './pages/owner/OwnerCreate'
import { OwnerDashboard } from './pages/owner/OwnerDashboard'
import { OwnerEdit } from './pages/owner/OwnerEdit'
import { OwnerProfile } from './pages/owner/OwnerProfile'
import { UserProfile } from './pages/user/profile/UserProfile'
import { RegisterPage } from './pages/shared/auth/RegisterPage'
import { PropertySearch } from './pages/shared/property-search/PropertySearch'
import { MapPage } from './pages/shared/map/MapPage'
import { GlobalLayout } from './components/layout/GlobalLayout'

function AppIntro({ onComplete, theme }) {
  useEffect(() => {
    const timer = setTimeout(onComplete, 1450)
    return () => clearTimeout(timer)
  }, [onComplete])

  const isLight = theme === 'light'
  const bg = isLight ? '#fffaf0' : '#020617'
  const text = isLight ? '#0f172a' : '#f8fafc'
  const muted = isLight ? 'rgba(15, 23, 42, 0.58)' : 'rgba(226, 232, 240, 0.62)'

  return (
    <motion.div
      className="app-intro"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.015, filter: 'blur(10px)' }}
      transition={{ duration: 0.42, ease: [0.16, 1, 0.3, 1] }}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 2147482000,
        display: 'grid',
        placeItems: 'center',
        overflow: 'hidden',
        background: bg,
      }}
    >
      <motion.div
        aria-hidden
        initial={{ x: '-120%', skewX: -14 }}
        animate={{ x: '120%', skewX: -14 }}
        transition={{ duration: 0.86, delay: 0.25, ease: [0.76, 0, 0.24, 1] }}
        style={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          width: '42vw',
          background: 'linear-gradient(90deg, transparent, rgba(56,189,248,0.28), rgba(245,158,11,0.22), transparent)',
          filter: 'blur(18px)',
        }}
      />

      <motion.div
        aria-hidden
        initial={{ scale: 0.72, opacity: 0 }}
        animate={{ scale: [0.72, 1.04, 1], opacity: [0, 1, 0.9] }}
        transition={{ duration: 0.72, ease: [0.16, 1, 0.3, 1] }}
        style={{
          position: 'absolute',
          width: 'min(54vw, 520px)',
          aspectRatio: '1',
          borderRadius: '50%',
          background: isLight
            ? 'radial-gradient(circle, rgba(245,158,11,0.2), rgba(56,189,248,0.1) 42%, transparent 70%)'
            : 'radial-gradient(circle, rgba(56,189,248,0.22), rgba(124,58,237,0.16) 42%, transparent 72%)',
        }}
      />

      <motion.div
        initial={{ y: 26, opacity: 0, scale: 0.94 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        transition={{ duration: 0.62, ease: [0.16, 1, 0.3, 1] }}
        style={{
          position: 'relative',
          display: 'grid',
          justifyItems: 'center',
          gap: 18,
          color: text,
        }}
      >
        <motion.div
          initial={{ rotate: -18, scale: 0.78 }}
          animate={{ rotate: 0, scale: [0.78, 1.12, 1] }}
          transition={{ duration: 0.68, ease: [0.16, 1, 0.3, 1] }}
          style={{
            width: 72,
            height: 72,
            borderRadius: 22,
            display: 'grid',
            placeItems: 'center',
            background: 'linear-gradient(135deg, #0ea5e9, #38bdf8 48%, #f59e0b)',
            boxShadow: isLight ? '0 24px 70px rgba(245,158,11,0.28)' : '0 24px 82px rgba(14,165,233,0.35)',
          }}
        >
          <motion.span
            initial={{ scale: 0, rotate: 45 }}
            animate={{ scale: 1, rotate: 45 }}
            transition={{ duration: 0.38, delay: 0.2, ease: [0.34, 1.56, 0.64, 1] }}
            style={{
              width: 26,
              height: 26,
              borderRadius: 7,
              background: '#fff',
              display: 'block',
            }}
          />
        </motion.div>

        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <motion.strong
            initial={{ letterSpacing: '0.12em', opacity: 0 }}
            animate={{ letterSpacing: '0', opacity: 1 }}
            transition={{ duration: 0.62, delay: 0.12, ease: [0.16, 1, 0.3, 1] }}
            style={{ fontFamily: 'Outfit, sans-serif', fontSize: 'clamp(3rem, 8vw, 5.6rem)', lineHeight: 0.9, fontWeight: 950 }}
          >
            Aparty
          </motion.strong>
          <motion.span
            initial={{ y: 16, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.42, delay: 0.42 }}
            style={{ color: '#38bdf8', fontSize: 'clamp(2.2rem, 5vw, 4rem)', fontWeight: 950 }}
          >
            .uz
          </motion.span>
        </div>

        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.46, delay: 0.42 }}
          style={{ margin: 0, color: muted, fontWeight: 750, letterSpacing: '0.08em', textTransform: 'uppercase', fontSize: '0.76rem' }}
        >
          Andijonda uyingizni toping
        </motion.p>

        <div
          style={{
            width: 180,
            height: 4,
            borderRadius: 999,
            overflow: 'hidden',
            background: isLight ? 'rgba(15,23,42,0.08)' : 'rgba(255,255,255,0.08)',
          }}
        >
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: '0%' }}
            transition={{ duration: 0.78, delay: 0.36, ease: [0.16, 1, 0.3, 1] }}
            style={{ width: '100%', height: '100%', borderRadius: 999, background: 'linear-gradient(90deg, #0ea5e9, #38bdf8, #f59e0b)' }}
          />
        </div>
      </motion.div>
    </motion.div>
  )
}

function AppContent({ showIntro, setShowIntro, theme }) {
  const location = useLocation();

  return (
    <>
      <AnimatePresence>
        {showIntro && <AppIntro key="app-intro" theme={theme} onComplete={() => setShowIntro(false)} />}
      </AnimatePresence>

      <GlobalLayout>
        <NavBar />
        <AIChatAssistant />
        
        <AnimatePresence mode="wait">
          <motion.main
            key={location.pathname}
            initial={{ opacity: 0, y: 12, filter: 'blur(8px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, y: -12, filter: 'blur(8px)' }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
            className="route-transition-wrapper"
            style={{ position: 'relative', zIndex: 1, minHeight: '80vh', overflow: 'visible' }}
          >
            <Routes location={location}>
          {/* Public Routes */}
          <Route path="/" element={<HomePremium />} />
          <Route path="/search" element={<PropertySearch />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/listing/:id" element={<Listing />} />
          <Route path="/messages" element={<Messages />} />
          
          {/* Protected Auth Routes */}
          <Route path="/login" element={<ProtectedAuthRoute><LoginPage /></ProtectedAuthRoute>} />
          <Route path="/register" element={<ProtectedAuthRoute><RegisterPage /></ProtectedAuthRoute>} />

          {/* Student Routes */}
          <Route path="/profile" element={<UserProfile />} />
          <Route path="/my-room" element={<RoleRoute role="student"><MyRoom /></RoleRoute>} />

          {/* Owner Routes */}
          <Route path="/owner" element={<RoleRoute role="owner"><OwnerDashboard /></RoleRoute>} />
          <Route path="/owner/profile" element={<RoleRoute role="owner"><OwnerProfile /></RoleRoute>} />
          <Route path="/owner/create" element={<RoleRoute role="owner"><OwnerCreate /></RoleRoute>} />
          <Route path="/owner/listing/:id/edit" element={<RoleRoute role="owner"><OwnerEdit /></RoleRoute>} />

          {/* Makler Routes */}
          <Route path="/makler" element={<RoleRoute role="makler"><MaklerDashboard /></RoleRoute>} />
          <Route path="/makler/profile" element={<RoleRoute role="makler"><MaklerProfile /></RoleRoute>} />
          <Route path="/makler/create" element={<RoleRoute role="makler"><MaklerCreate /></RoleRoute>} />
          <Route path="/makler/listing/:id/edit" element={<RoleRoute role="makler"><OwnerEdit /></RoleRoute>} />
          <Route path="/makler/subscription" element={<RoleRoute role="makler"><MaklerSubscription /></RoleRoute>} />
          <Route path="/makler/payments" element={<RoleRoute role="makler"><MaklerPayments /></RoleRoute>} />
          <Route path="/broker" element={<RoleRoute role="broker"><MaklerDashboard /></RoleRoute>} />
          <Route path="/broker/profile" element={<RoleRoute role="broker"><MaklerProfile /></RoleRoute>} />
          <Route path="/broker/create" element={<RoleRoute role="broker"><MaklerCreate /></RoleRoute>} />
          <Route path="/broker/listing/:id/edit" element={<RoleRoute role="broker"><OwnerEdit /></RoleRoute>} />
          <Route path="/broker/subscription" element={<RoleRoute role="broker"><MaklerSubscription /></RoleRoute>} />
          <Route path="/broker/payments" element={<RoleRoute role="broker"><MaklerPayments /></RoleRoute>} />

          {/* Admin Routes */}
          <Route path="/admin" element={<RoleRoute role="admin"><AdminDashboard /></RoleRoute>} />
          <Route path="/admin/profile" element={<RoleRoute role="admin"><AdminProfile /></RoleRoute>} />
          <Route path="/admin/listings" element={<RoleRoute role="admin"><AdminListings /></RoleRoute>} />
          <Route path="/admin/listings/:listingId" element={<RoleRoute role="admin"><AdminListingDetail /></RoleRoute>} />
          <Route path="/admin/users" element={<RoleRoute role="admin"><AdminUsers /></RoleRoute>} />
          <Route path="/admin/users/:userId" element={<RoleRoute role="admin"><AdminUserDetail /></RoleRoute>} />
          <Route path="/admin/complaints" element={<RoleRoute role="admin"><AdminComplaints /></RoleRoute>} />
          <Route path="/admin/revenue" element={<RoleRoute role="admin"><AdminRevenue /></RoleRoute>} />

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
          </motion.main>
        </AnimatePresence>

        <Footer />
      </GlobalLayout>
    </>
  )
}

function App() {
  const theme = useThemeStore((s) => s.theme)
  const initializeAuth = useAuthStore((s) => s.initializeAuth)
  const [showIntro, setShowIntro] = useState(true)

  useEffect(() => {
    initializeAuth()
  }, [initializeAuth])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <MotionConfig reducedMotion="user">
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AppContent showIntro={showIntro} setShowIntro={setShowIntro} theme={theme} />
      </BrowserRouter>
    </MotionConfig>
  )
}

export default App
