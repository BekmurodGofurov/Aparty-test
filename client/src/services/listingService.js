import { api } from './api'

export const searchListings = async (filters = {}, page = 1, pageSize = 12) => {
  const safePageSize = Math.min(Math.max(Number(pageSize) || 12, 1), 100)
  const { data } = await api.get('/listings/search', {
    params: { ...filters, page, limit: safePageSize },
  })
  return data
}

export const getListingById = async (id) => {
  const { data } = await api.get(`/listings/${id}`)
  return data
}

export const getMyListings = async () => {
  const { data } = await api.get('/listings/me')
  return data
}

export const createBooking = async ({ listingId, startDate, endDate, message }) => {
  const { data } = await api.post('/bookings', {
    listing_id: listingId,
    start_date: startDate,
    end_date: endDate,
    message: message || null,
  })
  return data
}

export const createRoommateListing = async ({ apartmentId, ...ad }) => {
  const { data } = await api.post(`/listings/${apartmentId}/roommate`, {
    residents_male: ad.residentsMale,
    residents_female: ad.residentsFemale,
    residents_children: ad.residentsChildren,
    available_spaces: ad.availableSpaces,
    target_gender: ad.targetGender,
    available_from: ad.availableFrom || null,
    price: ad.price,
    description: ad.description || null,
  })
  return data
}

export const getMyBookings = async () => {
  const { data } = await api.get('/bookings')
  return data
}

export const getIncomingBookings = async (listingId) => {
  const { data } = await api.get('/bookings/incoming', { params: listingId ? { listing_id: listingId } : {} })
  return data
}

export const updateBookingStatus = async (id, status) => {
  const { data } = await api.patch(`/bookings/${id}/status`, { status })
  return data
}

export const createListing = async (payload) => {
  const { data } = await api.post('/listings/', payload)
  return data
}

export const updateListing = async (id, payload) => {
  const { data } = await api.put(`/listings/${id}`, payload)
  return data
}

export const deleteListing = async (id) => {
  const { data } = await api.delete(`/listings/${id}`)
  return data
}

export const activateListingBasic = async (id) => {
  const { data } = await api.post(`/listings/${id}/activate-basic`)
  return data
}

export const upgradeListingToPremium = async (id) => {
  const { data } = await api.post(`/listings/${id}/upgrade-to-premium`)
  return data
}

export const markListingOccupied = async (id) => {
  const { data } = await api.post(`/listings/${id}/mark-occupied`)
  return data
}

export const markListingAvailable = async (id) => {
  const { data } = await api.post(`/listings/${id}/mark-available`)
  return data
}

export const getAdminListings = async () => {
  const { data } = await api.get('/admin/listings')
  return data
}
