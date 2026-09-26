import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { AnimatePresence, motion } from 'framer-motion'
import {
  BadgeCheck,
  Building2,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ChefHat,
  Droplets,
  Eye,
  Flame,
  Heart,
  Home,
  MapPin,
  Maximize2,
  MessageCircle,
  Refrigerator,
  ShieldCheck,
  Share2,
  Snowflake,
  Sparkles,
  Star,
  Tv,
  Users,
  WashingMachine,
  Wifi,
  X,
} from 'lucide-react'
import { createBooking, createRentalRequest, getListingById } from '../../../services/listingService'
import { favoritesService } from '../../../services/favoritesService'
import { useAuthStore } from '../../../store/authStore'
import { ListingMap } from '../../../components/listing/ListingMap'
import { ReviewSection } from '../../../components/listing/ReviewSection'
import { RoommateAdForm, RoommateAdInfo } from '../../../components/listing/RoommateAd'
import { ListingDetailSkeleton } from '../../../components/ui/ListingDetailSkeleton.jsx'
import './Listing.scss'

const FALLBACK_IMG = 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1400&q=82'
const spring = { type: 'spring', stiffness: 360, damping: 34, mass: 0.8 }

export function Listing() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { accessToken, role, userId } = useAuthStore()
  const [listing, setListing] = useState(null)
  const [activeImage, setActiveImage] = useState(0)
  const [saved, setSaved] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [requestMessage, setRequestMessage] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [requestStatus, setRequestStatus] = useState('')
  const [requestLoading, setRequestLoading] = useState(false)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    setLoading(true)
    setError(null)
    setListing(null)
    setActiveImage(0)
    void getListingById(id)
      .then((data) => { if (cancelled) return; setListing(data) })
      .catch((err) => { if (cancelled) return; const status = err?.response?.status; setError(status === 404 || status === 422 ? 'not_found' : 'load_failed') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [id])

  useEffect(() => {
    if (!id || !accessToken) { setSaved(false); return }
    let active = true
    void favoritesService.getMyFavorites()
      .then((items) => { if (active) setSaved(Array.isArray(items) && items.some((item) => String(item.id) === String(id))) })
      .catch(() => { if (active) setSaved(false) })
    return () => { active = false }
  }, [accessToken, id])

  useEffect(() => {
    if (!previewOpen) return undefined
    const handleKeyDown = (event) => { if (event.key === 'Escape') setPreviewOpen(false) }
    document.body.classList.add('listing-preview-lock')
    window.addEventListener('keydown', handleKeyDown)
    return () => { document.body.classList.remove('listing-preview-lock'); window.removeEventListener('keydown', handleKeyDown) }
  }, [previewOpen])

  const images = useMemo(() => {
    const gallery = listing?.images?.length ? listing.images : [FALLBACK_IMG]
    return gallery
  }, [listing])

  const amenityRows = useMemo(() => ([
    ['wifi', 'WiFi', <Wifi size={19} />],
    ['gas', t('search.gas'), <Flame size={19} />],
    ['water', t('search.water'), <Droplets size={19} />],
    ['fridge', t('search.fridge'), <Refrigerator size={19} />],
    ['kitchenware', t('search.kitchen'), <ChefHat size={19} />],
    ['ac', t('search.ac'), <Snowflake size={19} />],
    ['tv', t('search.tv'), <Tv size={19} />],
    ['washer', t('search.washer'), <WashingMachine size={19} />],
  ]), [t])

  if (loading) return <ListingDetailSkeleton />

  if (error || !listing) {
    return (
      <main className="listing-page listing-error-page">
        <section className="listing-error-card">
          <span className="listing-error-icon"><Home size={28} /></span>
          <span className="eyebrow">{t('listing.not_found_label', 'Listing')}</span>
          <h1>{t('listing.not_found_title', 'E\u2019lon topilmadi')}</h1>
          <p>
            {error === 'not_found'
              ? t('listing.not_found_desc', 'Bu e\u2019lon o\u2018chirilgan, aktiv emas yoki havola eskirgan bo\u2018lishi mumkin.')
              : t('listing.load_failed_desc', 'E\u2019lonni yuklashda xatolik bo\u2018ldi. Backend ishga tushganini tekshiring.')}
          </p>
          <div className="listing-error-actions">
            <Link to="/search" className="booking-primary">{t('home.view_all', "Barcha e'lonlar")}</Link>
            <Link to="/" className="booking-secondary">{t('auth.btn_home', 'Bosh sahifa')}</Link>
          </div>
        </section>
      </main>
    )
  }

  const isSharedRoom = listing.rooms_count === 1
  const activeSrc = images[activeImage] || FALLBACK_IMG
  const rating = typeof listing.rating === 'number' ? listing.rating.toFixed(1) : t('listing.new')
  const title = listing.address || `${listing.rooms_count} ${t('listing.rooms_count')} uy`
  const fullAddress = `${listing.district}, ${listing.region}`
  const similarListings = images.slice(0, 3).map((src, index) => ({
    src,
    title: index === 0 ? t('listing.premium_residence') : index === 1 ? t('listing.modern_apartment') : t('listing.student_friendly_home'),
    meta: `${listing.district}, ${listing.region}`,
    price: Math.max(Number(listing.price || 0) - index * 35, 0),
  }))

  const today = new Date().toISOString().slice(0, 10)

  const nextImage = () => setActiveImage((v) => (v + 1) % images.length)
  const prevImage = () => setActiveImage((v) => (v - 1 + images.length) % images.length)
  const handleGalleryNav = (event, action) => { event.stopPropagation(); action() }

  const handleBookingRequest = async () => {
    if (!accessToken) { setRequestStatus("Avval tizimga kiring, keyin band qilish so'rovini yuborasiz."); return }
    if (!startDate || !endDate) { setRequestStatus("Kirish va chiqish sanalarini tanlang."); return }
    try {
      setRequestLoading(true); setRequestStatus('')
      await createBooking({ listingId: listing.id, startDate, endDate, message: requestMessage })
      setRequestStatus("So'rov yuborildi. Egasi yoki broker dashboardida ko'radi.")
      setRequestMessage('')
    } catch (err) {
      setRequestStatus(err.response?.data?.detail || "So'rov yuborishda xatolik bo'ldi.")
    } finally { setRequestLoading(false) }
  }

  const handleSave = async () => {
    if (!accessToken) { navigate('/login'); return }
    const previous = saved; setSaved(!previous)
    try { const result = await favoritesService.toggleFavorite(listing.id); setSaved(result.status === 'added') }
    catch (err) { setSaved(previous); setRequestStatus(err.response?.data?.detail || "Saqlashda xatolik bo'ldi.") }
  }

  const handleTelegramContact = async () => {
    if (ownerTelegramLink) { window.location.assign(ownerTelegramLink); return }
    if (!accessToken) { navigate('/login'); return }
    try {
      setRequestLoading(true)
      const request = await createRentalRequest({ listing_id: listing.id, message: requestMessage || `Salom, ${title} bo'yicha Telegram o'rniga shu chatda bog'lanmoqchiman.` })
      navigate(`/messages?request=${request.id}`)
    } catch (err) {
      setRequestStatus(err.response?.data?.detail || "Chat ochishda xatolik bo'ldi.")
    } finally { setRequestLoading(false) }
  }

  // Tenants (not the apartment's owner) can look for roommates for an apartment on the platform.
  const canPostRoommateAd =
    Boolean(accessToken) && ['student', 'makler'].includes(role) && !listing.parent_listing_id && String(listing.owner_id) !== String(userId)
  const ownerPhoneLink = listing.owner_phone ? `tel:${String(listing.owner_phone).replace(/\s/g, '')}` : null
  const ownerTelegramId = Number(listing.owner_telegram_id)
  const hasLikelyTelegramId = Number.isFinite(ownerTelegramId) && ownerTelegramId >= 10000 && ownerTelegramId < 10000000000
  const ownerTelegramLink = listing.owner_telegram_url || (hasLikelyTelegramId ? `tg://user?id=${ownerTelegramId}` : null)

  return (
    <main className="listing-page">

      {/*
       * ═══════════════════════════════════════════════════════════════════
       *  OUTER 2-COL LAYOUT
       *  Left  (.listing-left)  — gallery (main + 2 thumbs) + detail panels
       *  Right (.right-col)     — booking card, position:sticky
       *  Both inside .listing-two-col  →  sticky stops when this div ends.
       *  O'xshash e'lonlar is OUTSIDE this wrapper → sticky releases there.
       * ═══════════════════════════════════════════════════════════════════
       */}
      <div className="listing-two-col">

        {/* ───── LEFT COLUMN ───── */}
        <div className="listing-left">

          {/* Gallery: main image + 2 thumbnails */}
          <section className="listing-hero-shell">
            <motion.div
              className="listing-gallery"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            >
              {/* Main image */}
              <div className="gallery-main">
                <button
                  type="button"
                  className="gallery-image-button"
                  onClick={() => setPreviewOpen(true)}
                  aria-label={t('listing.open_gallery')}
                >
                  <span className="gallery-image-backdrop" style={{ backgroundImage: `url(${activeSrc})` }} />
                  <AnimatePresence mode="wait">
                    <motion.img
                      key={activeSrc}
                      src={activeSrc}
                      alt={listing.address || 'Listing'}
                      initial={{ opacity: 0, scale: 1.03 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
                      onError={(e) => { e.currentTarget.src = FALLBACK_IMG }}
                    />
                  </AnimatePresence>
                  <span className="image-open-hint">
                    <Maximize2 size={14} />
                    {t('listing.view')}
                  </span>
                </button>

                <div className="gallery-gradient" />

                <div className="gallery-topbar">
                  <div className="hero-chips">
                    {listing.is_premium && (
                      <span className="hero-chip premium"><Sparkles size={13} /> {t('listing.premium')}</span>
                    )}
                    <span className="hero-chip"><Star size={13} fill="currentColor" /> {rating}</span>
                    <span className="hero-chip">{t('listing.new')}</span>
                  </div>
                  <div className="hero-actions">
                    <button type="button" aria-label={t('listing.share')}><Share2 size={16} /></button>
                    <button type="button" onClick={handleSave} className={saved ? 'saved' : ''}>
                      <Heart size={16} fill={saved ? 'currentColor' : 'none'} />
                    </button>
                    <button type="button" onClick={() => setPreviewOpen(true)}><Maximize2 size={16} /></button>
                  </div>
                </div>

                {images.length > 1 && (
                  <>
                    <button className="listing-gallery-arrow listing-gallery-arrow--prev" type="button"
                      onClick={(e) => handleGalleryNav(e, prevImage)} aria-label={t('listing.previous_image')}>
                      <ChevronLeft size={22} />
                    </button>
                    <button className="listing-gallery-arrow listing-gallery-arrow--next" type="button"
                      onClick={(e) => handleGalleryNav(e, nextImage)} aria-label={t('listing.next_image')}>
                      <ChevronRight size={22} />
                    </button>
                  </>
                )}

                <div className="hero-copy">
                  <span className="location-kicker"><MapPin size={14} /> {fullAddress}</span>
                  <h1>{title}</h1>
                  <p>
                    {listing.building_number ? `${t('listing.dom')} ${listing.building_number}` : t('listing.street')}
                    {listing.room_number ? `, ${t('listing.room')} ${listing.room_number}` : ''}
                  </p>
                </div>
              </div>

              {/* 2 thumbnails — right of main image, inside the same gallery box */}
              <div className="gallery-thumbs">
                {images.slice(0, 2).map((src, index) => (
                  <motion.button
                    key={`${src}-${index}`}
                    type="button"
                    className={activeImage === index ? 'active' : ''}
                    onClick={(e) => { e.stopPropagation(); setActiveImage(index) }}
                    whileHover={{ y: -3 }}
                    whileTap={{ scale: 0.96 }}
                    transition={spring}
                  >
                    <img src={src} alt={`${index + 1}`} onError={(e) => { e.currentTarget.src = FALLBACK_IMG }} />
                  </motion.button>
                ))}
              </div>
            </motion.div>
          </section>

          {/* ── Detail panels (scrollable) ── */}
          <div className="left-col">

            {/* Overview: xona, qavat, maydon, ko'rishlar */}
            <motion.section className="overview-panel" initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={spring}>
              <div className="overview-metrics">
                <span><Home size={20} /> <strong>{listing.rooms_count}</strong><small>{t('listing.rooms_count')}</small></span>
                <span><Users size={20} /> <strong>{listing.available_spaces ?? '-'}</strong><small>{t('listing.free_spots')}</small></span>
                <span><Building2 size={20} /> <strong>{listing.floor ?? '-'}/{listing.total_floors ?? '-'}</strong><small>{t('listing.floor')}</small></span>
                <span><Eye size={20} /> <strong>{listing.views_count ?? 0}</strong><small>{t('listing.views')}</small></span>
              </div>
              <div className="address-card">
                <MapPin size={20} />
                <div>
                  <strong>{fullAddress}</strong>
                  <p>{t('listing.street')}: {listing.address ?? '-'} {listing.area_m2 ? `, ${listing.area_m2} m2` : ''}</p>
                </div>
              </div>
              {isSharedRoom && (
                <div className="shared-note">
                  <Users size={18} />
                  <span>{t('listing.free_spots')}: {listing.available_spaces} / {listing.max_guests} {t('listing.people')}</span>
                </div>
              )}
            </motion.section>

            {listing.parent_listing_id && <RoommateAdInfo listing={listing} />}
            {canPostRoommateAd && <RoommateAdForm apartmentId={listing.id} />}

            {/* Description */}
            <motion.section className="desc panel-card" initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={spring}>
              <div className="section-heading">
                <span>{t('listing.overview')}</span>
                <h2>{t('listing.description')}</h2>
              </div>
              <p>{listing.description ?? t('listing.no_description')}</p>
            </motion.section>

            {/* Amenities */}
            <motion.section className="amenities-panel panel-card" initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={spring}>
              <div className="section-heading">
                <span>{t('listing.comfort')}</span>
                <h2>{t('listing.amenities') || t('search.amenities')}</h2>
              </div>
              <div className="amenities-grid">
                {amenityRows.map(([key, label, icon]) => {
                  const active = Boolean(listing.amenities?.[key])
                  return (
                    <div key={key} className={`amenity-tile ${active ? 'active' : 'muted'}`}>
                      <span>{icon}</span>
                      <strong>{label}</strong>
                      <small>{active ? t('listing.included') : t('listing.not_listed')}</small>
                    </div>
                  )
                })}
              </div>
            </motion.section>

            {/* Map */}
            <motion.section className="location-section panel-card" initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={spring}>
              <div className="section-heading">
                <span>{t('listing.location')}</span>
                <h2>{t('listing.location')}</h2>
              </div>
              <ListingMap lat={listing.latitude} lng={listing.longitude} address={listing.address} />
            </motion.section>

            {/* Reviews */}
            <ReviewSection listingId={listing.id} />

          </div>{/* /left-col */}
        </div>{/* /listing-left */}

        {/* ───── RIGHT COLUMN: sticky booking card ───── */}
        <aside className="right-col">
          <motion.div
            className="booking-card sticky-booking"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
          >
            <div className="booking-price">
              <span>${listing.price}</span>
              <small>/ {t('listing.per_month')}</small>
            </div>

            <div className="booking-host">
              <span className="host-avatar">{listing.owner_full_name?.charAt(0)?.toUpperCase() || 'A'}</span>
              <div>
                <strong>{listing.owner_full_name || t('listing.owner_label')}</strong>
                <small>{listing.owner_phone || (listing.source === 'makler' ? t('listing.makler_verified') : t('listing.owner_label'))}</small>
              </div>
              <BadgeCheck size={19} />
            </div>

            <div className="booking-mini-stats">
              <span><Star size={15} fill="currentColor" /> {rating}</span>
              <span><Eye size={15} /> {listing.views_count ?? 0}</span>
              <span><ShieldCheck size={15} /> {t('listing.verified')}</span>
            </div>

            <div className="booking-details">
              <span><CalendarDays size={17} /> {t('listing.first_month')}: ${listing.price}</span>
              <span><ShieldCheck size={17} /> {listing.source === 'makler' ? t('listing.makler_notice') : t('listing.owner_notice')}</span>
            </div>

            {(!role || role === 'student') && (
              <>
                <div className="booking-dates">
                  <label>
                    Kirish
                    <input type="date" value={startDate} min={today} onChange={(e) => setStartDate(e.target.value)} />
                  </label>
                  <label>
                    Chiqish
                    <input type="date" value={endDate} min={startDate || today} onChange={(e) => setEndDate(e.target.value)} />
                  </label>
                </div>
                <textarea
                  className="booking-request-text"
                  value={requestMessage}
                  onChange={(e) => setRequestMessage(e.target.value)}
                  placeholder="Egasi yoki brokerga qisqa xabar..."
                  rows={3}
                />
                <button className="booking-primary" type="button" onClick={handleBookingRequest} disabled={requestLoading}>
                  <MessageCircle size={18} />
                  {requestLoading ? 'Yuborilmoqda...' : "Band qilish so'rovi"}
                </button>
                {requestStatus && <p className="booking-request-status">{requestStatus}</p>}
              </>
            )}
            <button className="booking-secondary" type="button"
              onClick={() => ownerPhoneLink && window.location.assign(ownerPhoneLink)}
              disabled={!ownerPhoneLink}>
              {t('listing.contact')}
            </button>
            <button className="booking-secondary" type="button"
              onClick={handleTelegramContact}
              disabled={requestLoading}>
              {t('listing.telegram')}
            </button>
          </motion.div>
        </aside>

      </div>{/* /listing-two-col  ← sticky releases here */}

      {/* ══ O'xshash e'lonlar — 100% kenglik, sticky shu yerda to'xtaydi ══ */}
      <motion.section
        className="similar-section similar-section--full"
        initial={{ opacity: 0, y: 18 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={spring}
      >
        <div className="section-heading">
          <span>{t('listing.explore')}</span>
          <h2>{t('listing.similar_listings')}</h2>
        </div>
        <div className="similar-grid">
          {similarListings.map((item, index) => (
            <article className="similar-card" key={`${item.src}-${index}`}>
              <img src={item.src} alt={item.title} />
              <div>
                <strong>{item.title}</strong>
                <small>{item.meta}</small>
                <span>${item.price} / oy</span>
              </div>
            </article>
          ))}
        </div>
      </motion.section>

      {/* Fullscreen gallery preview */}
      <AnimatePresence>
        {previewOpen && (
          <motion.div
            className="fullscreen-gallery"
            role="dialog"
            aria-modal="true"
            aria-label={t('listing.fullscreen_preview')}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setPreviewOpen(false)}
          >
            <div className="preview-toolbar">
              <button className="preview-back" type="button" onClick={() => setPreviewOpen(false)}>
                <ChevronLeft size={19} />
                Orqaga
              </button>
              <span>{activeImage + 1} / {images.length}</span>
              <button className="preview-close" type="button" onClick={() => setPreviewOpen(false)} aria-label={t('listing.close_preview')}>
                <X size={21} />
              </button>
            </div>
            {images.length > 1 && (
              <button className="preview-nav left" type="button" onClick={(e) => { e.stopPropagation(); prevImage() }}>
                <ChevronLeft size={28} />
              </button>
            )}
            <motion.img
              key={`preview-${activeSrc}`}
              src={activeSrc}
              alt={t('listing.preview_alt')}
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.35 }}
              onClick={(e) => e.stopPropagation()}
            />
            {images.length > 1 && (
              <button className="preview-nav right" type="button" onClick={(e) => { e.stopPropagation(); nextImage() }}>
                <ChevronRight size={28} />
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

    </main>
  )
}
