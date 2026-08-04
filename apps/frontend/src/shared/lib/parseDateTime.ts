/**
 * Parse an API timestamp into a Date.
 *
 * The backend stores and serializes UTC datetimes without a timezone marker
 * (e.g. "2026-08-04T10:00:00.123456"). JavaScript would otherwise interpret
 * such a string as LOCAL time, shifting the rendered time away from the real
 * instant. Strings that already carry an explicit offset ("Z" or "+02:00") are
 * parsed as-is. Returns null for empty or invalid input.
 */
export function parseDateTime(ts: string | null | undefined): Date | null {
  if (!ts) return null
  const value = ts.trim()
  if (!value) return null

  const hasOffset = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)
  const normalized = hasOffset ? value : value.replace(' ', 'T') + 'Z'

  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date
}
