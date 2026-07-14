import { create } from 'zustand'
import { searchListings } from '../services/listingService'

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
  apartmentType: '',
  amenities: {
    wifi: false,
    gas: false,
    water: false,
    tv: false,
    ac: false,
    washer: false,
    fridge: false,
    kitchenware: false,
  },
}

export const useListingStore = create((set, get) => ({
  filters: initialFilters,
  results: [],
  total: 0,
  page: 1,
  pages: 1,
  loading: false,
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
    filters: { ...initialFilters, amenities: { ...initialFilters.amenities } },
    page: 1,
    error: '',
  }),
  replaceFilters: (nextFilters = {}) => set({
    filters: {
      ...initialFilters,
      ...nextFilters,
      amenities: {
        ...initialFilters.amenities,
        ...(nextFilters.amenities || {}),
      },
    },
    page: 1,
    error: '',
  }),
  fetchResults: async (page = 1, filtersOverride) => {
    set({ loading: true, error: '' })
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
      if (data.success === false) {
        throw new Error(data.message || 'Listings load failed')
      }
      set({
        results: Array.isArray(data.listings) ? data.listings : [],
        total: data.total ?? 0,
        page: data.page ?? page,
        pages: data.pages ?? 1,
      })
    } catch (error) {
      set({
        results: [],
        total: 0,
        page,
        pages: 1,
        error: error?.message || 'Listings load failed',
      })
    } finally {
      set({ loading: false })
    }
  },
}))
