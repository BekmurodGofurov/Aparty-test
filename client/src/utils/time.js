const MINUTE = 60 * 1000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

// "Hozir", "5 daqiqa oldin", "3 soat oldin", "2 kun oldin", then the date.
export const formatTimeAgo = (value, now = Date.now()) => {
  const elapsed = now - new Date(value).getTime()
  if (!Number.isFinite(elapsed) || elapsed < MINUTE) return 'Hozir'
  if (elapsed < HOUR) return `${Math.floor(elapsed / MINUTE)} daqiqa oldin`
  if (elapsed < DAY) return `${Math.floor(elapsed / HOUR)} soat oldin`
  if (elapsed < 7 * DAY) return `${Math.floor(elapsed / DAY)} kun oldin`
  return new Date(value).toLocaleDateString('uz-UZ')
}
