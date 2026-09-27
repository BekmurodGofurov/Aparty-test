import assert from 'node:assert/strict'
import { test } from 'node:test'
import { AMENITY_KEYS, emptyAmenities } from './amenities.js'

test('every amenity starts switched off', () => {
  const amenities = emptyAmenities()
  assert.deepEqual(Object.keys(amenities), AMENITY_KEYS)
  assert.ok(Object.values(amenities).every((value) => value === false))
})

test('uses the names the backend filters on', () => {
  for (const key of ['air_conditioner', 'washing_machine', 'kitchen']) assert.ok(AMENITY_KEYS.includes(key))
  for (const legacy of ['ac', 'washer', 'kitchenware']) assert.ok(!AMENITY_KEYS.includes(legacy))
})
