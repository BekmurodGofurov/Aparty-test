import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ─────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────

/** Max number of recently viewed apartments to keep (FIFO eviction). */
const MAX_RECENTLY_VIEWED = 10

/** Max number of recent search queries to keep. */
const MAX_RECENT_QUERIES = 5

/** Max number of ETag cache entries to keep (LRU eviction by access time). */
const MAX_ETAG_ENTRIES = 50

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

/**
 * @typedef {Object} EtagCacheEntry
 * @property {string} etag      – The ETag value from the server (e.g. W/"abc...")
 * @property {any}    data      – The cached response body
 * @property {number} accessedAt – Unix timestamp (ms) of last access (for LRU eviction)
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

      /**
       * ETag cache — keyed by URL path.
       * Each entry stores the ETag string + the cached response data.
       * This enables HTTP 304 Not Modified zero-bandwidth responses.
       *
       * Shape: { [url: string]: EtagCacheEntry }
       *
       * Example:
       *   {
       *     "/locations": {
       *       etag: 'W/"a3f2b8..."',
       *       data: { regions: [...], amenities: [...] },
       *       accessedAt: 1721984000000
       *     }
       *   }
       */
      etagCache: {},

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

      // ── Actions: ETag Cache ────────────────────────────────

      /**
       * Store or update an ETag entry for a specific URL.
       * Performs LRU eviction when the cache exceeds MAX_ETAG_ENTRIES.
       *
       * @param {string} url  – API endpoint path (e.g. "/locations")
       * @param {string} etag – The ETag value from the server
       * @param {any}    data – The response body to cache locally
       */
      setEtagEntry: (url, etag, data) =>
        set((state) => {
          const next = { ...state.etagCache }

          // Store the new entry with a fresh access timestamp
          next[url] = { etag, data, accessedAt: Date.now() }

          // LRU eviction: if we exceed the max, remove the oldest entries
          const keys = Object.keys(next)
          if (keys.length > MAX_ETAG_ENTRIES) {
            const sorted = keys.sort(
              (a, b) => (next[a].accessedAt || 0) - (next[b].accessedAt || 0)
            )
            // Remove the oldest entries until we're within the limit
            const toRemove = sorted.slice(0, keys.length - MAX_ETAG_ENTRIES)
            toRemove.forEach((key) => delete next[key])
          }

          return { etagCache: next }
        }),

      /**
       * Remove a specific ETag cache entry.
       * Call this after mutations (POST/PUT/DELETE) that change the resource.
       *
       * @param {string} url – The endpoint URL to invalidate
       */
      removeEtagEntry: (url) =>
        set((state) => {
          const next = { ...state.etagCache }
          delete next[url]
          return { etagCache: next }
        }),

      /** Clear all ETag cache entries. */
      clearEtagCache: () => set({ etagCache: {} }),

      // ── Actions: Global Reset ──────────────────────────────

      /** Factory-reset all persisted local cache state. */
      clearAllLocalCache: () =>
        set({
          userPreferences: { ...defaultUserPreferences },
          recentFilters: { ...defaultRecentFilters },
          recentlyViewed: [],
          etagCache: {},
        }),
    }),

    // ── Persist Configuration ──────────────────────────────────
    {
      name: STORAGE_KEY,

      // Schema version — bumped to 2 for the etagCache addition
      version: 2,

      // Only serialize state slices, not action functions
      partialize: (state) => ({
        userPreferences: state.userPreferences,
        recentFilters: state.recentFilters,
        recentlyViewed: state.recentlyViewed,
        etagCache: state.etagCache,
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
        // v1 → v2: Add the etagCache slice (missing in v1).
        if (version === 1) {
          persistedState.etagCache = {}
        }
        return persistedState
      },
    }
  )
)
