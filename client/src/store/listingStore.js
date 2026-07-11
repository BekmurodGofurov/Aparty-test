import { create } from 'zustand'
import { searchListings } from '../services/listingService'
import { adaptListing } from '../utils/adaptListing'

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



/**
 * Maps Uzbek filter key names → backend English query param names,
 * and converts Uzbek gender values → backend English values.
 * Returns { key, value } so the caller can set the correct param name.
 */
const normalizeFilter = (key, value) => {
  // key rename map: frontend → backend
  const KEY_MAP = {
    viloyat:      'region',
    tuman:        'district',
    narx_min:     'price_min',
    narx_max:     'price_max',
    jins:         'target_gender',
    xonalar_soni: 'rooms_count',
    bosh_joy:     'available_spaces',
    egasi_turi:   'owner_role',
  }

  // gender value map
  const GENDER_MAP = { erkak: 'male', ayol: 'female', aralash: 'mixed' }

  const mappedKey = KEY_MAP[key] ?? key
  let mappedValue = value

  if (key === 'jins') {
    mappedValue = GENDER_MAP[value] ?? value
  }

  return { key: mappedKey, value: mappedValue }
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
        const { key: mappedKey, value: mappedValue } = normalizeFilter(key, value)
        normalized[mappedKey] = mappedValue
      })
      const data = await searchListings(normalized, page)
      if (data.success === false) {
        throw new Error(data.message || 'Listings load failed')
      }
      set({
        results: Array.isArray(data.listings) ? data.listings.map(adaptListing) : [],
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
