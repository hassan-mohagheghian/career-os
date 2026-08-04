import { describe, it, expect } from 'vitest'
import { parseDateTime } from './parseDateTime'

describe('parseDateTime', () => {
  it('returns null for empty input', () => {
    expect(parseDateTime(null)).toBeNull()
    expect(parseDateTime(undefined)).toBeNull()
    expect(parseDateTime('')).toBeNull()
    expect(parseDateTime('   ')).toBeNull()
  })

  it('returns null for invalid input', () => {
    expect(parseDateTime('garbage')).toBeNull()
    expect(parseDateTime('not-a-date')).toBeNull()
  })

  it('treats a naive timestamp (no offset) as UTC', () => {
    // The backend serializes UTC datetimes without a timezone marker. Without
    // this normalization the string would be interpreted as local time.
    const date = parseDateTime('2026-08-04T10:00:00.123456')
    expect(date?.toISOString()).toBe('2026-08-04T10:00:00.123Z')
  })

  it('treats a space-separated naive timestamp as UTC', () => {
    const date = parseDateTime('2026-08-04 10:00:00')
    expect(date?.toISOString()).toBe('2026-08-04T10:00:00.000Z')
  })

  it('keeps an explicit Z marker as-is', () => {
    const date = parseDateTime('2026-08-04T10:00:00Z')
    expect(date?.toISOString()).toBe('2026-08-04T10:00:00.000Z')
  })

  it('keeps an explicit numeric offset as-is', () => {
    const date = parseDateTime('2026-08-04T12:00:00+02:00')
    expect(date?.toISOString()).toBe('2026-08-04T10:00:00.000Z')
  })
})
