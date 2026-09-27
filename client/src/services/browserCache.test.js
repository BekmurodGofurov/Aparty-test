import assert from 'node:assert/strict'
import { test } from 'node:test'

// browserCache.js reads window.localStorage at import time, so the fake must exist before import.
const store = new Map()
const fakeLocalStorage = {
  getItem: (key) => (store.has(key) ? store.get(key) : null),
  setItem: (key, value) => store.set(key, String(value)),
  removeItem: (key) => store.delete(key),
}
// Mirrors the browser, where both the bare global and window.localStorage refer to the same object.
globalThis.localStorage = fakeLocalStorage
globalThis.window = { localStorage: fakeLocalStorage }
// decodeJwtPayload only needs atob/TextDecoder, both already global in Node.

const { currentCacheScope, peekCache, browserCache } = await import('./browserCache.js')

const token = (claims) => {
  const encode = (value) => globalThis.Buffer.from(JSON.stringify(value)).toString('base64url')
  return `${encode({ alg: 'HS256' })}.${encode(claims)}.sig`
}

test('the cache scope is the signed-in user, or null when signed out', () => {
  assert.equal(currentCacheScope(), null)
  localStorage.setItem('accessToken', token({ sub: '20' }))
  assert.equal(currentCacheScope(), '20')
  localStorage.removeItem('accessToken')
})

test('peekCache reads what was set for the current user under the same key', () => {
  localStorage.setItem('accessToken', token({ sub: '20' }))
  const key = browserCache.keyFor('20', '/listings/search', { page: 1 })
  browserCache.set(key, { total: 3 }, 60_000)
  assert.deepEqual(peekCache('/listings/search', { page: 1 }), { total: 3 })
  localStorage.removeItem('accessToken')
})

test('peekCache returns undefined for a miss, an uncacheable endpoint, or another user', () => {
  localStorage.setItem('accessToken', token({ sub: '20' }))
  assert.equal(peekCache('/listings/search', { page: 99 }), undefined)
  assert.equal(peekCache('/bookings'), undefined)
  localStorage.setItem('accessToken', token({ sub: '21' }))
  assert.equal(peekCache('/listings/search', { page: 1 }), undefined)
  localStorage.removeItem('accessToken')
})

test('blocked storage access degrades to "no scope", it never throws', () => {
  const original = fakeLocalStorage.getItem
  fakeLocalStorage.getItem = () => { throw new Error('SecurityError: storage is disabled') }
  try {
    assert.equal(currentCacheScope(), null)
    assert.equal(peekCache('/listings/search', { page: 1 }), undefined)
  } finally {
    fakeLocalStorage.getItem = original
  }
})
