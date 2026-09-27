import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { NavBar } from './components/NavBar/NavBar'
import { RoleRoute } from './components/RoleRoute/RoleRoute'
import { ProtectedAuthRoute } from './components/ProtectedAuthRoute/ProtectedAuthRoute'
import { useThemeStore } from './store/themeStore'
import { useAuthStore } from './store/authStore'
import { Footer } from './components/Footer/Footer'
import { GlobalLayout } from './components/layout/GlobalLayout'
import PremiumLoader from './components/shared/PremiumLoader/PremiumLoader'

// Pages load on demand so the first visit downloads only the page it opens. Each loader is also
// kept so the rest can be fetched in the background afterwards (see prefetchRemainingPages below):
// once the browser has already fetched a chunk, opening that page is instant either way.
const pageLoaders = []
const page = (load, name) => {
  pageLoaders.push(load)
  return lazy(() => load().then((module) => ({ default: module[name] })))
}

const HomePremium = page(() => import('./pages/shared/home/HomePremium'), 'HomePremium')
const PropertySearch = page(() => import('./pages/shared/property-search/PropertySearch'), 'PropertySearch')
const MapPage = page(() => import('./pages/shared/map/MapPage'), 'MapPage')
const Listing = page(() => import('./pages/shared/listing/Listing'), 'Listing')
const LoginPage = page(() => import('./pages/shared/auth/LoginPage'), 'LoginPage')
const TelegramCallbackPage = page(() => import('./pages/shared/auth/TelegramCallbackPage'), 'TelegramCallbackPage')
const ChooseRolePage = page(() => import('./pages/shared/auth/ChooseRolePage'), 'ChooseRolePage')
const UserProfile = page(() => import('./pages/user/profile/UserProfile'), 'UserProfile')
const MyBookings = page(() => import('./pages/user/bookings/MyBookings'), 'MyBookings')
const OwnerDashboard = page(() => import('./pages/owner/OwnerDashboard'), 'OwnerDashboard')
const OwnerProfile = page(() => import('./pages/owner/OwnerProfile'), 'OwnerProfile')
const OwnerCreate = page(() => import('./pages/owner/OwnerCreate'), 'OwnerCreate')
const OwnerEdit = page(() => import('./pages/owner/OwnerEdit'), 'OwnerEdit')
const MaklerDashboard = page(() => import('./pages/makler/MaklerDashboard'), 'MaklerDashboard')
const MaklerProfile = page(() => import('./pages/makler/MaklerProfile'), 'MaklerProfile')
const MaklerCreate = page(() => import('./pages/makler/MaklerCreate'), 'MaklerCreate')

// Fetches every other page's JS while the browser is idle, so switching pages later needs no
// network round trip (the module is already cached) — the visible "loading" on navigation was
// this chunk download, not data. Runs once, after the current page has had time to settle.
const prefetchRemainingPages = () => {
  const idle = window.requestIdleCallback || ((run) => window.setTimeout(run, 1500))
  idle(() => pageLoaders.forEach((load) => void load().catch(() => {})))
}

function AppContent() {
  const location = useLocation()

  return (
    <GlobalLayout>
      <NavBar />

      <main
        className="route-transition-wrapper"
        style={{ position: 'relative', zIndex: 1, minHeight: '80vh', overflow: 'visible' }}
      >
        <Suspense fallback={<PremiumLoader mini />}>
          <Routes location={location}>
            {/* Public Routes */}
            <Route path="/" element={<HomePremium />} />
            <Route path="/search" element={<PropertySearch />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/listing/:id" element={<Listing />} />

            {/* Auth Routes */}
            <Route path="/login" element={<ProtectedAuthRoute><LoginPage /></ProtectedAuthRoute>} />
            <Route path="/auth/telegram/callback" element={<TelegramCallbackPage />} />
            <Route path="/choose-role" element={<ChooseRolePage />} />

            {/* Student Routes */}
            <Route path="/profile" element={<UserProfile />} />
            <Route path="/my-bookings" element={<MyBookings />} />

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

            {/* Catch all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>

      <Footer />
    </GlobalLayout>
  )
}

function App() {
  const theme = useThemeStore((s) => s.theme)
  const initializeAuth = useAuthStore((s) => s.initializeAuth)

  useEffect(() => {
    initializeAuth()
    prefetchRemainingPages()
  }, [initializeAuth])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
