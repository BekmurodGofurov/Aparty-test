import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BadgeCheck, Check, Crown, Gem, Infinity as InfinityIcon, Sparkles, Zap } from 'lucide-react'
import { api } from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import './MaklerSubscription.scss'

export function MaklerSubscription() {
  const navigate = useNavigate()
  const role = useAuthStore((s) => s.role)
  const basePath = role === 'broker' ? '/broker' : '/makler'
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const plans = [
    {
      id: 'free',
      name: 'Pay per lead',
      eyebrow: 'Flexible start',
      price: 5,
      listings: 5,
      icon: Sparkles,
      tone: 'free',
      features: ['Har bir lead uchun to\'lov', '5 ta faol e\'lon', 'Smart matching preview', 'Basic statistikalar'],
    },
    {
      id: 's',
      name: 'S tarifi',
      eyebrow: 'Recommended',
      price: 79,
      listings: 25,
      icon: Zap,
      tone: 'recommended',
      features: ['25 ta faol e\'lon', 'Lead management', 'AI e\'lon optimizatsiya', 'Boosted visibility', 'CRM mini-panel'],
    },
    {
      id: 'l',
      name: 'L tarifi',
      eyebrow: 'Scale mode',
      price: 149,
      listings: 100,
      icon: Crown,
      tone: 'elite',
      features: ['100 ta faol e\'lon', 'Premium support', 'Advanced analytics', 'Smart matching', 'Jamoa uchun CRM tools'],
    },
  ]

  const handleSubscribe = async (planId) => {
    setLoading(true)
    setError('')
    try {
      await api.post(`/subscriptions/${planId}`, {})
      navigate(basePath)
    } catch (err) {
      setError(err.response?.data?.detail || 'Obunani faollashtirishda xatolik yuz berdi')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="makler-subscription">
      <div className="page-container">
        <section className="subscription-hero">
          <motion.div
            className="subscription-orb"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: 'spring', stiffness: 180, damping: 22 }}
          >
            <Gem size={28} />
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
          >
            <p className="subscription-eyebrow">Aparty billing</p>
            <h1>Obunani yangilash</h1>
            <p className="subtitle">Makler portfelingiz uchun lead management, AI tools, ko'rinish boosti va premium statistikalar.</p>
          </motion.div>
          <div className="billing-toggle" aria-label="Billing mode">
            <button type="button" className="active">Oylik</button>
            <button type="button">Yillik</button>
          </div>
        </section>

        {error && <div className="error-message">{error}</div>}

        <div className="plans-grid">
          {plans.map((plan, index) => {
            const Icon = plan.icon
            return (
            <motion.div
              key={plan.id}
              className={`plan-card plan-card--${plan.tone}`}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08, type: 'spring', stiffness: 220, damping: 24 }}
              whileHover={{ y: -8, scale: 1.012 }}
            >
              {plan.tone === 'recommended' && <div className="plan-ribbon"><BadgeCheck size={14} /> Eng ma'qul</div>}
              <div className="plan-top">
                <div className="plan-icon"><Icon size={22} /></div>
                <div>
                  <span>{plan.eyebrow}</span>
                  <h3>{plan.name}</h3>
                </div>
              </div>
              <div className="plan-price">
                <span>$</span>{plan.price}<small>/oy</small>
              </div>
              <div className="plan-listings">
                <InfinityIcon size={16} />
                {plan.listings} tagacha faol e'lon
              </div>
              <div className="plan-features">
                {plan.features.map((feature) => (
                  <div key={feature} className="feature">
                    <Check size={15} />
                    {feature}
                  </div>
                ))}
              </div>
              <button
                className="btn-primary"
                onClick={() => handleSubscribe(plan.id)}
                disabled={loading}
              >
                {loading ? 'Jarayonda...' : 'Obuna bo\'lish'}
              </button>
            </motion.div>
          )})}
        </div>

        <section className="subscription-compare">
          <div>
            <span>AI tools</span>
            <strong>Tezroq e'lon tayyorlash</strong>
          </div>
          <div>
            <span>Lead CRM</span>
            <strong>Mijozlarni nazorat qilish</strong>
          </div>
          <div>
            <span>Analytics</span>
            <strong>Real natijani ko'rish</strong>
          </div>
        </section>
      </div>
    </main>
  )
}
