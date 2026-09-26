const EARTH_RADIUS_KM = 6371

export const DEFAULT_ANDIJAN_LOCATION = {
  lat: 40.7821,
  lng: 72.3442,
}

// Tashkent city center. Keep in sync with DEFAULT_LATITUDE/LONGITUDE in catalog-service constants.
export const DEFAULT_LISTING_LOCATION = {
  lat: 41.311081,
  lng: 69.240562,
}

export function getDistanceKm(from, to) {
  if (!from || !to) return null

  const lat1 = toRadians(from.lat)
  const lat2 = toRadians(to.lat)
  const deltaLat = toRadians(to.lat - from.lat)
  const deltaLng = toRadians(to.lng - from.lng)

  const a =
    Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) *
    Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2)

  return EARTH_RADIUS_KM * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export function formatDistance(distanceKm) {
  if (distanceKm == null) return 'Masofa aniqlanmadi'
  if (distanceKm < 1) return `${Math.round(distanceKm * 1000)} m`
  return `${distanceKm.toFixed(1)} km`
}

function toRadians(value) {
  return value * Math.PI / 180
}
