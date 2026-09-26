import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { authService } from '../../../services/authService'
import { useAuthStore } from '../../../store/authStore'
import { getErrorMessage, getHomePath } from '../../../utils/auth'
import PremiumLoader from '../../../components/shared/PremiumLoader/PremiumLoader'
import './Auth.scss'

export function TelegramCallbackPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const setAuth = useAuthStore((s) => s.setAuth)
  const code = searchParams.get('code')
  const state = searchParams.get('state')
  const [error, setError] = useState(() =>
    code && state ? '' : searchParams.get('error_description') || t('auth.login_cancelled', 'Telegram orqali kirish bekor qilindi.'),
  )
  // The login state is single-use, so the code must be exchanged only once (React StrictMode runs effects twice).
  const started = useRef(false)

  useEffect(() => {
    if (!code || !state || started.current) return
    started.current = true

    authService
      .completeTelegramLogin({ code, state })
      .then((data) => {
        setAuth(data.access_token, data.user?.role ?? null, data.user?.id)
        navigate(data.needs_role ? getHomePath(null) : getHomePath(data.user?.role), { replace: true })
      })
      .catch((requestError) => {
        setError(getErrorMessage(requestError, t('auth.login_error', "Kirish amalga oshmadi. Qayta urinib ko'ring.")))
      })
  }, [code, state, navigate, setAuth, t])

  return (
    <div className="auth-page liquid-theme">
      <div className="auth-liquid-container single-card-layout">
        <div className="liquid-card main-panel login-compact">
          {error ? (
            <>
              <div className="error-alert-liquid">{error}</div>
              <button type="button" className="btn-liquid-primary" onClick={() => navigate('/login', { replace: true })}>
                <span className="btn-content">{t('auth.try_again', 'Qayta urinish')}</span>
              </button>
            </>
          ) : (
            <>
              <PremiumLoader mini />
              <p className="subtitle-premium">{t('auth.signing_in', 'Kirilmoqda...')}</p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
