/** Photo-led home page with live catalog data and one-time section reveals. */

import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  ArrowDown, ArrowUpRight, KeyRound, MessageCircle, Search, MapPin, Home, Users, Star, Shield,
  CheckCircle, Sparkles, ChevronRight, Zap,
  TrendingUp, Clock, ArrowRight,
} from 'lucide-react'
import { PremiumListingCard } from '../../../components/listing/PremiumListingCard'
import { HomeSearchBar } from '../../../components/search/HomeSearchBar'
import { ListingCardSkeleton } from '../../../components/ui/ListingCardSkeleton.jsx'
import { searchListings } from '../../../services/listingService'
import { peekCache } from '../../../services/browserCache'
import { PLACEHOLDER_IMAGE } from '../../../utils/images'
import { useAuthStore } from '../../../store/authStore'
import { useThemeStore } from '../../../store/themeStore'
import './HomePremium.scss'

const HOME_LISTING_LIMIT = 8

const TRUST_BADGES = [
  { icon: CheckCircle, key: 'verified' },
  { icon: Shield, key: 'free' },
  { icon: Users, key: 'student' },
]

// Tabs over the real catalog: each one is a search filter the backend understands.
const LISTING_TABS = [
  { key: 'all',      label: 'Barchasi',             filters: {} },
  { key: 'roommate', label: 'Sherik izlayotganlar', filters: { owner_role: 'student' } },
  { key: 'room',     label: 'Xonalar',              filters: { rental_type: 'shared_room' } },
]

const HOW_STEPS = [
  { num: '01', icon: Search, title: 'home.how_search_title', desc: 'home.how_search_desc' },
  { num: '02', icon: MessageCircle, title: 'home.how_connect_title', desc: 'home.how_connect_desc' },
  { num: '03', icon: KeyRound, title: 'home.how_movein_title', desc: 'home.how_movein_desc' },
]

const ADVANTAGES = [
  { icon: Home, key: 'no_fee' },
  { icon: Clock, key: 'direct' },
  { icon: Users, key: 'roommate' },
  { icon: Shield, key: 'telegram' },
]

// The params searchListings(filters, 1, HOME_LISTING_LIMIT) sends, so a cache lookup matches exactly.
const searchParamsFor = (tab) => ({ ...tab.filters, page: 1, limit: HOME_LISTING_LIMIT })
const cachedTab = (key) => peekCache('/listings/search', searchParamsFor(LISTING_TABS.find((item) => item.key === key)))

