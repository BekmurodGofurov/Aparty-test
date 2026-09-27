import assert from 'node:assert/strict'
import { test } from 'node:test'
import { profileStats } from './profileStats.js'

const TODAY = '2030-06-15'

const booking = (status, endDate = '2030-06-30') => ({ id: `${status}-${endDate}`, status, end_date: endDate })

test('counts saved listings, sent requests and current stays', () => {
  const stats = profileStats(
    {
      favorites: [{ id: 'l1' }, { id: 'l2' }],
      bookings: [booking('pending'), booking('confirmed'), booking('rejected'), booking('cancelled')],
    },
    TODAY,
  )
  assert.deepEqual(stats, { saved: 2, requests: 4, rooms: 1 })
})

test('a confirmed stay that already ended is not "my apartment"', () => {
  const stats = profileStats({ bookings: [booking('confirmed', '2030-06-14'), booking('confirmed', TODAY)] }, TODAY)
  assert.equal(stats.rooms, 1)
  assert.equal(stats.requests, 2)
})

test('a new user has zeros', () => {
  assert.deepEqual(profileStats({}, TODAY), { saved: 0, requests: 0, rooms: 0 })
})
