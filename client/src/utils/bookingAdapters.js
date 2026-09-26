// Turns bookings from the Order Service (`/bookings/incoming`) into the shapes the owner and
// broker dashboards render: booking requests and current rentals.

const STATUS_LABELS = {
  pending: 'Kutilmoqda',
  accepted: 'Qabul qilingan',
  rejected: 'Rad etilgan',
  cancelled: 'Bekor qilingan',
}

const toIsoDate = (date) => date.toISOString().slice(0, 10)

export const indexById = (items = []) => Object.fromEntries(items.map((item) => [item.id, item]))

const listingSummary = (booking, listingsById) => {
  const listing = listingsById[booking.listing_id]
  return {
    id: booking.listing_id,
    address: listing?.address || booking.listing_title || '',
    district: listing?.district || '',
    region: listing?.region || '',
    images: listing?.images || [],
  }
}

const requesterOf = (booking) =>
  booking.requester || { id: booking.user_id, full_name: `Foydalanuvchi #${booking.user_id}`, phone: '' }

export const toRequest = (booking, listingsById = {}) => {
  const status = booking.status === 'confirmed' ? 'accepted' : booking.status
  return {
    id: booking.id,
    status,
    statusLabel: STATUS_LABELS[status] || status,
    message: booking.message,
    requester: requesterOf(booking),
    listing: listingSummary(booking, listingsById),
  }
}

// A rental is a confirmed booking that has not ended yet. `today` is injectable for tests.
export const isActiveRental = (booking, today = toIsoDate(new Date())) =>
  booking.status === 'confirmed' && booking.end_date >= today

export const toRental = (booking, listingsById = {}) => {
  const requester = requesterOf(booking)
  return {
    id: booking.id,
    listing_id: booking.listing_id,
    is_active: true,
    start_date: booking.start_date,
    end_date: booking.end_date,
    price: listingsById[booking.listing_id]?.price ?? 0,
    tenant: { full_name: requester.full_name, phone: requester.phone, is_verified: requester.is_verified },
    listing: listingSummary(booking, listingsById),
  }
}

export const activeRentals = (bookings, listingsById = {}, today) =>
  bookings.filter((booking) => isActiveRental(booking, today)).map((booking) => toRental(booking, listingsById))
