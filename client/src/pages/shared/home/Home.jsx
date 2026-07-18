import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { searchListings } from '../../../services/listingService'
import { HomeSearchBar } from '../../../components/search/HomeSearchBar'
import ListingCard from '../../../components/ListingCard/ListingCard.jsx'
import './Home.scss'

const TRUST_BADGES = [
  { icon: '✅', label: 'Tekshirilgan e\'lonlar' },
  { icon: '🚫', label: 'Yashirin to\'lovsiz' },
  { icon: '🎓', label: 'Talabalar uchun' },
]

const HOW_STEPS = [
  { num: '01', icon: '🔍', title: 'Qidiring',      desc: 'Shahar, narx va xona soni bo\'yicha filtrlang' },
  { num: '02', icon: '📞', title: 'Bog\'laning',   desc: 'Egasi yoki makler bilan to\'g\'ridan-to\'g\'ri' },
  { num: '03', icon: '🏠', title: 'Ko\'chib kiring', desc: 'Kelishib, shartnoma tuzing va ko\'ching' },
]

const ROLE_CARDS = [
  { icon: '🎓', role: 'Talaba',   desc: 'Tez va arzon uy toping', color: '#168BFF' },
  { icon: '🏘️', role: 'Uy egasi', desc: 'E\'lon bering — bepul',  color: '#10B981' },
  { icon: '📋', role: 'Makler',   desc: 'Premium reja bilan ko\'proq mijoz', color: '#F59E0B' },
]

