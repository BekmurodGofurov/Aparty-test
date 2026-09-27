import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export function RoleRoute({ role, children }) {
  const currentRole = useAuthStore((s) => s.role)

  if (!currentRole) return <Navigate to="/login" replace />
  if (currentRole.toLowerCase() !== role) return <Navigate to="/" replace />

  return children
}
