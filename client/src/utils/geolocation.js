const ERROR_STATUS = { 1: 'denied', 2: 'unavailable', 3: 'timeout' }

// Native geolocation cannot be aborted, so cancelled and late callbacks are ignored.
export function locateBrowser({ geolocation, onSuccess, onError, timeoutMs = 9000 }) {
  let active = true
  let timer
  const finish = callback => {
    if (!active) return
    active = false
    clearTimeout(timer)
    callback()
  }
  const cancel = () => { active = false; clearTimeout(timer) }

  if (!geolocation?.getCurrentPosition) {
    finish(() => onError('unsupported'))
    return cancel
  }

  timer = setTimeout(() => finish(() => onError('timeout')), timeoutMs)
  try {
    geolocation.getCurrentPosition(
      position => {
        const lat = position?.coords?.latitude
        const lng = position?.coords?.longitude
        if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) {
          finish(() => onError('unavailable'))
          return
        }
        finish(() => onSuccess({ lat, lng }))
      },
      error => finish(() => onError(ERROR_STATUS[error?.code] || 'unavailable')),
      { enableHighAccuracy: false, timeout: timeoutMs, maximumAge: 5 * 60000 },
    )
  } catch {
    finish(() => onError('unavailable'))
  }
  return cancel
}
