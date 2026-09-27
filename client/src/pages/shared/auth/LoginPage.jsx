import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Send } from 'lucide-react'
import { authService } from '../../../services/authService'
import { getErrorMessage } from '../../../utils/auth'
import PremiumLoader from '../../../components/shared/PremiumLoader/PremiumLoader'
import './Auth.scss'

export function LoginPage() {
  const { t } = useTranslation()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

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

  return (
    <div className="auth-page liquid-theme">
      <motion.div
        className="auth-liquid-container single-card-layout"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="liquid-card main-panel login-compact">
          <header className="brand-header-premium">
            <div className="logo-orb"><span>A</span></div>
            <h2 className="brand-text">Aparty<span>.uz</span></h2>
          </header>

          <section className="hero-content">
            <h1 className="title-premium">{t('auth.login_title', 'Tizimga kirish')}</h1>
            <p className="subtitle-premium">
              {t('auth.telegram_subtitle', "Telegram oynasida telefon raqamingizni kiriting va ilovada tasdiqlang. Ro'yxatdan o'tish ham shu yerda.")}
            </p>
          </section>

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
        </div>
      </motion.div>
    </div>
  )
}
