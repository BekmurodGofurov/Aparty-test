import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Briefcase, GraduationCap, Home } from 'lucide-react'
import { authService } from '../../../services/authService'
import { userService } from '../../../services/userService'
import { useAuthStore } from '../../../store/authStore'
import { getErrorMessage, getHomePath } from '../../../utils/auth'
import './Auth.scss'

const ROLE_CHOICES = [
  { value: 'student', icon: GraduationCap, title: 'Ijarachi / talaba', text: "Uy qidiraman, ijaraga olaman yoki sherik qidiraman" },
  { value: 'owner', icon: Home, title: 'Uy egasi', text: "O'z uyimni ijaraga beraman" },
  { value: 'makler', icon: Briefcase, title: 'Makler', text: "Mijozlar uchun e'lon joylayman" },
]

export function ChooseRolePage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { accessToken, role, userId, setAuth } = useAuthStore()
  const [error, setError] = useState('')
  const [savingRole, setSavingRole] = useState(null)

  // The role may already be saved on the server while this browser lost it: restore it instead of asking again.
  useEffect(() => {
    if (!accessToken || role) return undefined
    let active = true
    userService
      .getCurrentUser()
      .then((user) => {
        if (active && user.rol) setAuth(accessToken, user.rol, user.id)
      })
      .catch(() => {})
    return () => {
      active = false
    }
  }, [accessToken, role, setAuth])

  if (!accessToken) return <Navigate to="/login" replace />
  if (role) return <Navigate to={getHomePath(role)} replace />

  const handleChoose = async (value) => {
    setError('')
    setSavingRole(value)
    try {
      const data = await authService.chooseRole(value)
      setAuth(data.access_token, data.user.role, userId)
      navigate(getHomePath(data.user.role), { replace: true })
    } catch (requestError) {
      if (requestError.response?.status === 409) {
        // The server already has a role for this account: use it.
        try {
          const user = await userService.getCurrentUser()
          setAuth(accessToken, user.rol, user.id)
          navigate(getHomePath(user.rol), { replace: true })
          return
        } catch {
          // fall through to the error message
        }
      }
      setError(getErrorMessage(requestError, t('auth.role_error', "Rolni saqlab bo'lmadi. Qayta urinib ko'ring.")))
      setSavingRole(null)
    }
  }

  return (
    <div className="auth-page liquid-theme">
      <div className="auth-liquid-container single-card-layout">
        <div className="liquid-card main-panel">
          <section className="hero-content">
            <h1 className="title-premium">{t('auth.choose_role_title', 'Siz kimsiz?')}</h1>
            <p className="subtitle-premium">
              {t('auth.choose_role_subtitle', "Rolni bir marta tanlaysiz, keyin o'zgartirib bo'lmaydi.")}
            </p>
          </section>

          <div className="role-choice-grid">
            {ROLE_CHOICES.map(({ value, icon: Icon, title, text }) => (
              <button
                key={value}
                type="button"
                className="role-choice-card"
                onClick={() => handleChoose(value)}
                disabled={savingRole !== null}
              >
                <Icon size={28} />
                <strong>{title}</strong>
                <span>{text}</span>
              </button>
            ))}
          </div>

          {error && <div className="error-alert-liquid">{error}</div>}
        </div>
      </div>
    </div>
  )
}
