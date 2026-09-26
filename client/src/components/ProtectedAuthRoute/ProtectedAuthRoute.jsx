import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { getHomePath } from '../../utils/auth'

/**
 * Protects auth pages (login) - redirects authenticated users to their dashboard,
 * or to role selection when they have not chosen a role yet.
 */
export function ProtectedAuthRoute({ children }) {
  const { accessToken, role } = useAuthStore()

  if (accessToken) return <Navigate to={getHomePath(role)} replace />

  return children
}
