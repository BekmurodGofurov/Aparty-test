import { createHttpCache } from './httpCache.js'
import { decodeJwtPayload } from '../utils/jwt.js'

export const browserCache = createHttpCache({ storage: window.localStorage })

// The cache is scoped per signed-in user (the access token's subject), never shared between accounts.
export const currentCacheScope = () => {
  const token = localStorage.getItem('accessToken')
  return token ? (decodeJwtPayload(token)?.sub ?? null) : null
}

// Read a cached GET response synchronously, without making a request. Used to paint a page
// instantly from the last known answer while it revalidates in the background — most useful
// right after a route remounts (React Router unmounts pages on navigation, so their own state
// cannot survive a visit away and back; the cache can). Returns undefined on a cache miss or
// for a request this cache never stores (see httpCache's RULES).
export const peekCache = (url, params) => {
  const scope = currentCacheScope()
  const rule = browserCache.ruleFor(url, scope)
  if (!rule) return undefined
  return browserCache.get(browserCache.keyFor(scope, url, params))
}
