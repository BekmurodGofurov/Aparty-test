import { activeRentals } from './bookingAdapters.js'

// Student profile numbers come from the user's own bookings (GET /bookings) and saved listings.
// "requests" counts every booking the user sent; "rooms" counts the confirmed stays that have not ended.
export const profileStats = ({ favorites = [], bookings = [] }, today) => ({
  saved: favorites.length,
  requests: bookings.length,
  rooms: activeRentals(bookings, {}, today).length,
})
