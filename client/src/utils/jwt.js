// Reads the claims of a JWT without verifying it. Only for display and routing decisions:
// the server still checks every token.
export const decodeJwtPayload = (token) => {
  try {
    const payload = token.split('.')[1]
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const json = new TextDecoder().decode(Uint8Array.from(atob(base64), (char) => char.charCodeAt(0)))
    return JSON.parse(json)
  } catch {
    return null
  }
}
