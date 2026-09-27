import assert from 'node:assert/strict'
import { test } from 'node:test'
import { createHttpCache } from './httpCache.js'

const fakeStorage = () => {
  const map = new Map()
  const storage = {
    getItem: (key) => (map.has(key) ? map.get(key) : null),
    setItem: (key, value) => map.set(key, value),
    removeItem: (key) => map.delete(key),
  }
  return new Proxy(storage, { ownKeys: () => [...map.keys()], getOwnPropertyDescriptor: () => ({ enumerable: true, configurable: true }) })
}

const LISTING_ID = '3f2b8c1e-8a4d-4e0b-9c53-0c1d2e3f4a5b'

const setup = () => {
  const clock = { time: 1_000_000 }
  const cache = createHttpCache({ storage: fakeStorage(), now: () => clock.time })
  return { cache, clock }
}

test('public listing reads are cached, endpoints with no rule are not', () => {
  const { cache } = setup()
  assert.ok(cache.ruleFor('/listings/search', null))
  assert.ok(cache.ruleFor(`/listings/${LISTING_ID}`, null))
  assert.equal(cache.ruleFor('/notifications/me', '1'), null)
  assert.equal(cache.ruleFor(`/listings/${LISTING_ID}/booking-info`, '1'), null)
})

test('private data is cached only for a signed-in user', () => {
  const { cache } = setup()
  for (const url of ['/users/me', '/favorites/me', '/listings/me', '/bookings', '/bookings/incoming']) {
    assert.equal(cache.ruleFor(url, null), null, url)
    assert.ok(cache.ruleFor(url, '20'), url)
  }
})

test('bookings and your own listings keep a short TTL, unlike the other private data', () => {
  const { cache } = setup()
  assert.ok(cache.ruleFor('/bookings', '20').ttl < cache.ruleFor('/users/me', '20').ttl)
  assert.ok(cache.ruleFor('/listings/me', '20').ttl < cache.ruleFor('/favorites/me', '20').ttl)
})

test('an entry is served until it expires', () => {
  const { cache, clock } = setup()
  const key = cache.keyFor('20', '/listings/search', { page: 1 })
  cache.set(key, { total: 3 }, 60_000)
  assert.deepEqual(cache.get(key), { total: 3 })
  clock.time += 59_000
  assert.deepEqual(cache.get(key), { total: 3 })
  clock.time += 2_000
  assert.equal(cache.get(key), undefined)
})

test('users and query parameters never share an entry', () => {
  const { cache } = setup()
  const first = cache.keyFor('20', '/favorites/me')
  cache.set(first, ['mine'], 60_000)
  assert.equal(cache.get(cache.keyFor('21', '/favorites/me')), undefined)
  assert.notEqual(cache.keyFor('20', '/listings/search', { page: 1 }), cache.keyFor('20', '/listings/search', { page: 2 }))
})

test('the same params in a different order still hit the same entry', () => {
  const { cache } = setup()
  const key = cache.keyFor('20', '/listings/search', { page: 1, limit: 8, region: 'Andijon' })
  cache.set(key, { total: 5 }, 60_000)
  const sameQuery = cache.keyFor('20', '/listings/search', { region: 'Andijon', page: 1, limit: 8 })
  assert.equal(key, sameQuery)
  assert.deepEqual(cache.get(sameQuery), { total: 5 })
})

test('saving a favourite drops saved lists, search cards and listing pages but keeps the profile', () => {
  const { cache } = setup()
  const favorites = cache.keyFor('20', '/favorites/me')
  const search = cache.keyFor('20', '/listings/search', { page: 1 })
  const detail = cache.keyFor('20', `/listings/${LISTING_ID}`)
  const profile = cache.keyFor('20', '/users/me')
  for (const key of [favorites, search, detail, profile]) cache.set(key, {}, 60_000)

  cache.invalidateForWrite(`/favorites/${LISTING_ID}`)
  assert.equal(cache.get(favorites), undefined)
  assert.equal(cache.get(search), undefined)
  assert.equal(cache.get(detail), undefined)
  assert.notEqual(cache.get(profile), undefined)
})

test('editing a listing drops listing reads and saved lists', () => {
  const { cache } = setup()
  const detail = cache.keyFor(null, `/listings/${LISTING_ID}`)
  const favorites = cache.keyFor('20', '/favorites/me')
  cache.set(detail, {}, 60_000)
  cache.set(favorites, [], 60_000)
  cache.invalidateForWrite(`/listings/${LISTING_ID}`)
  assert.equal(cache.get(detail), undefined)
  assert.equal(cache.get(favorites), undefined)
})

test('answering a booking drops cached bookings, incoming requests and listing reads', () => {
  const { cache } = setup()
  const mine = cache.keyFor('20', '/bookings')
  const incoming = cache.keyFor('20', '/bookings/incoming')
  const myListings = cache.keyFor('20', '/listings/me')
  const detail = cache.keyFor('20', `/listings/${LISTING_ID}`)
  for (const key of [mine, incoming, myListings, detail]) cache.set(key, {}, 60_000)

  cache.invalidateForWrite(`/bookings/${LISTING_ID}/status`)
  for (const key of [mine, incoming, myListings, detail]) assert.equal(cache.get(key), undefined)
})

test('a profile or role change drops the cached profile', () => {
  const { cache } = setup()
  const profile = cache.keyFor('20', '/users/me')
  cache.set(profile, {}, 60_000)
  cache.invalidateForWrite('/users/me/role')
  assert.equal(cache.get(profile), undefined)
})

test('clear removes every cached response', () => {
  const { cache } = setup()
  const key = cache.keyFor('20', '/users/me')
  cache.set(key, {}, 60_000)
  cache.clear()
  assert.equal(cache.get(key), undefined)
})

test('the cache stays bounded', () => {
  const { cache, clock } = setup()
  for (let page = 1; page <= 60; page += 1) {
    clock.time += 1
    cache.set(cache.keyFor('20', '/listings/search', { page }), { page }, 60_000)
  }
  const stored = [...Array(60).keys()].filter((i) => cache.get(cache.keyFor('20', '/listings/search', { page: i + 1 })) !== undefined)
  assert.ok(stored.length <= 40)
  assert.ok(stored.includes(59), 'the newest entry is kept')
})

test('a broken storage does not break reads or writes', () => {
  const cache = createHttpCache({
    storage: { getItem: () => { throw new Error('blocked') }, setItem: () => { throw new Error('blocked') }, removeItem: () => {} },
  })
  assert.doesNotThrow(() => cache.set('k', {}, 1000))
  assert.equal(cache.get('k'), undefined)
})
