/**
 * Normalizes backend URLs entered by users.
 * Automatically adds 'http://' and default port '8000' if omitted.
 * Examples:
 *   "192.168.1.73"       -> "http://192.168.1.73:8000"
 *   "192.168.1.73:8000"  -> "http://192.168.1.73:8000"
 *   "http://192.168.1.73"-> "http://192.168.1.73:8000"
 */
export function normalizeBackendUrl(rawUrl) {
  if (!rawUrl || typeof rawUrl !== 'string') return 'http://localhost:8000'
  let url = rawUrl.trim().replace(/\/+$/, '')
  if (!url) return 'http://localhost:8000'

  // If protocol is missing, add http://
  if (!/^https?:\/\//i.test(url)) {
    url = `http://${url}`
  }

  try {
    const parsed = new URL(url)
    // If no port specified and not on standard HTTPS, default to 8000
    if (!parsed.port) {
      parsed.port = '8000'
    }
    return `${parsed.protocol}//${parsed.hostname}:${parsed.port}`
  } catch {
    return url
  }
}
