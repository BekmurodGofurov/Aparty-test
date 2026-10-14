import { useState } from 'react'
import { PLACEHOLDER_IMAGE } from '../../utils/images'

// Remote photos break over time (an avatar changed in Telegram, a deleted upload). When the source is
// missing or fails to load, render `fallback`, or the listing placeholder photo when none is given.
export function FallbackImage({ src, fallback, as: Image = 'img', ...props }) {
  const [failedSrc, setFailedSrc] = useState(null)
  const usable = Boolean(src) && src !== failedSrc

  if (!usable && fallback !== undefined) return fallback
  return <Image {...props} src={usable ? src : PLACEHOLDER_IMAGE} onError={() => setFailedSrc(src)} />
}