export function Home() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [listings, setListings] = useState([])
  const [quick, setQuick] = useState({ viloyat: '', tuman: '', narx_min: '', narx_max: '', xonalar_soni: '' })

  useEffect(() => {
    void searchListings({}, 1, 9).then((data) => setListings(data.listings))
  }, [])

  const premium = useMemo(() => listings.filter((item) => item.premium).slice(0, 4), [listings])
  const recent  = useMemo(() => listings.slice(0, 6), [listings])

  const handleSearch = (event) => {
    event.preventDefault()
    const params = new URLSearchParams(
      Object.entries(quick).filter(([, v]) => v).map(([k, v]) => [k, String(v)]),
    )
    navigate(`/search?${params.toString()}`)
  }

  return (
    <main className="home-page">

      {/* ── HERO ──────────────────────────────── */}
      <section className="hero">
        <div className="hero-content page">
          <div className="hero-left">
            {/* Trust badges */}
            <div className="trust-badges anim-fade-in-up">
              {TRUST_BADGES.map((b) => (
                <span key={b.label} className="trust-badge">
                  <span>{b.icon}</span> {b.label}
                </span>
              ))}
            </div>

            <h1 className="hero-title anim-fade-in-up anim-delay-1">
              {t('home.hero_title')}
            </h1>
            <p className="hero-sub anim-fade-in-up anim-delay-2">
              {t('home.hero_subtitle')}
            </p>

            {/* ── SEARCH BAR ───────────────────────── */}
            <div className="anim-fade-in-up anim-delay-3" style={{ marginTop: '2rem', width: '100%', maxWidth: '1000px' }}>
              <HomeSearchBar />
            </div>



            {/* Open AI Chat Button */}
            <div className="anim-fade-in-up anim-delay-4" style={{ marginTop: '3rem' }}>
              <button 
                className="button-primary" 
                style={{ padding: '1rem 2rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', borderRadius: '999px', background: 'linear-gradient(135deg, #0EA5E9, #8B5CF6)' }}
                onClick={() => document.querySelector('.chat-toggle-btn')?.click()}
              >
                <span style={{ fontSize: '1.4rem' }}>✨</span> AI Yordamchi bilan suhbat
              </button>
            </div>
          </div>

          {/* Right side stats float */}
          <div className="hero-right anim-fade-in-up anim-delay-2">
            <div className="stat-float stat-float--1">
              <span className="stat-number">1,240+</span>
              <span className="stat-label">Faol e'lonlar</span>
            </div>
            <div className="stat-float stat-float--2">
              <span className="stat-icon">⭐</span>
              <span className="stat-number">4.8</span>
              <span className="stat-label">Reyting</span>
            </div>
            <div className="stat-float stat-float--3">
              <span className="stat-icon">🔒</span>
              <span className="stat-label">Tekshirilgan maklerlar</span>
            </div>
            <div className="hero-glow" />
          </div>
        </div>
      </section>

      {/* ── PREMIUM LISTINGS ──────────────────── */}
      <section className="home-section page">
        <div className="section-top">
          <div>
            <p className="section-label">Premium e'lonlar</p>
            <h2 className="section-title">{t('home.premium_title')}</h2>
          </div>
          <Link to="/search" className="see-all">{t('home.view_all')} →</Link>
        </div>
        <div className="horizontal-cards">
          {premium.length > 0
            ? premium.map((item) => <ListingCard key={item.id} listing={item} />)
            : <div className="empty-section-hint">E'lonlar yuklanmoqda...</div>
          }
        </div>
      </section>

      {/* ── TALABALAR UCHUN MAXSUS ──────────────── */}
      <section className="student-section page">
        <div className="student-content glass-card" style={{ '--role-color': '#9333ea' }}>
          <div className="student-text">
            <span className="badge-purple">🎓 Student Mode</span>
            <h2>Talabalar uchun maxsus</h2>
            <p>Universitetingizga yaqin, arzon va qulay yotoqxona yoki ijaraga xonalarni osongina toping. Komissiyasiz va ishonchli variantlar.</p>
            <ul className="student-perks">
              <li><span>✅</span> OTMlarga yaqinlik</li>
              <li><span>✅</span> Arzon narxlar</li>
              <li><span>✅</span> Sherik topish imkoniyati</li>
            </ul>
            <Link to="/search?student=true" className="button-primary mt-4">
              Talabalar e'lonlarini ko'rish →
            </Link>
          </div>
          <div className="student-image">
            {/* Placeholder for an image or illustration */}
            <div className="image-placeholder">
              <span className="text-6xl">🏫</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── ROOMMATE TOPISH ───────────────────── */}
      <section className="roommate-section page">
         <div className="section-top">
          <div>
            <p className="section-label">Yangi funksiya</p>
            <h2 className="section-title">O'zingizga mos Roommate toping</h2>
          </div>
        </div>
        <div className="roommate-grid">
          <div className="roommate-card glass-card">
            <div className="rm-avatar">👦🏻</div>
            <div className="rm-info">
              <h3>Azizbek, 20 yosh</h3>
              <p>ADU talabasi • 150$ byudjet</p>
              <div className="match-score">Match: 95%</div>
            </div>
          </div>
          <div className="roommate-card glass-card">
            <div className="rm-avatar">👨🏻‍💻</div>
            <div className="rm-info">
              <h3>Sardor, 24 yosh</h3>
              <p>Dasturchi • 250$ byudjet</p>
              <div className="match-score">Match: 88%</div>
            </div>
          </div>
          <div className="roommate-card glass-card empty-rm-card">
             <div className="rm-info text-center">
              <h3>Siz ham sherik qidiryapsizmi?</h3>
              <Link to="/roommate" className="role-cta mt-2">Profil yaratish →</Link>
             </div>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS (AI VERSION) ─────────── */}
      <section className="how-section page">
        <p className="section-label">Aparty.uz qanday ishlaydi?</p>
        <h2 className="section-title" style={{ marginBottom: '2.5rem' }}>Zamonaviy va ishonchli tizim</h2>
        <div className="how-grid">
          {HOW_STEPS.map((step) => (
            <div key={step.num} className="how-card glass-card">
              <span className="how-num">{step.num}</span>
              <span className="how-icon">{step.icon}</span>
              <h3>{step.title}</h3>
              <p>{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── ROLE CARDS ────────────────────────── */}
      <section className="roles-section page">
        <p className="section-label">Kim uchun?</p>
        <h2 className="section-title" style={{ marginBottom: '2rem' }}>Har bir foydalanuvchi uchun</h2>
        <div className="roles-grid">
          {ROLE_CARDS.map((r) => (
            <div key={r.role} className="role-card glass-card" style={{ '--role-color': r.color }}>
              <span className="role-icon">{r.icon}</span>
              <h3>{r.role}</h3>
              <p>{r.desc}</p>
              <Link to="/register" className="role-cta">Boshlash →</Link>
            </div>
          ))}
        </div>
      </section>

      {/* ── STATS BAR ─────────────────────────── */}
      <section className="stats-bar page">
        <div className="stats-inner">
          <div className="stat-item">
            <strong>1,240</strong>
            <span>{t('home.stats_listings')}</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <strong>830</strong>
            <span>{t('home.stats_students')}</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <strong>240</strong>
            <span>{t('home.stats_maklers')}</span>
          </div>
        </div>
      </section>

    </main>
  )
}
