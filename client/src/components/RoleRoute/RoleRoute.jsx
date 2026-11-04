import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export function RoleRoute({ role, children }) {
  const { accessToken, role: currentRole } = useAuthStore()

  if (!accessToken) return <Navigate to="/login" replace />
  if (!currentRole) return <Navigate to="/choose-role" replace />
  if (currentRole.toLowerCase() !== role.toLowerCase()) return <Navigate to="/" replace />

  return children
}
