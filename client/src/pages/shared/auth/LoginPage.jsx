import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { ShieldCheck, KeyRound, Eye, EyeOff, User, Lock } from 'lucide-react'
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
  const [codeDigits, setCodeDigits] = useState(['', '', '', '', '', ''])
  const inputRefs = useRef([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const isAdmin = searchParams.get('admin') === 'true'

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const code = codeDigits.join('')

  useEffect(() => {
    setError('')
  }, [isAdmin])

  const handleDigitChange = (index, value) => {
    const cleanVal = value.replace(/[^0-9]/g, '')
    if (!cleanVal && value !== '') return

    const newDigits = [...codeDigits]
    
    if (cleanVal.length > 1) {
      const pastedChars = cleanVal.slice(0, 6).split('')
      for (let i = 0; i < pastedChars.length; i++) {
        if (index + i < 6) {
          newDigits[index + i] = pastedChars[i]
        }
      }
      setCodeDigits(newDigits)
      const nextFocusIdx = Math.min(index + pastedChars.length, 5)
      inputRefs.current[nextFocusIdx]?.focus()
    } else {
      newDigits[index] = cleanVal
      setCodeDigits(newDigits)
      if (cleanVal && index < 5) {
        inputRefs.current[index + 1]?.focus()
      }
    }
  }

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !codeDigits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    } else if (e.key === 'ArrowLeft' && index > 0) {
      e.preventDefault()
      inputRefs.current[index - 1]?.focus()
    } else if (e.key === 'ArrowRight' && index < 5) {
      e.preventDefault()
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const pasteData = e.clipboardData.getData('text').replace(/[^0-9]/g, '').slice(0, 6)
    if (!pasteData) return
    const newDigits = ['', '', '', '', '', '']
    pasteData.split('').forEach((char, idx) => {
      newDigits[idx] = char
    })
    setCodeDigits(newDigits)
    const focusIdx = Math.min(pasteData.length - 1, 5)
    inputRefs.current[focusIdx]?.focus()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (isAdmin) {
      if (!username.trim() || !password) return
      setError('')
      setLoading(true)

      try {
        const { data } = await api.post('/auth/admin-login', { username: username.trim(), password })
        localStorage.setItem('accessToken', data.access_token)
        const user = await userService.getCurrentUser()

        setAuth(data.access_token, user.rol, user.id)
        navigate('/admin')
      } catch (requestError) {
        let errorMsg = t('auth.invalid_credentials', "Login yoki parol noto'g'ri")
        if (requestError?.response?.data?.detail) {
          const detail = requestError.response.data.detail
          if (Array.isArray(detail)) {
            errorMsg = detail[0]?.msg || detail[0] || errorMsg
          } else if (typeof detail === 'string') {
            errorMsg = detail
          } else if (typeof detail === 'object') {
            errorMsg = detail.message || errorMsg
          }
        }
        setError(errorMsg)
      } finally {
        setLoading(false)
      }
      return
    }

    if (code.length < 6) return
    setError('')
    setLoading(true)

    try {
      const cleanCode = code.replace(/\s+/g, '')
      const { data } = await api.post('/auth/login', { code: cleanCode })
      localStorage.setItem('accessToken', data.access_token)
      const user = await userService.getCurrentUser()

      if (isAdmin && user.rol !== 'admin') {
        setError(t('auth.admin_only', "Ushbu sahifa faqat adminlar uchun"))
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
      let errorMsg = t('auth.login_error', "Kod noto'g'ri yoki muddati o'tgan")
      
      if (requestError?.response?.data?.detail) {
        const detail = requestError.response.data.detail
        if (Array.isArray(detail)) {
          errorMsg = detail[0]?.msg || detail[0] || errorMsg
        } else if (typeof detail === 'string') {
          errorMsg = detail
        } else if (typeof detail === 'object') {
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
            <h1 className="title-premium">{isAdmin ? t('auth.admin_title', 'Admin kirish') : t('auth.login_title', 'Tizimga kirish')}</h1>
            <p className="subtitle-premium">
              {isAdmin
                ? t('auth.admin_subtitle', "Tizim admini uchun username va parol orqali kirish")
                : t('auth.login_code_subtitle', "Telegram botdan olingan 6 xonali kodni kiriting")}
            </p>
          </section>

          <form onSubmit={handleSubmit} className="auth-form-liquid">
            {isAdmin ? (
              <div className="admin-credentials-section" style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '1.25rem', marginBottom: '0.5rem' }}>
                <div className="input-group-liquid" style={{ display: 'flex', alignItems: 'center' }}>
                  <User size={18} style={{ position: 'absolute', left: '16px', color: 'var(--auth-text-muted)', pointerEvents: 'none' }} />
                  <input
                    type="text"
                    placeholder={t('auth.admin_username_placeholder', "Username (masalan: admin)")}
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
                    type={showPassword ? "text" : "password"}
                    placeholder={t('auth.admin_password_placeholder', "Parolni kiriting...")}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    style={{ paddingLeft: '46px', paddingRight: '46px' }}
                    required
                  />
                  <button
                    type="button"
                    className="eye-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex="-1"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>
            ) : (
              <div className="otp-code-section">
                <label className="otp-section-label">
                  {t('auth.enter_bot_code', 'TELEGRAM BOTDAN OLGAN KODINGIZNI KIRITING')}
                </label>

                <div className="otp-boxes-grid" onPaste={handlePaste}>
                  {codeDigits.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={(el) => (inputRefs.current[idx] = el)}
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      maxLength={6}
                      value={digit}
                      onChange={(e) => handleDigitChange(idx, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(idx, e)}
                      onFocus={(e) => e.target.select()}
                      disabled={loading}
                      className="otp-box-input"
                      aria-label={`Kodning ${idx + 1}-raqami`}
                    />
                  ))}
                </div>

                <p className="otp-bot-instruction">
                  {t('auth.otp_bot_instruction_prefix', 'Telegram botga ')}
                  <code className="cmd-pill">/login</code>
                  {t('auth.otp_bot_instruction_middle', " yozing va 6 xonali kodni oling. Botga o'tish: ")}
                  <a 
                    href="https://t.me/aparty_bot" 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="bot-link"
                  >
                    @aparty_bot
                  </a>
                </p>
              </div>
            )}

            {error && <div className="error-alert-liquid">{error}</div>}

            <button
              type="submit"
              className="btn-liquid-primary"
              disabled={loading || (isAdmin ? (!username.trim() || !password) : code.length < 6)}
            >
              <span className="shimmer-effect"></span>
              <span className="btn-content">
                {loading ? <PremiumLoader mini /> : (
                  <>
                    <KeyRound size={18} style={{ marginRight: '8px' }} />
                    {isAdmin ? t('auth.submit_admin_login', 'Admin panelga kirish') : t('auth.submit_login', 'Tizimga kirish')}
                  </>
                )}
              </span>
            </button>
          </form>

          {!isAdmin && (
            <footer className="footer-links-liquid">
              <p>
                {t('auth.no_account', "Hisobingiz yo'qmi?")}{' '}
                <Link to="/register" className="highlight-link">
                  {t('auth.register', "Ro'yxatdan o'tish")}
                </Link>
              </p>
              <button
                type="button"
                className="btn-ghost-sm"
                onClick={() => navigate('/login?admin=true')}
              >
                {t('auth.admin_login', 'Admin sifatida kirish')}
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
                {t('auth.back_to_login', 'Foydalanuvchi sifatida kirish')}
              </button>
            </footer>
          )}
        </div>
      </motion.div>
    </div>
  )
}

