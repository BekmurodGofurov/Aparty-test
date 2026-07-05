import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

/**
 * Protects auth pages (login/register) - redirects authenticated users to their dashboard
 */
export function ProtectedAuthRoute({ children }) {
  const { accessToken, role } = useAuthStore()

  if (accessToken && role) {
    // User is authenticated - redirect to appropriate dashboard
    if (role === 'admin') return <Navigate to="/admin" replace />
    if (role === 'owner') return <Navigate to="/owner" replace />
    if (role === 'makler') return <Navigate to="/makler" replace />
    if (role === 'broker') return <Navigate to="/broker" replace />
    // Default redirect for other roles (student, etc.)
    return <Navigate to="/" replace />
  }

  return children
}
