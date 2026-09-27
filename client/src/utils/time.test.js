import assert from 'node:assert/strict'
import { test } from 'node:test'
import { formatTimeAgo, todayLocalIso } from './time.js'

test('today is the local calendar date, padded', () => {
  assert.equal(todayLocalIso(new Date(2030, 0, 5, 0, 30)), '2030-01-05')
  assert.equal(todayLocalIso(new Date(2030, 11, 31, 23, 59)), '2030-12-31')
})

test('recent times are shown relative to now', () => {
  const now = Date.now()
  assert.equal(formatTimeAgo(now - 10_000, now), 'Hozir')
  assert.equal(formatTimeAgo(now - 5 * 60_000, now), '5 daqiqa oldin')
  assert.equal(formatTimeAgo(now - 3 * 3_600_000, now), '3 soat oldin')
})
