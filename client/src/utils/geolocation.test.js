import test from 'node:test'
import assert from 'node:assert/strict'
import { locateBrowser } from './geolocation.js'

test('returns valid coordinates once and ignores duplicate native callbacks', () => {
  const positions = []
  const errors = []
  locateBrowser({
    geolocation: { getCurrentPosition(success, error) { success({ coords: { latitude: 40.78, longitude: 72.34 } }); error({ code: 1 }) } },
    onSuccess: position => positions.push(position), onError: error => errors.push(error),
  })
  assert.deepEqual(positions, [{ lat: 40.78, lng: 72.34 }])
  assert.deepEqual(errors, [])
})

for (const [code, status] of [[1, 'denied'], [2, 'unavailable'], [3, 'timeout']]) {
  test('distinguishes geolocation error ' + status, () => {
    let result
    locateBrowser({ geolocation: { getCurrentPosition(_success, error) { error({ code }) } }, onSuccess: assert.fail, onError: value => { result = value } })
    assert.equal(result, status)
  })
}

test('a cancelled request cannot replace the selected default location or reopen a dialog', () => {
  let success
  let error
  const cancel = locateBrowser({
    geolocation: { getCurrentPosition(onSuccess, onError) { success = onSuccess; error = onError } },
    onSuccess: () => assert.fail('cancelled success'), onError: () => assert.fail('cancelled error'),
  })
  cancel()
  success({ coords: { latitude: 41.3, longitude: 69.2 } })
  error({ code: 1 })
})

test('ends an unresponsive native request with a timeout and ignores a late success', async () => {
  let success
  const statuses = []
  await new Promise(resolve => {
    locateBrowser({
      geolocation: { getCurrentPosition(onSuccess) { success = onSuccess } },
      onSuccess: () => assert.fail('late success'),
      onError: status => { statuses.push(status); resolve() },
      timeoutMs: 10,
    })
  })
  success({ coords: { latitude: 40.78, longitude: 72.34 } })
  assert.deepEqual(statuses, ['timeout'])
})

test('handles unavailable geolocation and synchronous browser failures', () => {
  const statuses = []
  locateBrowser({ onSuccess: assert.fail, onError: status => statuses.push(status) })
  locateBrowser({ geolocation: { getCurrentPosition() { throw new Error('device unavailable') } }, onSuccess: assert.fail, onError: status => statuses.push(status) })
  assert.deepEqual(statuses, ['unsupported', 'unavailable'])
})

test('rejects invalid coordinates before passing them to the map', () => {
  const statuses = []
  locateBrowser({ geolocation: { getCurrentPosition(success) { success({ coords: { latitude: NaN, longitude: 181 } }) } }, onSuccess: assert.fail, onError: status => statuses.push(status) })
  assert.deepEqual(statuses, ['unavailable'])
})
