import assert from 'node:assert/strict'
import { test } from 'node:test'
import { decodeJwtPayload } from './jwt.js'

const token = (claims) => {
  const encode = (value) => globalThis.Buffer.from(JSON.stringify(value)).toString('base64url')
  return `${encode({ alg: 'HS256', typ: 'JWT' })}.${encode(claims)}.signature`
}

test('reads the role and subject of an access token', () => {
  const claims = decodeJwtPayload(token({ sub: '2048865706', role: 'owner', type: 'access' }))
  assert.equal(claims.sub, '2048865706')
  assert.equal(claims.role, 'owner')
})

test('a null role stays null', () => {
  assert.equal(decodeJwtPayload(token({ sub: '1', role: null })).role, null)
})

test('handles url-safe characters and non-ASCII text', () => {
  const claims = decodeJwtPayload(token({ sub: '1', name: "Oʻktam ??>>" }))
  assert.equal(claims.name, "Oʻktam ??>>")
})

test('garbage returns null instead of throwing', () => {
  for (const value of ['', 'abc', 'a.b.c', 'a.@@@.c', undefined, null]) {
    assert.equal(decodeJwtPayload(value), null, String(value))
  }
})
