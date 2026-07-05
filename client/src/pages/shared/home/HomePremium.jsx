/**
 * APARTY.UZ — PREMIUM HOME PAGE v4.0
 * Aurora Glass Design — Immersive, conversion-focused, elegant
 */

import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MapPin, Home, Users, Star, Shield,
  CheckCircle, Sparkles, ChevronRight, Zap,
  TrendingUp, Clock, ArrowRight, Building, Key,
  Grid, Compass, Box, Ruler
} from 'lucide-react'
import { PremiumListingCard } from '../../../components/listing/PremiumListingCard'
import { HomeSearchBar } from '../../../components/search/HomeSearchBar'
import { useAuthStore } from '../../../store/authStore'
import { useThemeStore } from '../../../store/themeStore'
import './HomePremium.scss'

// ── ANIMATION VARIANTS ──────────────────────────────────────────────────────
const smoothEase = [0.16, 1, 0.3, 1]

const fadeUp = {
  hidden:  { opacity: 0, y: 12 },
  visible: (delay = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.58, ease: smoothEase, delay }
  })
}

const stagger = {
  hidden:  {},
  visible: { transition: { staggerChildren: 0.075, delayChildren: 0.04 } }
}

const cardItem = {
  hidden:  { opacity: 0, y: 14, scale: 0.985 },
  visible: { opacity: 1, y: 0,  scale: 1, transition: { duration: 0.48, ease: smoothEase } }
}

// ── CONSTANTS & FAKE DATA (Backend Offline Fallback) ─────────────────────────
const DISTRICTS = [
  'Andijon shahar', 'Asaka', 'Shahrixon', 'Jalolquduq',
  'Xo\'jaobod', 'Oltinko\'l', 'Baliqchi', 'Buloqboshi',
  'Izboskan', 'Marhamat', 'Ulug\'nor', 'Qo\'rg\'ontepa',
]

const TRUST_BADGES = [
  { icon: CheckCircle, label: 'Ishonchli va tekshirilgan',  key: 'verified' },
  { icon: Shield,      label: 'Hech qanday komissiyasiz',   key: 'free' },
  { icon: Sparkles,    label: 'Talabalar uchun qulay',   key: 'student' },
]

const STATS = [
  { icon: MapPin,      value: '12,000+', label: 'Faol e\'lonlar' },
  { icon: Users,       value: '8,500+', label: 'Foydalanuvchilar' },
  { icon: Home,        value: '95%',    label: 'Muvaffaqiyatli ijara' },
  { icon: Star,        value: '4.9',    label: 'O\'rtacha reyting' },
]

const HOW_STEPS = [
  { num: '01', emoji: '🔍', title: 'Qidiring va toping', desc: 'O\'zingizga mos kvartirani lokatsiya, narx va xonalar soni bo\'yicha filterlang.' },
  { num: '02', emoji: '💬', title: 'To\'g\'ridan-to\'g\'ri aloqa', desc: 'Hech qanday maklerlarsiz, to\'g\'ridan-to\'g\'ri uy egasi bilan bog\'laning va gaplashing.' },
  { num: '03', emoji: '🏠', title: 'Ko\'chib o\'ting',  desc: 'Shartnomani tasdiqlang va yangi uyingizga xotirjam ko\'chib o\'ting.' },
]

const TESTIMONIALS = [
  { name: 'Zarina K.',    role: 'Talaba', avatar: '👩‍🎓',    quote: 'Aparty orqali Andijon Davlat Universiteti yonidan juda arzon va qulay xona topdim. AI qidiruvi ajoyib ishladi!', rating: 5 },
  { name: 'Sardor M.',   role: 'Yosh oila',   avatar: '👨‍👩‍👦',    quote: 'Uylanishim arafasida edim, maklerlarga pul to\'lashni xohlamagandim. Sayt orqali to\'g\'ridan-to\'g\'ri uy egasi bilan kelishdik.', rating: 5 },
  { name: 'Nodira S.',   role: 'Uy egasi',   avatar: '👩‍💼', quote: 'Ijarachilarni topish endi juda oson. Sayt orqali 2 kun ichida ishonchli talaba qizlarni topdim.', rating: 5 },
]

