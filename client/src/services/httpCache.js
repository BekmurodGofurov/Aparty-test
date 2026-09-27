// Browser cache for GET responses, kept in localStorage to save traffic and make repeat views instant.
// Entries expire quickly, are scoped to the signed-in user (the token's subject), and are dropped
// when the user writes something that could change them or signs out.

const PREFIX = 'aparty_http_'
const MAX_ENTRIES = 40
const ANONYMOUS = 'anon'

const SECOND = 1000
const MINUTE = 60 * SECOND

// What may be cached and for how long. `private` data is only cached for a signed-in user.
// Bookings and your own listings change status often (accept/reject, occupancy), so their TTL is
// short and, unlike the other private entries, a write to /bookings also clears them directly
// (see INVALIDATIONS) rather than relying on the TTL alone.
const RULES = [
  { pattern: /^\/listings\/search$/, ttl: MINUTE, private: false },
  { pattern: /^\/listings\/[0-9a-f-]{36}$/i, ttl: 2 * MINUTE, private: false },
  { pattern: /^\/listings\/me$/, ttl: 20 * SECOND, private: true },
  { pattern: /^\/favorites\/me$/, ttl: 2 * MINUTE, private: true },
  { pattern: /^\/users\/me$/, ttl: 5 * MINUTE, private: true },
  { pattern: /^\/bookings$/, ttl: 20 * SECOND, private: true },
  { pattern: /^\/bookings\/incoming$/, ttl: 20 * SECOND, private: true },
]

// A write to a path prefix makes these cached paths stale.
const INVALIDATIONS = [
  { prefix: '/listings', stale: ['/listings', '/favorites'] },
  { prefix: '/favorites', stale: ['/favorites', '/listings'] },
  { prefix: '/bookings', stale: ['/listings', '/bookings'] },
  { prefix: '/users', stale: ['/users'] },
]

// Two callers can build the same query params object with keys in a different order (e.g. spread
// order); sorting them first means the cache key only depends on which params were sent, not how.
const stableParams = (params) =>
  JSON.stringify(
    Object.keys(params)
      .sort()
      .reduce((sorted, key) => ({ ...sorted, [key]: params[key] }), {}),
  )

const keyFor = (scope, url, params) => `${PREFIX}${scope}|${url}|${params ? stableParams(params) : ''}`

export const createHttpCache = ({ storage, now = Date.now }) => {
  const read = (key) => {
    try {
      const entry = JSON.parse(storage.getItem(key))
      return entry && entry.expires > now() ? entry : null
    } catch {
      return null
    }
  }

  const keys = () => Object.keys(storage).filter((key) => key.startsWith(PREFIX))

  const remove = (key) => {
    try {
      storage.removeItem(key)
    } catch {
      // storage unavailable: nothing to remove
    }
  }

  // Drops expired entries, then the entries closest to expiry until there is room.
  const prune = () => {
    const live = []
    for (const key of keys()) {
      const entry = read(key)
      if (entry) live.push({ key, expires: entry.expires })
      else remove(key)
    }
    live.sort((a, b) => a.expires - b.expires)
    live.slice(0, Math.max(0, live.length - MAX_ENTRIES + 1)).forEach(({ key }) => remove(key))
  }

  return {
    // `scope` is the signed-in user's id, or null when signed out.
    ruleFor: (url, scope) => {
      const rule = RULES.find((item) => item.pattern.test(url))
      return rule && (!rule.private || scope) ? rule : null
    },

    keyFor: (scope, url, params) => keyFor(scope || ANONYMOUS, url, params),

    get: (key) => read(key)?.data,

    set: (key, data, ttl) => {
      const value = JSON.stringify({ expires: now() + ttl, data })
      try {
        prune()
        storage.setItem(key, value)
      } catch {
        // Quota full or storage blocked: the site works without the cache.
      }
    },

    invalidateForWrite: (url) => {
      const rule = INVALIDATIONS.find((item) => url.startsWith(item.prefix))
      if (!rule) return
      for (const key of keys()) {
        const path = key.split('|')[1]
        if (rule.stale.some((stalePath) => path.startsWith(stalePath))) remove(key)
      }
    },

    clear: () => keys().forEach(remove),
  }
}
