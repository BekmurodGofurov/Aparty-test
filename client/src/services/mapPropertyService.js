import { DEFAULT_ANDIJAN_LOCATION, getDistanceKm } from '../utils/geo'
import { api } from './api'
import { PLACEHOLDER_IMAGE } from '../utils/images'

export const MAP_LISTING_LIMIT = 100

const toBadgeList = (listing) => {
  const badges = []
  if (listing.is_premium) badges.push('Premium')
  if (listing.owner_verified) badges.push('Verified')
  return badges.length ? badges : ['Active']
}

const normalizeListing = (listing, userLocation) => {
  const lat = Number(listing.latitude)
  const lng = Number(listing.longitude)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null

  const images = Array.isArray(listing.images) && listing.images.length
    ? listing.images
    : [PLACEHOLDER_IMAGE]
  const address = [listing.address, listing.district, listing.region].filter(Boolean).join(', ')
  const rooms = Number(listing.rooms_count || 1)

  return {
    id: listing.id,
    title: listing.address || `${listing.district || 'Andijon'}dagi ${rooms} xonali uy`,
    price: Number(listing.price || 0),
    currency: '$',
    rooms,
    area: listing.area_m2 || null,
    floor: listing.floor ?? null,
    views: Number(listing.views_count || 0),
    phone: listing.owner_phone || '',
    badges: toBadgeList(listing),
    description: listing.description || '',
    lat,
    lng,
    address,
    image: images[0],
    images,
    distanceKm: getDistanceKm(userLocation, { lat, lng }),
  }
}

// Listings do not depend on where the user is, so they are fetched once and ranked locally.
export async function fetchMapListings(filters) {
  const { data } = await api.get('/listings/search', {
    params: {
      page: 1,
      limit: MAP_LISTING_LIMIT,
      ...(filters || {}),
    },
  })
  return Array.isArray(data?.listings) ? data.listings : []
}

export function toMapProperties(listings, userLocation = DEFAULT_ANDIJAN_LOCATION) {
  return listings
    .map(listing => normalizeListing(listing, userLocation))
    .filter(Boolean)
    .sort((a, b) => Number(b.badges.includes('Premium')) - Number(a.badges.includes('Premium')) || a.distanceKm - b.distanceKm)
}