const ADVANTAGES = [
  { icon: Shield, title: '100% Xavfsiz', desc: 'Barcha uy egalari shaxsni tasdiqlovchi hujjatlar orqali tekshirilgan.' },
  { icon: Sparkles, title: 'AI Qidiruv', desc: 'Sun\'iy intellekt sizning talablaringizga 99% mos tushuvchi uyni topadi.' },
  { icon: Home, title: 'Komissiyasiz', desc: 'Ijarachilar uchun mutlaqo bepul. Maklerlarga ortiqcha pul to\'lamaysiz.' },
  { icon: Clock, title: 'Tezkor aloqa', desc: 'Uy egasi bilan to\'g\'ridan-to\'g\'ri chat orqali bog\'laning va darhol ko\'chib o\'ting.' }
]

const LOCATIONS = [
  { name: 'Andijon shahar markazi', count: '340+ e\'lon', img: 'https://images.unsplash.com/photo-1449844908441-8829872d2607?q=80&w=2070&auto=format&fit=crop' },
  { name: 'ADU atrofi', count: '120+ e\'lon', img: 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?q=80&w=2070&auto=format&fit=crop' },
  { name: 'Asaka tumani', count: '85+ e\'lon', img: 'https://images.unsplash.com/photo-1518780664697-55e3ad937233?q=80&w=2065&auto=format&fit=crop' },
]

// Realistic Demo Listings
const DEMO_LISTINGS = [
  { id: '101', viloyat: 'Andijon', tuman: 'Andijon shahar', manzil: 'Navoiy shoh ko\'chasi, 12-dom', narx_usd: 250, xonalar_soni: 2, premium: true, egasi_verified: true, rasmlar: ['https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?q=80&w=2070&auto=format&fit=crop'], maydon: 65, qavat: '3/4', wifi: true, type: 'family' },
  { id: '102', viloyat: 'Andijon', tuman: 'Andijon shahar', manzil: 'Bobur maydoni yonida', narx_usd: 180, xonalar_soni: 1, premium: false, egasi_verified: true, rasmlar: ['https://images.unsplash.com/photo-1502672260266-1c1de2d93688?q=80&w=1980&auto=format&fit=crop'], maydon: 40, qavat: '2/5', wifi: true, type: 'student' },
  { id: '103', viloyat: 'Andijon', tuman: 'Asaka', manzil: 'Markaziy shifoxona ro\'parasida', narx_usd: 300, xonalar_soni: 3, premium: true, egasi_verified: true, rasmlar: ['https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?q=80&w=2075&auto=format&fit=crop'], maydon: 90, qavat: '1/4', wifi: false, type: 'luxury' },
  { id: '104', viloyat: 'Andijon', tuman: 'Shahrixon', manzil: 'Bozor yonida, tinch mahalla', narx_usd: 150, xonalar_soni: 2, premium: false, egasi_verified: false, rasmlar: ['https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?q=80&w=2070&auto=format&fit=crop'], maydon: 55, qavat: '1/1', wifi: true, type: 'student' },
  { id: '105', viloyat: 'Andijon', tuman: 'Andijon shahar', manzil: 'Makro supermarketi ustida', narx_usd: 400, xonalar_soni: 4, premium: true, egasi_verified: true, rasmlar: ['https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?q=80&w=2070&auto=format&fit=crop'], maydon: 120, qavat: '5/7', wifi: true, type: 'luxury' },
  { id: '106', viloyat: 'Andijon', tuman: 'Andijon shahar', manzil: 'Universitet yotoqxonasi yonida', narx_usd: 120, xonalar_soni: 1, premium: false, egasi_verified: true, rasmlar: ['https://images.unsplash.com/photo-1554995207-c18c203602cb?q=80&w=2070&auto=format&fit=crop'], maydon: 35, qavat: '4/4', wifi: true, type: 'student' },
  { id: '107', viloyat: 'Andijon', tuman: 'Xo\'jaobod', manzil: 'Katta yo\'l yoqasida', narx_usd: 200, xonalar_soni: 2, premium: false, egasi_verified: false, rasmlar: ['https://images.unsplash.com/photo-1493809842364-78817add7ffb?q=80&w=2070&auto=format&fit=crop'], maydon: 60, qavat: '2/2', wifi: false, type: 'family' },
  { id: '108', viloyat: 'Andijon', tuman: 'Andijon shahar', manzil: 'Eski shahar, milliy uslubda', narx_usd: 280, xonalar_soni: 3, premium: true, egasi_verified: true, rasmlar: ['https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?q=80&w=2070&auto=format&fit=crop'], maydon: 85, qavat: '1/2', wifi: true, type: 'luxury' },
]

// ── DECORATIVE BACKGROUND COMPONENT (REDESIGNED) ─────────────────────────────
const SectionDecor = ({ count = 8 }) => {
  const icons = useMemo(() => {
    const iconPool = [Home, MapPin, Building, Key, Grid, Compass, Box, Ruler];
    return Array.from({ length: Math.min(count, 8) }).map((_, i) => ({
      id: i,
      Icon: iconPool[i % iconPool.length],
      size: Math.random() * 18 + 28,
      top: `${Math.random() * 70 + 15}%`,
      left: `${Math.random() * 70 + 15}%`,
      rotate: Math.random() * 45,
      opacity: Math.random() * 0.06 + 0.04
    }));
  }, [count]);

  const orbs = useMemo(() => [
    { id: 0, size: 320, top: '10%', left: '10%', color: 'rgba(245, 158, 11, 0.08)' },
    { id: 1, size: 260, top: '55%', left: '75%', color: 'rgba(59, 130, 246, 0.08)' }
  ], []);

  return (
    <div className="section-decor-layer" aria-hidden="true">
      {orbs.map(orb => (
        <div
          key={orb.id}
          className="ambient-orb"
          style={{
            position: 'absolute',
            width: orb.size,
            height: orb.size,
            top: orb.top,
            left: orb.left,
            background: orb.color,
            borderRadius: '50%',
            zIndex: 0,
            opacity: 0.9
          }}
        />
      ))}

      {icons.map((item) => (
        <div
          key={item.id}
          className="decor-icon-wrapper"
          style={{
            position: 'absolute',
            top: item.top,
            left: item.left,
            opacity: item.opacity,
            transform: `translate(-50%, -50%) rotate(${item.rotate}deg)`,
            zIndex: 1,
          }}
        >
          <item.Icon size={item.size} strokeWidth={1.2} />
        </div>
      ))}
    </div>
  );
};

// ── COMPONENT ────────────────────────────────────────────────────────────────
export function HomePremium() {
  const navigate  = useNavigate()
  const { t }     = useTranslation()
  const { role }  = useAuthStore()
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

  // Use DEMO data immediately for instant load and premium feel
  const listings = DEMO_LISTINGS
  const [activeFilter, setActiveFilter] = useState('featured')

  const displayListings = useMemo(() => {
    let src = listings;
    if (activeFilter === 'featured') src = listings.filter(l => l.premium)
    if (activeFilter === 'student') src = listings.filter(l => l.type === 'student')
    if (activeFilter === 'luxury') src = listings.filter(l => l.type === 'luxury')
    return src.slice(0, 8)
  }, [listings, activeFilter])

  return (
    <main className="home-premium">

      {/* ══════════════════════════════════════════════════════════════════
          HERO SECTION — Immersive full-viewport introduction
      ══════════════════════════════════════════════════════════════════ */}
      <section className="hero relative overflow-hidden">
        {/* Background image layer - static for performance */}
        <div className="hero-bg absolute inset-0 z-0" aria-hidden>
          <div className="absolute inset-0 z-10 bg-transparent" />
          
          {/* Static Mesh Gradients for performance */}
          <div 
            className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full opacity-40 bg-[#F59E0B]"
            style={{ pointerEvents: 'none' }}
          />
          <div 
            className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full opacity-30 bg-[#D97706]"
            style={{ pointerEvents: 'none' }}
          />
          
          <img
            src="/premium_dark_interior_hero_1777829975835.png"
            alt=""
            className="hero-bg-img opacity-50 mix-blend-luminosity"
          />
          <div className="hero-bg-overlay" />
        </div>

        {/* Hero content */}
        <div className="hero-content">
          <motion.div
            className="hero-inner"
            variants={stagger}
            initial="hidden"
            animate="visible"
          >
            {/* Trust badges row */}
            <motion.div className="trust-row" variants={fadeUp} custom={0}>
              {TRUST_BADGES.map(({ icon: Icon, label, key }) => (
                <span key={key} className="trust-badge">
                  <Icon size={13} />
                  {t(label)}
                </span>
              ))}
            </motion.div>

            {/* Main heading */}
            <motion.h1 className="hero-title" variants={fadeUp} custom={0.1}>
              {t('home.hero_title_prefix', 'Andijonda')}{' '}
              <span className="gradient-text">
                {t('home.hero_title_accent', 'kvartira toping')}
              </span>
            </motion.h1>

            {/* Subtitle */}
            <motion.p className="hero-subtitle" variants={fadeUp} custom={0.2}>
              {t('home.hero_subtitle', 'Talabalar, oilalar va yoshlar uchun ishonchli va qulay ijaralar — hech qanday komissiyasiz')}
            </motion.p>

            {/* ── SEARCH BAR ───────────────────────────────────────────── */}
            <motion.div 
              className="hero-search-wrap" 
              variants={fadeUp} 
              custom={0.35}
            >
              <HomeSearchBar />
            </motion.div>



            {/* ── QUICK STATS ──────────────────────────────────────────── */}
            <motion.div className="hero-stats" variants={fadeUp} custom={0.45}>
              {STATS.map(({ icon: Icon, value, label }) => (
                <div key={label} className="hero-stat">
                  <div className="stat-icon"><Icon size={18} /></div>
                  <div className="stat-body">
                    <strong>{value}</strong>
                    <span>{t(label)}</span>
                  </div>
                </div>
              ))}
            </motion.div>
          </motion.div>
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
        <SectionDecor count={15} />
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
              {[
                { key: 'all',      label: 'Barchasi' },
                { key: 'featured', label: 'TOP E\'lonlar' },
                { key: 'student',  label: 'Talabalar uchun' },
                { key: 'luxury',   label: 'Premium / Luxury' },
              ].map(({ key, label }) => (
                <button
                  key={key}
                  className={`pill ${activeFilter === key ? 'active' : ''}`}
                  onClick={() => setActiveFilter(key)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Grid */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeFilter}
              className="listings-grid"
              variants={stagger}
              initial="hidden"
              animate="visible"
              exit={{ opacity: 0, y: -8, transition: { duration: 0.22, ease: [0.4, 0, 1, 1] } }}
            >
              {displayListings.length > 0 ? (
                    displayListings.map(listing => (
                      <motion.div key={listing.id} variants={cardItem}>
                        <PremiumListingCard
                          id={listing.id}
                          image={listing.rasmlar?.[0] || '/placeholder-apartment.jpg'}
                          title={listing.manzil || `${listing.tuman || ''}, ${listing.viloyat || ''}`}
                          location={`${listing.tuman || ''}, ${listing.viloyat || ''}`}
                          price={listing.narx_usd}
                          rooms={listing.xonalar_soni}
                          isPremium={listing.premium}
                          isVerified={listing.egasi_verified}
                          onClick={() => navigate(`/listing/${listing.id}`)}
                        />
                      </motion.div>
                    ))
                  ) : (
                    <div className="empty-filter-state" style={{ gridColumn: '1 / -1', padding: '3rem', textAlign: 'center', color: 'var(--color-muted)' }}>
                      Bu bo'limda hozircha e'lonlar yo'q
                    </div>
                  )
              }
            </motion.div>
          </AnimatePresence>

          {/* View all CTA */}
          <motion.div
            className="section-cta"
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease: smoothEase }}
          >
            <button className="btn-outline" onClick={() => navigate('/search')}>
              {t('home.view_all', "Barcha e'lonlar")}
              <ChevronRight size={18} />
            </button>
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          POPULAR LOCATIONS
      ══════════════════════════════════════════════════════════════════ */}
      <section className="home-section locations-section">
        <SectionDecor count={12} />
        <div className="section-container">
          <div className="section-head centered">
            <p className="section-eyebrow" style={eyebrowStyle}><MapPin size={14} /> Eng ommabop hududlar</p>
            <h2 className="section-title" style={titleStyle}>Qayerda yashashni xohlaysiz?</h2>
            <p className="section-sub" style={subStyle}>Andijonning eng qaynoq va talabgor hududlaridagi takliflar</p>
          </div>

          <div className="locations-grid">
            {LOCATIONS.map((loc, i) => (
              <motion.div 
                key={loc.name} 
                className="location-card"
                initial={{ opacity: 0, y: 10, scale: 0.985 }}
                whileInView={{ opacity: 1, y: 0, scale: 1 }}
                viewport={{ once: true, margin: '-40px' }}
                transition={{ duration: 0.58, delay: i * 0.08, ease: smoothEase }}
                onClick={() => navigate(`/search?tuman=${loc.name}`)}
              >
                <img src={loc.img} alt={loc.name} className="loc-img" loading="lazy" />
                <div className="loc-overlay" />
                <div className="loc-content">
                  <h3>{loc.name}</h3>
                  <span>{loc.count}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          AI RECOMMENDATION SECTION
      ══════════════════════════════════════════════════════════════════ */}
      <section className="home-section ai-recommendation">
        <div className="section-container">
          <motion.div 
            className="ai-banner-card"
            initial={{ opacity: 0, y: 12, scale: 0.985 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.62, ease: smoothEase }}
          >
            <div className="ai-content">
              <div className="ai-badge"><Zap size={16} /> AI Tavsiya</div>
              <h2>O'zingizga mos uyni topishga qiynalyapsizmi?</h2>
              <p>Bizning sun'iy intellekt yordamchimiz sizning byudjetingiz, o'qish yoki ish joyingizga eng yaqin va qulay variantlarni 5 soniyada topib beradi.</p>
              <button className="btn-ai-solid" onClick={() => document.querySelector('.chat-toggle-btn')?.click()}>
                <Sparkles size={18} />
                AI yordamchidan so'rash
              </button>
            </div>
            <div className="ai-visual">
              {/* Decorative AI visual element */}
              <div className="glass-mockup">
                <div className="mockup-header"><div className="dots"></div></div>
                <div className="mockup-body">
                  <div className="chat-bubble user">"ADU yonidan 150$ gacha xona kerak"</div>
                  <div className="chat-bubble ai">"Tushundim! ADU ga 5 minutlik piyoda masofada 3 ta ajoyib variant topdim..."</div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          HOW IT WORKS
      ══════════════════════════════════════════════════════════════════ */}
      <section className="home-section how-section">
        <SectionDecor count={10} />
        <div className="section-container">
          <div className="section-head centered">
            <p className="section-eyebrow" style={eyebrowStyle}><Clock size={14} /> {t('home.how_label', 'Qanday ishlaydi')}</p>
            <h2 className="section-title" style={titleStyle}>{t('home.how_title', '3 oddiy qadam')}</h2>
            <p className="section-sub" style={subStyle}>{t('home.how_subtitle', "Kvartira topish hech qachon bu qadar oson bo'lmagan")}</p>
          </div>

          <motion.div
            className="how-grid"
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-40px' }}
          >
            {HOW_STEPS.map(step => (
              <motion.div key={step.num} className="how-card" variants={cardItem}>
                <div className="how-num">{step.num}</div>
                <div className="how-emoji">{step.emoji}</div>
                <h3>{t(step.title)}</h3>
                <p>{t(step.desc)}</p>
              </motion.div>
            ))}
          </motion.div>
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

          <motion.div
            className="advantages-grid"
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-40px' }}
          >
            {ADVANTAGES.map((adv) => {
              const Icon = adv.icon
              return (
                <motion.div key={adv.title} className="advantage-card" variants={cardItem}>
                  <div className="adv-icon-wrapper">
                    <Icon size={24} />
                  </div>
                  <h3>{adv.title}</h3>
                  <p>{adv.desc}</p>
                </motion.div>
              )
            })}
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          TESTIMONIALS
      ══════════════════════════════════════════════════════════════════ */}
      <section className="home-section testimonials-section">
        <div className="section-container">
          <div className="section-head centered">
            <p className="section-eyebrow" style={eyebrowStyle}><Star size={14} /> {t('home.testimonials_label', 'Fikrlar')}</p>
            <h2 className="section-title" style={titleStyle}>{t('home.testimonials_title', 'Foydalanuvchilar nima deydi')}</h2>
          </div>

          <motion.div
            className="testimonials-grid"
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            {TESTIMONIALS.map(t_ => (
              <motion.div key={t_.name} className="testimonial-card" variants={cardItem}>
                <div className="t-stars">{'⭐'.repeat(t_.rating)}</div>
                <p className="t-quote">"{t(t_.quote)}"</p>
                <div className="t-author">
                  <span className="t-avatar">{t_.avatar}</span>
                  <div>
                    <strong>{t_.name}</strong>
                    <span>{t(t_.role)}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════════════════
          OWNER CTA
      ══════════════════════════════════════════════════════════════════ */}
      <section className="home-section owner-cta-section">
        <div className="section-container">
          <motion.div
            className="owner-cta-card"
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.62, ease: smoothEase }}
          >
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
                onClick={() => navigate(role ? (role === 'makler' ? '/makler/create' : '/owner/create') : '/register')}
              >
                {role ? t('home.owner_cta_btn_logged', "E'lon joylash") : t('home.owner_cta_btn', 'Hozir boshlash')}
                <ArrowRight size={18} />
              </button>
            </div>
          </motion.div>
        </div>
      </section>

    </main>
  )
}