// ── COMPONENT ────────────────────────────────────────────────────────────────
export function HomePremium() {
  const navigate  = useNavigate()
  const { t }     = useTranslation()
  const role = useAuthStore((state) => state.role)
  const theme = useThemeStore((state) => state.theme)
  const isLight   = theme === 'light'
  const rootRef = useRef(null)

  // Observe each section once. No per-frame scroll state or offscreen animation loops.
  useEffect(() => {
    const root = rootRef.current
    if (!root || !('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined
    const elements = root.querySelectorAll('[data-reveal]')
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue
        entry.target.classList.add('is-revealed')
        observer.unobserve(entry.target)
      }
    }, { threshold: 0.12 })
    root.classList.add('motion-ready')
    elements.forEach(element => observer.observe(element))
    return () => {
      observer.disconnect()
      root.classList.remove('motion-ready')
    }
  }, [])

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
  // Revisiting the home page (e.g. via the browser back button) paints the last-known listings for
  // the active tab straight away instead of a loading flash, then quietly refreshes them below.
  const [listings, setListings] = useState(() => cachedTab(LISTING_TABS[0].key)?.listings || [])
  const [totalListings, setTotalListings] = useState(() => cachedTab(LISTING_TABS[0].key)?.total ?? null)
  const [status, setStatus] = useState(() => (cachedTab(LISTING_TABS[0].key) ? 'ready' : 'loading'))

  const selectTab = (key) => {
    if (key === activeFilter) return
    const cached = cachedTab(key)
    setListings(cached?.listings || [])
    setStatus(cached ? 'ready' : 'loading')
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
      .catch(() => { if (!cancelled && cachedTab(activeFilter) === undefined) setStatus('error') })
    return () => { cancelled = true }
  }, [activeFilter])

  return (
    <div className="home-premium" ref={rootRef}>

      {/* ══════════════════════════════════════════════════════════════════
          HERO SECTION — Immersive full-viewport introduction
      ══════════════════════════════════════════════════════════════════ */}
      <section className="hero" aria-labelledby="home-hero-title">
        {/* Background image layer - static for performance */}
        <div className="hero-bg absolute inset-0 z-0" aria-hidden>
          <img
            src="/hero.jpg"
            fetchPriority="high"
            decoding="async"
            alt=""
            className="hero-bg-img"
          />
          <div className="hero-bg-overlay" />
          <div className="hero-frame" />
        </div>

        {/* Hero content */}
        <div className="hero-content">
          <div className="hero-inner">
            <p className="hero-eyebrow"><span className="hero-status-dot" /><span>{t('home.experience.eyebrow')}</span><Sparkles size={14} aria-hidden="true" /></p>

            {/* Main heading */}
            <h1 className="hero-title" id="home-hero-title">
              <span className="hero-title-line">{t('home.hero_title_prefix', 'Andijonda')}</span>{' '}
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



            <div className="trust-row">
              {TRUST_BADGES.map(({ icon: Icon, key }) => (
                <span key={key} className="trust-badge"><Icon size={14} aria-hidden="true" />{t(`home.experience.${key}`)}</span>
              ))}
            </div>

            {/* Real catalog count; no simulated users, ratings or availability. */}
            {totalListings !== null && (
              <div className="hero-stats">
                <div className="hero-stat">
                  <div className="stat-icon"><MapPin size={18} /></div>
                  <div className="stat-body">
                    <strong>{totalListings}</strong>
                    <span>{t('home.experience.live_listings')}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="hero-footer"><span className="hero-location"><MapPin size={14} />Andijon, Uzbekistan</span><button type="button" className="hero-explore" onClick={() => document.getElementById('home-featured')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' })}>{t('home.experience.explore')}<ArrowDown size={15} /></button><span className="hero-signature">APARTY<span> / </span>YOUR NEXT CHAPTER</span></div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          FEATURED LISTINGS
      ══════════════════════════════════════════════════════════════════ */}
      <section className="home-section featured-section" id="home-featured" aria-labelledby="featured-heading">
        <div className="section-container">
          {/* Header */}
          <div className="section-head" data-reveal>
            <div>
              <p className="section-eyebrow" style={eyebrowStyle}>
                <Star size={14} />
                {t('home.featured_label', "So'nggi e'lonlar")}
              </p>
              <h2 className="section-title" id="featured-heading" style={titleStyle}>{t('home.featured_title', "Tanlangan e'lonlar")}</h2>
              <p className="section-sub" style={subStyle}>{t('home.featured_subtitle', 'Andijondagi eng sifatli kvartiralar')}</p>
            </div>

            {/* Filter pills */}
            <div className="filter-pills" role="group" aria-label={t('home.experience.listing_filters')}>
              {LISTING_TABS.map(({ key, label }) => (
                <button
                  key={key}
                  className={`pill ${activeFilter === key ? 'active' : ''}`}
                  type="button"
                  aria-pressed={activeFilter === key}
                  onClick={() => selectTab(key)}
                >
                  {t(`home.experience.tab_${key}`, label)}
                </button>
              ))}
            </div>
          </div>

          {/* Grid */}
          <div className="listings-grid">
            {status === 'loading' && Array.from({ length: 4 }, (_, index) => <ListingCardSkeleton key={index} />)}
            {status === 'error' && (
              <div className="empty-filter-state" role="status">
                <Search size={28} aria-hidden="true" /><h3>{t('home.experience.load_error')}</h3><p>{t('home.experience.load_error_hint')}</p>
              </div>
            )}
            {status === 'ready' && listings.length === 0 && (
              <div className="empty-filter-state" role="status">
                <span className="empty-icon"><Home size={28} strokeWidth={1.5} aria-hidden="true" /></span><h3>{t('home.experience.empty_title')}</h3><p>{t('home.experience.empty_desc')}</p><button type="button" onClick={() => navigate('/search')}>{t('home.experience.empty_action')}<ArrowUpRight size={16} /></button>
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
          <div className="section-head centered" data-reveal>
            <p className="section-eyebrow" style={eyebrowStyle}><Clock size={14} /> {t('home.how_label', 'Qanday ishlaydi')}</p>
            <h2 className="section-title" style={titleStyle}>{t('home.how_title', '3 oddiy qadam')}</h2>
            <p className="section-sub" style={subStyle}>{t('home.how_subtitle', "Kvartira topish hech qachon bu qadar oson bo'lmagan")}</p>
          </div>

          <div className="how-grid">
            {HOW_STEPS.map(({ num, icon: Icon, title, desc }, index) => (
              <div key={num} className="how-card" data-reveal style={{ '--reveal-delay': `${index * 70}ms` }}>
                <div className="how-top"><div className="how-icon"><Icon size={25} strokeWidth={1.6} /></div><span className="how-num">{num}</span></div>
                <h3>{t(title)}</h3>
                <p>{t(desc)}</p>
                <ArrowUpRight size={19} className="how-arrow" aria-hidden="true" />
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
          <div className="section-head centered" data-reveal>
            <p className="section-eyebrow" style={eyebrowStyle}><Shield size={14} />{t('home.experience.advantages_label')}</p>
            <h2 className="section-title" style={titleStyle}>{t('home.experience.advantages_title')}</h2>
            <p className="section-sub" style={subStyle}>{t('home.experience.advantages_desc')}</p>
          </div>

          <div className="advantages-grid">
            {ADVANTAGES.map((adv, index) => {
              const Icon = adv.icon
              return (
                <div key={adv.key} className="advantage-card" data-reveal style={{ '--reveal-delay': `${index * 60}ms` }}>
                  <div className="adv-icon-wrapper">
                    <Icon size={24} />
                  </div>
                  <h3>{t(`home.experience.${adv.key}_title`)}</h3>
                  <p>{t(`home.experience.${adv.key}_desc`)}</p>
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
          <div className="owner-cta-card" data-reveal>
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
            <div className="owner-cta-art" aria-hidden="true"><span className="owner-orbit" /><span className="owner-orbit inner" /><Home size={172} strokeWidth={0.65} /><span className="owner-art-label">APARTY.UZ</span></div>
          </div>
        </div>
      </section>

    </div>
  )
}
