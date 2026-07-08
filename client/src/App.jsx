import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { NavBar } from './components/NavBar/NavBar'
import { RoleRoute } from './components/RoleRoute/RoleRoute'
import { ProtectedAuthRoute } from './components/ProtectedAuthRoute/ProtectedAuthRoute'
import { useThemeStore } from './store/themeStore'
import { useAuthStore } from './store/authStore'
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
function AppContent() {
  const location = useLocation();

  return (
    <>
      <GlobalLayout>
        <NavBar />

        <main
          key={location.pathname}
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
        </main>

        <Footer />
      </GlobalLayout>
    </>
  )
}

function App() {
  const theme = useThemeStore((s) => s.theme)
  const initializeAuth = useAuthStore((s) => s.initializeAuth)

  useEffect(() => {
    initializeAuth()
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
