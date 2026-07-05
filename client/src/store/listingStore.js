import { create } from 'zustand'
import { searchListings } from '../services/listingService'

const initialFilters = {
  viloyat: '',
  tuman: '',
  narx_min: '',
  narx_max: '',
  jins: '',
  xonalar_soni: '',
  bosh_joy: '',
  egasi_turi: '',
  kiring_yashaing: false,
  apartmentType: '', // '' = barcha, 'bomboq', 'yotoqxona'
  qulayliklar: {
    wifi: false,
    gaz: false,
    suv: false,
    tv: false,
    konditsioner: false,
    kir_mashina: false,
    holodilnik: false,
    oshxona_jihozi: false,
  },
}

const normalizeSearchValue = (key, value) => {
  if (key === 'jins') {
    return {
      erkak: 'male',
      ayol: 'female',
      aralash: 'mixed',
    }[value] || value
  }

  return value
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
        qulayliklar: { ...state.filters.qulayliklar, [key]: value },
      },
    })),
  clearFilters: () => set({ filters: { ...initialFilters, qulayliklar: { ...initialFilters.qulayliklar } }, page: 1, error: '' }),
  replaceFilters: (nextFilters = {}) => set({
    filters: {
      ...initialFilters,
      ...nextFilters,
      qulayliklar: {
        ...initialFilters.qulayliklar,
        ...(nextFilters.qulayliklar || {}),
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
        if (key === 'qulayliklar') {
          Object.entries(value).forEach(([amenityKey, amenityValue]) => {
            if (amenityValue) normalized[amenityKey] = true
          })
          return
        }
        if (value === '' || value === null || value === false) return
        normalized[key] = normalizeSearchValue(key, value)
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
