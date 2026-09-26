import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { ShieldCheck, KeyRound, Eye, EyeOff, User, Lock, Send } from 'lucide-react'
import { authService } from '../../../services/authService'
import { userService } from '../../../services/userService'
import { useAuthStore } from '../../../store/authStore'
import { getErrorMessage, getHomePath } from '../../../utils/auth'
import PremiumLoader from '../../../components/shared/PremiumLoader/PremiumLoader'
import './Auth.scss'

export function LoginPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const setAuth = useAuthStore((s) => s.setAuth)
  const isAdmin = searchParams.get('admin') === 'true'

  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const handleTelegramLogin = async () => {
    setError('')
    setLoading(true)
    try {
      window.location.assign(await authService.startTelegramLogin())
    } catch (requestError) {
      setError(getErrorMessage(requestError, t('auth.login_error', "Telegram orqali kirishni boshlab bo'lmadi. Qayta urinib ko'ring.")))
      setLoading(false)
    }
  }

  const handleAdminSubmit = async (event) => {
    event.preventDefault()
    if (!username.trim() || !password) return
    setError('')
    setLoading(true)
    try {
      const data = await authService.adminLogin({ username: username.trim(), password })
      localStorage.setItem('accessToken', data.access_token)
      const user = await userService.getCurrentUser()
      setAuth(data.access_token, user.rol, user.id)
      navigate(getHomePath(user.rol))
    } catch (requestError) {
      setError(getErrorMessage(requestError, t('auth.invalid_credentials', "Login yoki parol noto'g'ri")))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page liquid-theme">
      <motion.div
        className="auth-liquid-container single-card-layout"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="liquid-card main-panel login-compact">
          {isAdmin && <div className="admin-pill"><ShieldCheck size={15} /> ADMIN</div>}

          <header className="brand-header-premium">
            <div className="logo-orb"><span>A</span></div>
            <h2 className="brand-text">Aparty<span>.uz</span></h2>
          </header>

          <section className="hero-content">
            <h1 className="title-premium">{isAdmin ? t('auth.admin_title', 'Admin kirish') : t('auth.login_title', 'Tizimga kirish')}</h1>
            <p className="subtitle-premium">
              {isAdmin
                ? t('auth.admin_subtitle', 'Tizim admini uchun username va parol orqali kirish')
                : t('auth.telegram_subtitle', "Telegram oynasida telefon raqamingizni kiriting va ilovada tasdiqlang. Ro'yxatdan o'tish ham shu yerda.")}
            </p>
          </section>

          {isAdmin ? (
            <form onSubmit={handleAdminSubmit} className="auth-form-liquid">
              <div className="admin-credentials-section" style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '1.25rem', marginBottom: '0.5rem' }}>
                <div className="input-group-liquid" style={{ display: 'flex', alignItems: 'center' }}>
                  <User size={18} style={{ position: 'absolute', left: '16px', color: 'var(--auth-text-muted)', pointerEvents: 'none' }} />
                  <input
                    type="text"
                    placeholder={t('auth.admin_username_placeholder', 'Username (masalan: admin)')}
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    disabled={loading}
                    style={{ paddingLeft: '46px' }}
                    required
                  />
                </div>
                <div className="input-group-liquid password-field" style={{ display: 'flex', alignItems: 'center' }}>
                  <Lock size={18} style={{ position: 'absolute', left: '16px', color: 'var(--auth-text-muted)', pointerEvents: 'none' }} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder={t('auth.admin_password_placeholder', 'Parolni kiriting...')}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    style={{ paddingLeft: '46px', paddingRight: '46px' }}
                    required
                  />
                  <button type="button" className="eye-toggle" onClick={() => setShowPassword(!showPassword)} tabIndex="-1">
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {error && <div className="error-alert-liquid">{error}</div>}

              <button type="submit" className="btn-liquid-primary" disabled={loading || !username.trim() || !password}>
                <span className="shimmer-effect"></span>
                <span className="btn-content">
                  {loading ? <PremiumLoader mini /> : (
                    <>
                      <KeyRound size={18} style={{ marginRight: '8px' }} />
                      {t('auth.submit_admin_login', 'Admin panelga kirish')}
                    </>
                  )}
                </span>
              </button>
            </form>
          ) : (
            <div className="auth-form-liquid">
              {error && <div className="error-alert-liquid">{error}</div>}

              <button type="button" className="btn-liquid-primary" onClick={handleTelegramLogin} disabled={loading}>
                <span className="shimmer-effect"></span>
                <span className="btn-content">
                  {loading ? <PremiumLoader mini /> : (
                    <>
                      <Send size={18} style={{ marginRight: '8px' }} />
                      {t('auth.telegram_login', 'Telegram orqali kirish')}
                    </>
                  )}
                </span>
              </button>
            </div>
          )}

          <footer className="footer-links-liquid">
            <button type="button" className="btn-ghost-sm" onClick={() => navigate(isAdmin ? '/login' : '/login?admin=true')}>
              {isAdmin ? t('auth.back_to_login', 'Foydalanuvchi sifatida kirish') : t('auth.admin_login', 'Admin sifatida kirish')}
            </button>
          </footer>
        </div>
      </motion.div>
    </div>
  )
}
