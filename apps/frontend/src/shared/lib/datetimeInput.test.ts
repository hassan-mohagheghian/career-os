import { describe, it, expect } from 'vitest'
import { toDatetimeLocalInput, toIsoFromLocalInput } from './datetimeInput'

describe('toDatetimeLocalInput', () => {
  it('renders an ISO timestamp in local wall-clock input form', () => {
    const out = toDatetimeLocalInput('2026-08-01T09:00:00Z')
    expect(out).toMatch(/^2026-08-01T\d{2}:\d{2}$/)
  })

  it('returns empty string for invalid or empty input', () => {
    expect(toDatetimeLocalInput(null)).toBe('')
    expect(toDatetimeLocalInput('not-a-date')).toBe('')
  })
})

describe('toIsoFromLocalInput', () => {
  it('returns null for empty input', () => {
    expect(toIsoFromLocalInput('')).toBeNull()
  })

  it('produces a parseable ISO string with an offset', () => {
    const iso = toIsoFromLocalInput('2026-08-01T09:30')
    expect(iso).toBeTruthy()
    expect(Number.isNaN(new Date(iso!).getTime())).toBe(false)
    expect(iso).toMatch(/\+|-/)
  })
})