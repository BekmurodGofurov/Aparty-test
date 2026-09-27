// Phone photos are several MB. Shrinking them in the browser before upload saves traffic and time.
export const MAX_IMAGE_SIDE = 1600
export const JPEG_QUALITY = 0.82
// Files this small are already cheap to send.
export const SKIP_BELOW_BYTES = 300 * 1024

// Size that fits inside `maxSide` while keeping the aspect ratio. Never enlarges.
export const fitWithin = (width, height, maxSide = MAX_IMAGE_SIDE) => {
  const scale = Math.min(1, maxSide / Math.max(width, height))
  return { width: Math.round(width * scale), height: Math.round(height * scale) }
}

// Returns a smaller JPEG, or the original file when it is small, not a raster image, or anything fails.
export const compressImage = async (file) => {
  if (file.size < SKIP_BELOW_BYTES || !file.type.startsWith('image/') || file.type === 'image/gif') return file
  try {
    const bitmap = await createImageBitmap(file)
    const { width, height } = fitWithin(bitmap.width, bitmap.height)
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    canvas.getContext('2d').drawImage(bitmap, 0, 0, width, height)
    bitmap.close?.()
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY))
    if (!blob || blob.size >= file.size) return file
    return new File([blob], `${file.name.replace(/\.[^.]+$/, '')}.jpg`, { type: 'image/jpeg' })
  } catch {
    return file
  }
}
