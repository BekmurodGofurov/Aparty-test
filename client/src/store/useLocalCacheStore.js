import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ─────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────

/** Max number of recently viewed apartments to keep (FIFO eviction). */
const MAX_RECENTLY_VIEWED = 10

/** Max number of recent search queries to keep. */
const MAX_RECENT_QUERIES = 5

/** localStorage key for this store. */
const STORAGE_KEY = 'aparty-local-cache'

// ─────────────────────────────────────────────────────────────
// Default State
// ─────────────────────────────────────────────────────────────

const defaultUserPreferences = {
  /** @type {'light' | 'dark'} */
  theme: 'dark',
  /** @type {string} Default city for search (e.g. "Andijon") */
  defaultSearchLocation: '',
}

const defaultRecentFilters = {
  /** @type {{ min: number | null, max: number | null }} */
  priceRange: { min: null, max: null },
  /** @type {string[]} Last N unique search queries */
  searchQueries: [],
}

/**
 * @typedef {Object} RecentlyViewedItem
 * @property {string} id        – Apartment/listing UUID
 * @property {string} title     – Display title (address or generated)
 * @property {string} thumbnail – First image URL or empty string
 * @property {number} viewedAt  – Unix timestamp (ms) when viewed
 */

// ─────────────────────────────────────────────────────────────
// Store
// ─────────────────────────────────────────────────────────────

/**
 * useLocalCacheStore — Zustand store with `persist` middleware.
 *
 * Persist config explained:
 *  • `name`        – localStorage key for serialized state
 *  • `version`     – Schema version. Bump this when state shape changes,
 *                    then handle migration in the `migrate` callback.
 *  • `partialize`  – Selects ONLY the data slices for serialization,
 *                    excluding action functions (which aren't serializable).
 *  • `migrate`     – Runs when a stored version doesn't match the current
 *                    version. Use it to reshape persisted data safely.
 */
export const useLocalCacheStore = create(
  persist(
    (set, get) => ({
      // ── State Slices ────────────────────────────────────────

      /** User preferences: theme + default search city */
      userPreferences: { ...defaultUserPreferences },

      /** Recent search filters: price range + last queries */
      recentFilters: { ...defaultRecentFilters },

      /** Last 10 visited apartments for instant "back" navigation */
      recentlyViewed: [],

      // ── Actions: User Preferences ──────────────────────────

      /**
       * Set UI theme and sync with the DOM attribute.
       * @param {'light' | 'dark'} theme
       */
      setTheme: (theme) => {
        document.documentElement.setAttribute('data-theme', theme)
        set((state) => ({
          userPreferences: { ...state.userPreferences, theme },
        }))
      },

      /**
       * Set the default city shown in search.
       * @param {string} location
       */
      setDefaultSearchLocation: (location) =>
        set((state) => ({
          userPreferences: {
            ...state.userPreferences,
            defaultSearchLocation: location,
          },
        })),

      // ── Actions: Recent Filters ────────────────────────────

      /**
       * Merge new filter data into the store.
       *
       * @param {Object} filterUpdate
       * @param {{ min?: number|null, max?: number|null }} [filterUpdate.priceRange]
       * @param {string} [filterUpdate.query] – A new search query to prepend
       */
      updateRecentFilters: ({ priceRange, query } = {}) =>
        set((state) => {
          const next = { ...state.recentFilters }

          // Merge price range (partial update OK)
          if (priceRange) {
            next.priceRange = {
              ...next.priceRange,
              ...priceRange,
            }
          }

          // Prepend query, deduplicate, and cap at MAX_RECENT_QUERIES
          if (query && query.trim()) {
            const trimmed = query.trim()
            const filtered = state.recentFilters.searchQueries.filter(
              (q) => q !== trimmed
            )
            next.searchQueries = [trimmed, ...filtered].slice(
              0,
              MAX_RECENT_QUERIES
            )
          }

          return { recentFilters: next }
        }),

      // ── Actions: Recently Viewed ───────────────────────────

      /**
       * Add an apartment to the recently viewed list.
       * Deduplicates by ID, prepends the newest, and caps at 10 items.
       *
       * @param {Object} apartment
       * @param {string} apartment.id        – Listing UUID
       * @param {string} apartment.title     – Display title
       * @param {string} [apartment.thumbnail] – First image URL
       */
      addRecentlyViewed: (apartment) =>
        set((state) => {
          if (!apartment?.id) return state

          const item = {
            id: apartment.id,
            title: apartment.title || '',
            thumbnail: apartment.thumbnail || '',
            viewedAt: Date.now(),
          }

          // Remove any previous entry with the same ID (dedup)
          const filtered = state.recentlyViewed.filter(
            (rv) => rv.id !== item.id
          )

          // Prepend new item, enforce FIFO cap
          return {
            recentlyViewed: [item, ...filtered].slice(0, MAX_RECENTLY_VIEWED),
          }
        }),

      /** Clear the entire recently viewed list. */
      clearRecentlyViewed: () => set({ recentlyViewed: [] }),

      // ── Actions: Global Reset ──────────────────────────────

      /** Factory-reset all persisted local cache state. */
      clearAllLocalCache: () =>
        set({
          userPreferences: { ...defaultUserPreferences },
          recentFilters: { ...defaultRecentFilters },
          recentlyViewed: [],
        }),
    }),

    // ── Persist Configuration ──────────────────────────────────
    {
      name: STORAGE_KEY,

      // Schema version — bump when state shape changes
      version: 1,

      // Only serialize state slices, not action functions
      partialize: (state) => ({
        userPreferences: state.userPreferences,
        recentFilters: state.recentFilters,
        recentlyViewed: state.recentlyViewed,
      }),

      /**
       * Migration callback — runs when the persisted `version` doesn't
       * match the current `version` above.
       *
       * @param {Object} persistedState – The state loaded from localStorage
       * @param {number} version        – The version that was persisted
       * @returns {Object} The migrated state
       */
      migrate: (persistedState, version) => {
        // v0 → v1: no transformation needed for initial release.
        // Future migrations go here:
        //   if (version === 1) { /* reshape for v2 */ }
        return persistedState
      },
    }
  )
)
