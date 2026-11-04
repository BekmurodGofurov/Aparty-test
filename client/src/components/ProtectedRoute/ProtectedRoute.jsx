import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export function ProtectedRoute({ children }) {
  const { accessToken, role } = useAuthStore()

  if (!accessToken) return <Navigate to="/login" replace />
  if (!role) return <Navigate to="/choose-role" replace />

  return children
}
