import assert from 'node:assert/strict'
import { test } from 'node:test'
import { compressImage, fitWithin, SKIP_BELOW_BYTES } from './imageCompress.js'

test('large photos are scaled down to the longest side', () => {
  assert.deepEqual(fitWithin(4000, 3000, 1600), { width: 1600, height: 1200 })
  assert.deepEqual(fitWithin(3000, 4000, 1600), { width: 1200, height: 1600 })
})

test('small images are never enlarged', () => {
  assert.deepEqual(fitWithin(800, 600, 1600), { width: 800, height: 600 })
})

test('small files and non-images are sent as they are', async () => {
  const small = { size: SKIP_BELOW_BYTES - 1, type: 'image/jpeg', name: 'a.jpg' }
  const gif = { size: SKIP_BELOW_BYTES * 4, type: 'image/gif', name: 'a.gif' }
  const pdf = { size: SKIP_BELOW_BYTES * 4, type: 'application/pdf', name: 'a.pdf' }
  for (const file of [small, gif, pdf]) assert.equal(await compressImage(file), file)
})

test('falls back to the original when the browser cannot decode it', async () => {
  const broken = { size: SKIP_BELOW_BYTES * 4, type: 'image/png', name: 'broken.png' }
  assert.equal(await compressImage(broken), broken)
})
