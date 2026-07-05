import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export function RoleRoute({ role, children }) {
  const currentRole = useAuthStore((s) => s.role)
  const normalizedRole = currentRole?.toLowerCase()
  const roleAliases = {
    broker: ['broker', 'makler'],
    makler: ['makler', 'broker'],
    student: ['student', 'guest'],
    guest: ['guest', 'student'],
  }
  const allowedRoles = roleAliases[role] || [role]

  if (!normalizedRole) return <Navigate to="/login" replace />
  if (!allowedRoles.includes(normalizedRole)) return <Navigate to="/" replace />

  return children
}
