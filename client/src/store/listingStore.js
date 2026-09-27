import { create } from 'zustand'
import { searchListings } from '../services/listingService'
import { emptyAmenities } from '../utils/amenities'
import { getErrorMessage } from '../utils/auth'

const initialFilters = {
  region: '',
  district: '',
  price_min: '',
  price_max: '',
  target_gender: '',
  rooms_count: '',
  available_spaces: '',
  owner_role: '',
  move_in_ready: false,
  rental_type: '',
  amenities: emptyAmenities(),
}

// Only the newest request may update the list, so a slow answer to an old filter cannot overwrite it.
let latestRequest = 0

export const useListingStore = create((set, get) => ({
  filters: initialFilters,
  results: [],
  total: 0,
  page: 1,
  pages: 1,
  loading: false,
  loadingMore: false,
  error: '',
  setFilter: (key, value) => set((state) => ({ filters: { ...state.filters, [key]: value } })),
  setAmenity: (key, value) =>
    set((state) => ({
      filters: {
        ...state.filters,
        amenities: { ...state.filters.amenities, [key]: value },
      },
    })),
  clearFilters: () => set({
    filters: { ...initialFilters, amenities: emptyAmenities() },
    page: 1,
    error: '',
  }),
  replaceFilters: (nextFilters = {}) => set({
    filters: {
      ...initialFilters,
      ...nextFilters,
      amenities: {
        ...emptyAmenities(),
        ...(nextFilters.amenities || {}),
      },
    },
    page: 1,
    error: '',
  }),
  fetchResults: async (page = 1, filtersOverride) => {
    const append = page > 1
    const requestId = ++latestRequest
    set(append ? { loadingMore: true, error: '' } : { loading: true, error: '' })
    try {
      const filters = filtersOverride || get().filters
      const normalized = {}
      Object.entries(filters).forEach(([key, value]) => {
        if (key === 'amenities') {
          Object.entries(value).forEach(([amenityKey, amenityValue]) => {
            if (amenityValue) normalized[amenityKey] = true
          })
          return
        }
        if (value === '' || value === null || value === false) return
        normalized[key] = value
      })
      const data = await searchListings(normalized, page)
      if (requestId !== latestRequest) return
      const listings = Array.isArray(data.listings) ? data.listings : []
      set((state) => ({
        results: append ? [...state.results, ...listings] : listings,
        total: data.total ?? 0,
        page: data.page ?? page,
        pages: data.pages ?? 1,
      }))
    } catch (error) {
      if (requestId !== latestRequest) return
      set((state) => ({
        results: append ? state.results : [],
        total: append ? state.total : 0,
        page: append ? state.page : page,
        pages: append ? state.pages : 1,
        error: getErrorMessage(error, error?.message || 'Listings load failed'),
      }))
    } finally {
      if (requestId === latestRequest) set({ loading: false, loadingMore: false })
    }
  },
  loadMore: () => get().fetchResults(get().page + 1),
}))
