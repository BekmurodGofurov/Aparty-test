import { createHttpCache } from './httpCache.js'
import { decodeJwtPayload } from '../utils/jwt.js'

export const browserCache = createHttpCache({ storage: window.localStorage })

// The cache is scoped per signed-in user (the access token's subject), never shared between accounts.
// A browser that blocks storage access entirely (some private-browsing modes) just means no scope.
export const currentCacheScope = () => {
  try {
    const token = localStorage.getItem('accessToken')
    return token ? (decodeJwtPayload(token)?.sub ?? null) : null
  } catch {
    return null
  }
}

// Read a cached GET response synchronously, without making a request. Used to paint a page
// instantly from the last known answer while it revalidates in the background — most useful
// right after a route remounts (React Router unmounts pages on navigation, so their own state
// cannot survive a visit away and back; the cache can). Returns undefined on a cache miss, for a
// request this cache never stores (see httpCache's RULES), or when storage is unavailable.
export const peekCache = (url, params) => {
  try {
    const scope = currentCacheScope()
    const rule = browserCache.ruleFor(url, scope)
    if (!rule) return undefined
    return browserCache.get(browserCache.keyFor(scope, url, params))
  } catch {
    return undefined
  }
}
