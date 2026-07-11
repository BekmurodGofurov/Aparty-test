/**
 * adaptListing — Backend (English) → Frontend (Uzbek) field adapter.
 *
 * Backend schemas (ListingCard, ListingOut) use English snake_case field names.
 * All frontend components (ListingCard.jsx, Listing.jsx) use Uzbek names.
 * This single function is the bridge between them.
 *
 * Usage:
 *   import { adaptListing } from '../../utils/adaptListing'
 *   const listing = adaptListing(rawBackendData)
 */
export const adaptListing = (l) => {
  if (!l) return null

  const GENDER_MAP = { male: 'erkak', female: 'ayol', mixed: 'aralash' }

  return {
    // ── identity ─────────────────────────────────────────────────
    id: l.id,

    // ── location ─────────────────────────────────────────────────
    viloyat:    l.region,
    tuman:      l.district,
    manzil:     l.address,
    dom_raqami: l.building_number,
    xona_raqami: l.room_number,

    // coordinates (same names — backend also uses latitude/longitude)
    latitude:   l.latitude,
    longitude:  l.longitude,

    // ── pricing ───────────────────────────────────────────────────
    narx_usd: l.price_usd,

    // ── room details ──────────────────────────────────────────────
    xonalar_soni: l.rooms_count,
    maydon_m2:    l.area_m2,
    qavat:        l.floor,
    jami_qavat:   l.total_floors,
    bosh_joy:     l.available_spaces,
    max_kishi:    l.max_guests,

    // ── gender ────────────────────────────────────────────────────
    jins: GENDER_MAP[l.target_gender] ?? l.target_gender,

    // ── amenities & media ─────────────────────────────────────────
    qulayliklar: l.amenities ?? {},
    rasmlar:     l.images ?? [],
    tavsif:      l.description,

    // ── premium / status ──────────────────────────────────────────
    premium:            l.is_premium,
    premium_expires_at: l.premium_expires_at,
    is_active:          l.is_active,
    korishlar:          l.views_count ?? 0,
    manba:              l.source,  // 'owner' | 'makler'

    // ── owner info ────────────────────────────────────────────────
    egasi_id:          l.owner_id,
    egasi_ism:         l.owner_full_name,
    egasi_telefon:     l.owner_phone,
    egasi_turi:        l.owner_role,       // 'owner' | 'makler' | 'student'
    egasi_verified:    l.owner_verified,
    egasi_telegram_id: l.owner_telegram_id  ?? null,
    egasi_telegram_url: l.owner_telegram_url ?? null,

    // ── ratings ───────────────────────────────────────────────────
    reyting:      l.rating ?? null,
    sharhlar_soni: l.reviews_count ?? 0,

    // ── timestamps ────────────────────────────────────────────────
    created_at: l.created_at,
  }
}
