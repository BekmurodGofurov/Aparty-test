/**
 * APARTY.UZ — PREMIUM HOME PAGE v4.0
 * Aurora Glass Design — Immersive, conversion-focused, elegant
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  MapPin, Home, Users, Star, Shield,
  CheckCircle, Sparkles, ChevronRight, Zap,
  TrendingUp, Clock, ArrowRight,
} from 'lucide-react'
import { PremiumListingCard } from '../../../components/listing/PremiumListingCard'
import { HomeSearchBar } from '../../../components/search/HomeSearchBar'
import { ListingCardSkeleton } from '../../../components/ui/ListingCardSkeleton.jsx'
import { searchListings } from '../../../services/listingService'
import { PLACEHOLDER_IMAGE } from '../../../utils/images'
import { useAuthStore } from '../../../store/authStore'
import { useThemeStore } from '../../../store/themeStore'
import './HomePremium.scss'

const HOME_LISTING_LIMIT = 8

const TRUST_BADGES = [
  { icon: CheckCircle, label: 'Ishonchli va tekshirilgan',  key: 'verified' },
  { icon: Shield,      label: 'Hech qanday komissiyasiz',   key: 'free' },
  { icon: Sparkles,    label: 'Talabalar uchun qulay',   key: 'student' },
]

// Tabs over the real catalog: each one is a search filter the backend understands.
const LISTING_TABS = [
  { key: 'all',      label: 'Barchasi',             filters: {} },
  { key: 'roommate', label: 'Sherik izlayotganlar', filters: { owner_role: 'student' } },
  { key: 'room',     label: 'Xonalar',              filters: { rental_type: 'shared_room' } },
]

const HOW_STEPS = [
  { num: '01', emoji: '🔍', title: 'Qidiring va toping', desc: 'O\'zingizga mos kvartirani lokatsiya, narx va xonalar soni bo\'yicha filterlang.' },
  { num: '02', emoji: '💬', title: 'Telegram orqali bog\'laning', desc: 'Band qilish so\'rovini yuboring yoki uy egasiga to\'g\'ridan-to\'g\'ri Telegramda yozing.' },
  { num: '03', emoji: '🏠', title: 'Ko\'chib o\'ting',  desc: 'So\'rov qabul qilingach, uy egasi bilan kelishing va yangi uyingizga ko\'chib o\'ting.' },
]

const ADVANTAGES = [
  { icon: Home, title: 'Komissiyasiz', desc: 'Ijarachilar uchun mutlaqo bepul. Maklerlarga ortiqcha pul to\'lamaysiz.' },
  { icon: Clock, title: 'Tezkor aloqa', desc: 'Uy egasi bilan Telegram yoki telefon orqali darhol bog\'laning.' },
  { icon: Users, title: 'Sherik topish', desc: 'Kvartirada yashovchilar bo\'sh joy uchun sherik izlab e\'lon berishi mumkin.' },
  { icon: Shield, title: 'Telegram orqali kirish', desc: 'Parol kerak emas: hisobingiz Telegram raqamingiz bilan tasdiqlanadi.' },
]

// ── COMPONENT ────────────────────────────────────────────────────────────────
export function HomePremium() {
  const navigate  = useNavigate()
  const { t }     = useTranslation()
  const role = useAuthStore((state) => state.role)
  const { theme } = useThemeStore()
  const isLight   = theme === 'light'

  // Theme-aware inline styles for section text (bypasses CSS nesting issues)
  const eyebrowStyle = isLight
    ? { color: '#B45309' }
    : { color: 'var(--color-primary-light)' }

  const titleStyle = isLight
    ? { color: '#0C0A06' }
    : { color: '#F1F5F9' }

  const subStyle = isLight
    ? { color: '#57534E' }
    : { color: '#94A3B8' }

  const [activeFilter, setActiveFilter] = useState(LISTING_TABS[0].key)
  const [listings, setListings] = useState([])
  const [totalListings, setTotalListings] = useState(null)
  const [status, setStatus] = useState('loading')

  const selectTab = (key) => {
    if (key === activeFilter) return
    setStatus('loading')
    setActiveFilter(key)
  }

  useEffect(() => {
    let cancelled = false
    const tab = LISTING_TABS.find((item) => item.key === activeFilter)
    searchListings(tab.filters, 1, HOME_LISTING_LIMIT)
      .then((data) => {
        if (cancelled) return
        setListings(data.listings || [])
        if (activeFilter === LISTING_TABS[0].key) setTotalListings(data.total ?? null)
        setStatus('ready')
      })
      .catch(() => { if (!cancelled) setStatus('error') })
    return () => { cancelled = true }
  }, [activeFilter])

  return (
    <main className="home-premium">

      {/* ══════════════════════════════════════════════════════════════════
          HERO SECTION — Immersive full-viewport introduction
      ══════════════════════════════════════════════════════════════════ */}
      <section className="hero relative overflow-hidden">
        {/* Background image layer - static for performance */}
        <div className="hero-bg absolute inset-0 z-0" aria-hidden>
          <img
            src="/hero.jpg"
            fetchPriority="high"
            decoding="async"
            alt=""
            className="hero-bg-img"
          />
        </div>

        {/* Hero content */}
        <div className="hero-content">
          <div className="hero-inner">
            {/* Trust badges row */}
            <div className="trust-row">
              {TRUST_BADGES.map(({ icon: Icon, label, key }) => (
                <span key={key} className="trust-badge">
                  <Icon size={13} />
                  {t(label)}
                </span>
              ))}
            </div>

            {/* Main heading */}
            <h1 className="hero-title">
              {t('home.hero_title_prefix', 'Andijonda')}{' '}
              <span className="gradient-text">
                {t('home.hero_title_accent', 'kvartira toping')}
              </span>
            </h1>

            {/* Subtitle */}
            <p className="hero-subtitle">
              {t('home.hero_subtitle', 'Talabalar, oilalar va yoshlar uchun ishonchli va qulay ijaralar — hech qanday komissiyasiz')}
            </p>

            {/* ── SEARCH BAR ───────────────────────────────────────────── */}
            <div className="hero-search-wrap">
              <HomeSearchBar />
            </div>



            {/* ── QUICK STATS ──────────────────────────────────────────── */}
            {totalListings !== null && (
              <div className="hero-stats">
                <div className="hero-stat">
                  <div className="stat-icon"><MapPin size={18} /></div>
                  <div className="stat-body">
                    <strong>{totalListings}</strong>
                    <span>{t("Faol e'lonlar")}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="scroll-hint" aria-hidden>
          <div className="scroll-dot" />
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          FEATURED LISTINGS
      ══════════════════════════════════════════════════════════════════ */}
      <section className="home-section featured-section">
        <div className="section-container">
          {/* Header */}
          <div className="section-head">
            <div>
              <p className="section-eyebrow" style={eyebrowStyle}>
                <Star size={14} />
                {t('home.featured_label', "So'nggi e'lonlar")}
              </p>
              <h2 className="section-title" style={titleStyle}>{t('home.featured_title', "Tanlangan e'lonlar")}</h2>
              <p className="section-sub" style={subStyle}>{t('home.featured_subtitle', 'Andijondagi eng sifatli kvartiralar')}</p>
            </div>

            {/* Filter pills */}
            <div className="filter-pills">
              {LISTING_TABS.map(({ key, label }) => (
                <button
                  key={key}
                  className={`pill ${activeFilter === key ? 'active' : ''}`}
                  onClick={() => selectTab(key)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Grid */}
          <div className="listings-grid">
            {status === 'loading' && Array.from({ length: 4 }, (_, index) => <ListingCardSkeleton key={index} />)}
            {status === 'error' && (
              <div className="empty-filter-state" style={{ gridColumn: '1 / -1', padding: '3rem', textAlign: 'center', color: 'var(--color-muted)' }}>
                E'lonlarni yuklab bo'lmadi. Keyinroq qayta urinib ko'ring.
              </div>
            )}
            {status === 'ready' && listings.length === 0 && (
              <div className="empty-filter-state" style={{ gridColumn: '1 / -1', padding: '3rem', textAlign: 'center', color: 'var(--color-muted)' }}>
                Bu bo'limda hozircha e'lonlar yo'q
              </div>
            )}
            {status === 'ready' && listings.map((listing) => (
              <PremiumListingCard
                key={listing.id}
                id={listing.id}
                image={listing.images?.[0] || PLACEHOLDER_IMAGE}
                title={listing.address || `${listing.district || ''}, ${listing.region || ''}`}
                location={`${listing.district || ''}, ${listing.region || ''}`}
                price={listing.price}
                rooms={listing.rooms_count}
                isPremium={listing.is_premium}
                isVerified={listing.owner_verified}
                isFavorite={listing.is_favorite}
                onClick={() => navigate(`/listing/${listing.id}`)}
              />
            ))}
          </div>

          {/* View all CTA */}
          <div className="section-cta">
            <button className="btn-outline" onClick={() => navigate('/search')}>
              {t('home.view_all', "Barcha e'lonlar")}
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          HOW IT WORKS
      ══════════════════════════════════════════════════════════════════ */}
      <section className="home-section how-section">
        <div className="section-container">
          <div className="section-head centered">
            <p className="section-eyebrow" style={eyebrowStyle}><Clock size={14} /> {t('home.how_label', 'Qanday ishlaydi')}</p>
            <h2 className="section-title" style={titleStyle}>{t('home.how_title', '3 oddiy qadam')}</h2>
            <p className="section-sub" style={subStyle}>{t('home.how_subtitle', "Kvartira topish hech qachon bu qadar oson bo'lmagan")}</p>
          </div>

          <div className="how-grid">
            {HOW_STEPS.map(step => (
              <div key={step.num} className="how-card">
                <div className="how-num">{step.num}</div>
                <div className="how-emoji">{step.emoji}</div>
                <h3>{t(step.title)}</h3>
                <p>{t(step.desc)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          PLATFORM ADVANTAGES
      ══════════════════════════════════════════════════════════════════ */}
      <section className="home-section advantages-section">
        <div className="section-container">
          <div className="section-head centered">
            <p className="section-eyebrow" style={eyebrowStyle}><Shield size={14} /> Nega aynan Aparty?</p>
            <h2 className="section-title" style={titleStyle}>Bizning afzalliklarimiz</h2>
            <p className="section-sub" style={subStyle}>Biz ijarachilar va uy egalari o'rtasida ishonchli va zamonaviy ko'prik vazifasini bajaramiz.</p>
          </div>

          <div className="advantages-grid">
            {ADVANTAGES.map((adv) => {
              const Icon = adv.icon
              return (
                <div key={adv.title} className="advantage-card">
                  <div className="adv-icon-wrapper">
                    <Icon size={24} />
                  </div>
                  <h3>{adv.title}</h3>
                  <p>{adv.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          OWNER CTA
      ══════════════════════════════════════════════════════════════════ */}
      <section className="home-section owner-cta-section">
        <div className="section-container">
          <div className="owner-cta-card">
            <div className="owner-cta-glow" aria-hidden />
            <div className="owner-cta-content">
              <p className="section-eyebrow" style={eyebrowStyle}><Zap size={14} /> {t('home.owner_label', 'Uy egalari uchun')}</p>
              <h2 style={titleStyle}>{t('home.owner_cta_title', 'Kvartira yoki xonangizni ijaraga bering')}</h2>
              <p style={subStyle}>{t('home.owner_cta_desc', "Minglab talabalar va oilalar siz bilan bog'lanishini kutmoqda")}</p>

              <div className="owner-features">
                {[
                  { icon: Zap,        label: t('home.owner_feat_1', 'Tez e\'lon joylash') },
                  { icon: Users,      label: t('home.owner_feat_2', 'Ko\'p auditoriya') },
                  { icon: TrendingUp, label: t('home.owner_feat_3', 'Daromad oshirish') },
                ].map(({ icon: Icon, label }) => (
                  <span key={label} className="owner-feat">
                    <Icon size={16} /> {label}
                  </span>
                ))}
              </div>

              <button
                className="btn-owner-cta"
                onClick={() => navigate(role ? (role === 'makler' ? '/makler/create' : '/owner/create') : '/login')}
              >
                {role ? t('home.owner_cta_btn_logged', "E'lon joylash") : t('home.owner_cta_btn', 'Hozir boshlash')}
                <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>
      </section>

    </main>
  )
}
