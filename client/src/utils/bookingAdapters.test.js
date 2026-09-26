import assert from 'node:assert/strict'
import { test } from 'node:test'
import { activeRentals, indexById, isActiveRental, toRequest } from './bookingAdapters.js'

const TODAY = '2030-06-15'

const booking = (overrides = {}) => ({
  id: 'b1',
  listing_id: 'l1',
  listing_title: 'Sunny flat',
  user_id: 20,
  status: 'pending',
  start_date: '2030-06-20',
  end_date: '2030-06-30',
  message: 'Salom',
  requester: { id: 20, full_name: 'Malika Karimova', phone: '+998901112233', is_verified: true },
  ...overrides,
})

const listings = indexById([
  { id: 'l1', address: 'Amir Temur 5', district: 'Yunusobod', region: 'Toshkent shahri', price: 300, images: ['a.jpg'] },
])

test('a pending booking becomes a pending request with the requester and listing', () => {
  const request = toRequest(booking(), listings)
  assert.equal(request.status, 'pending')
  assert.equal(request.statusLabel, 'Kutilmoqda')
  assert.equal(request.requester.full_name, 'Malika Karimova')
  assert.deepEqual(request.listing, {
    id: 'l1', address: 'Amir Temur 5', district: 'Yunusobod', region: 'Toshkent shahri', images: ['a.jpg'],
  })
  assert.equal(request.message, 'Salom')
})

test('confirmed is shown as accepted and other statuses keep their name', () => {
  assert.equal(toRequest(booking({ status: 'confirmed' })).status, 'accepted')
  assert.equal(toRequest(booking({ status: 'rejected' })).statusLabel, 'Rad etilgan')
  assert.equal(toRequest(booking({ status: 'cancelled' })).statusLabel, 'Bekor qilingan')
})

test('without IAM data the requester falls back to the user id', () => {
  const request = toRequest(booking({ requester: null }))
  assert.equal(request.requester.full_name, 'Foydalanuvchi #20')
  assert.equal(request.requester.phone, '')
})

test('without the listing in the list the listing title is used as the address', () => {
  const request = toRequest(booking(), {})
  assert.equal(request.listing.address, 'Sunny flat')
  assert.deepEqual(request.listing.images, [])
})

test('only confirmed bookings that have not ended are active rentals', () => {
  assert.equal(isActiveRental(booking({ status: 'confirmed' }), TODAY), true)
  assert.equal(isActiveRental(booking({ status: 'confirmed', end_date: TODAY }), TODAY), true)
  assert.equal(isActiveRental(booking({ status: 'confirmed', end_date: '2030-06-14' }), TODAY), false)
  assert.equal(isActiveRental(booking({ status: 'pending' }), TODAY), false)
  assert.equal(isActiveRental(booking({ status: 'cancelled' }), TODAY), false)
})

test('a rental carries the tenant, the price of the listing and its dates', () => {
  const [rental] = activeRentals([booking({ status: 'confirmed' }), booking({ id: 'b2', status: 'pending' })], listings, TODAY)
  assert.equal(rental.id, 'b1')
  assert.equal(rental.listing_id, 'l1')
  assert.equal(rental.is_active, true)
  assert.equal(rental.price, 300)
  assert.equal(rental.tenant.full_name, 'Malika Karimova')
  assert.equal(rental.start_date, '2030-06-20')
  assert.equal(rental.listing.address, 'Amir Temur 5')
})

test('a rental of an unknown listing has price 0', () => {
  const [rental] = activeRentals([booking({ status: 'confirmed' })], {}, TODAY)
  assert.equal(rental.price, 0)
})

test('no bookings means no requests or rentals', () => {
  assert.deepEqual(activeRentals([], listings, TODAY), [])
})
