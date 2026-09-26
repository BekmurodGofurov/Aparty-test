import { DEFAULT_ANDIJAN_LOCATION, getDistanceKm } from '../utils/geo'
import { api } from './api'

const MAP_LISTING_LIMIT = 100
const FALLBACK_IMAGE = 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=900&q=80'

const toBadgeList = (listing) => {
  const badges = []
  if (listing.is_premium) badges.push('Premium')
  if (listing.owner_verified) badges.push('Verified')
  if ((listing.reviews_count || 0) > 0) badges.push('Top rated')
  return badges.length ? badges : ['Active']
}

const normalizeListing = (listing, userLocation) => {
  const lat = Number(listing.latitude)
  const lng = Number(listing.longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null

  const images = Array.isArray(listing.images) && listing.images.length
    ? listing.images
    : [FALLBACK_IMAGE]
  const address = [listing.address, listing.district, listing.region].filter(Boolean).join(', ')
  const rooms = Number(listing.rooms_count || 1)

  return {
    id: listing.id,
    title: listing.address || `${listing.district || 'Andijon'}dagi ${rooms} xonali uy`,
    price: Number(listing.price || 0),
    currency: '$',
    rooms,
    area: Number(listing.area_m2 || 0) || Math.max(28, rooms * 22),
    floor: listing.floor ?? 1,
    rating: listing.rating || 4.8,
    views: Number(listing.views_count || 0),
    phone: listing.owner_phone || '',
    badges: toBadgeList(listing),
    description: listing.description || "Qulay joylashuv, tekshirilgan e'lon va tezkor aloqa imkoniyati.",
    lat,
    lng,
    address,
    image: images[0],
    images,
    distanceKm: getDistanceKm(userLocation, { lat, lng }),
  }
}

export async function fetchMapProperties({ userLocation = DEFAULT_ANDIJAN_LOCATION, filters } = {}) {
  const { data } = await api.get('/listings/search', {
    params: {
      page: 1,
      limit: MAP_LISTING_LIMIT,
      ...(filters || {}),
    },
  })

  const listings = Array.isArray(data?.listings) ? data.listings : []

  return listings
    .map(listing => normalizeListing(listing, userLocation))
    .filter(Boolean)
    .sort((a, b) => Number(b.badges.includes('Premium')) - Number(a.badges.includes('Premium')) || a.distanceKm - b.distanceKm)
}

export const mapPropertyApi = {
  fetchNearby: fetchMapProperties,
}
