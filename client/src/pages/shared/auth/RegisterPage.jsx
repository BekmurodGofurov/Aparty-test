import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Send, Sparkles } from 'lucide-react'
import './Auth.scss'

export function RegisterPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  
  const botUsername = 'aparty_bot' 
  const botLink = `https://t.me/${botUsername}`

  return (
    <div className="auth-page liquid-theme">
      <motion.div 
        className="auth-liquid-container"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="liquid-card main-panel">
          <header className="brand-header-premium">
            <div className="logo-orb">
              <span>A</span>
            </div>
            <h2 className="brand-text">Aparty<span>.uz</span></h2>
          </header>

          <section className="hero-content">
            <h1 className="title-premium">{t('auth.register_title', "Ro'yxatdan o'tish")}</h1>
            <p className="subtitle-premium">
              {t('auth.register_subtitle', "Aparty.uz ga qo'shilish uchun ro'yxatdan o'ting")}
            </p>
          </section>

          <div className="bot-display-premium">
            <div className="bot-details">
              <span className="label">RASMIY BOT</span>
              <span className="username">@{botUsername}</span>
            </div>
          </div>

          <div className="action-stack-premium">
            <a href={botLink} target="_blank" rel="noopener noreferrer" className="btn-liquid-primary">
              <span className="shimmer-effect"></span>
              <span className="btn-content">
                {t('auth.btn_telegram', 'Telegram botni ochish')} <Send size={20} />
              </span>
            </a>
            
            <button className="btn-liquid-outline" onClick={() => navigate('/')}>
              <span>{t('auth.btn_home', 'Bosh sahifa')}</span>
            </button>
          </div>

          <footer className="footer-links-premium">
            <span>{t('auth.have_account', 'Hisobingiz bormi?')}</span>
            <Link to="/login" className="login-trigger">{t('auth.submit_login', 'Kirish')}</Link>
          </footer>
        </div>

        {/* Informational Sidebar (Solid and distinct) */}
        <div className="liquid-card info-panel">
          <div className="panel-header">
            <span className="step-badge">{t('auth.how_it_works_title', "RO'YXATDAN O'TISH TARTIBI")}</span>
          </div>

          <div className="steps-container-premium">
            {[1, 2, 3, 4, 5, 6].map((num) => (
              <motion.div 
                className="step-item-premium" 
                key={num}
                whileHover={{ x: 10 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <div className="step-orb">{num}</div>
                <p className="step-text">
                  {t(`auth.tg_step_${num}`, `${num}) ...`)}
                </p>
              </motion.div>
            ))}
          </div>

          <div className="premium-alert-box">
             <div className="alert-glow"></div>
             <p>
               <Sparkles size={16} /> {t('auth.tg_box_2_title', "Telefon raqam + generatsiya qilingan parol orqali saytga kirasiz.")}
             </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
