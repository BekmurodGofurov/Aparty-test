import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Eye, EyeOff, ShieldCheck } from 'lucide-react'
import { api } from '../../../services/api'
import { userService } from '../../../services/userService'
import { useAuthStore } from '../../../store/authStore'
import PremiumLoader from '../../../components/shared/PremiumLoader/PremiumLoader'
import './Auth.scss'

export function LoginPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [telefon, setTelefon] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const isAdmin = searchParams.get('admin') === 'true'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const endpoint = isAdmin ? '/auth/admin-login' : '/auth/login'
      const cleanPhone = telefon.replace(/\s+/g, '')
      const { data } = await api.post(endpoint, { phone: cleanPhone, password })
      localStorage.setItem('accessToken', data.access_token)
      const user = await userService.getCurrentUser()

      if (isAdmin && user.rol !== 'admin') {
        setError(t('auth.admin_only'))
        setLoading(false)
        return
      }

      setAuth(data.access_token, user.rol, user.id)
      if (user.rol === 'admin') navigate('/admin')
      else if (user.rol === 'owner') navigate('/owner')
      else if (user.rol === 'broker') navigate('/broker')
      else if (user.rol === 'makler') navigate('/makler')
      else navigate('/profile')
    } catch (requestError) {
      // Handle Pydantic validation errors (422) and other errors
      let errorMsg = t('auth.login_error')
      
      if (requestError?.response?.data?.detail) {
        const detail = requestError.response.data.detail
        
        // If detail is an array (Pydantic validation errors)
        if (Array.isArray(detail)) {
          errorMsg = detail[0]?.msg || detail[0] || errorMsg
        } 
        // If detail is a string (custom error message)
        else if (typeof detail === 'string') {
          errorMsg = detail
        }
        // If detail is an object (shouldn't happen but handle it)
        else if (typeof detail === 'object') {
          errorMsg = detail.message || errorMsg
        }
      }
      
      setError(errorMsg)
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
            <h1 className="title-premium">{isAdmin ? t('auth.admin_title') : t('auth.login_title')}</h1>
            <p className="subtitle-premium">{isAdmin ? t('auth.admin_subtitle') : t('auth.login_subtitle')}</p>
          </section>

          <form onSubmit={handleSubmit} className="auth-form-liquid">
            <div className="input-group-liquid">
              <input
                type="tel"
                placeholder={t('auth.phone')}
                value={telefon}
                onChange={(e) => setTelefon(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="input-group-liquid password-field">
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder={t('auth.password')}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
              <button
                type="button"
                className="eye-toggle"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
                aria-label={showPassword ? 'Parolni yashirish' : "Parolni ko'rsatish"}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            {error && <div className="error-alert-liquid">{error}</div>}

            <button type="submit" className="btn-liquid-primary" disabled={loading}>
              <span className="shimmer-effect"></span>
              <span className="btn-content">
                {loading ? <PremiumLoader mini /> : t('auth.submit_login')}
              </span>
            </button>
          </form>

          {!isAdmin && (
            <footer className="footer-links-liquid">
              <p>
                {t('auth.no_account')}{' '}
                <Link to="/register" className="highlight-link">
                  {t('auth.register')}
                </Link>
              </p>
              <button
                type="button"
                className="btn-ghost-sm"
                onClick={() => navigate('/login?admin=true')}
              >
                {t('auth.admin_login')}
              </button>
            </footer>
          )}

          {isAdmin && (
            <footer className="footer-links-liquid">
              <button
                type="button"
                className="btn-ghost-sm"
                onClick={() => navigate('/login')}
              >
                {t('auth.back_to_login')}
              </button>
            </footer>
          )}
        </div>
      </motion.div>
    </div>
  )
}
