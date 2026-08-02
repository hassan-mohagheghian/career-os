import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { formatTimeAgo } from './formatTimeAgo'

describe('formatTimeAgo', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-07-27T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns empty string for null input', () => {
    expect(formatTimeAgo(null)).toBe('')
  })

  it('returns "just now" for timestamps less than 1 minute ago', () => {
    const ts = new Date(Date.now() - 30_000).toISOString()
    expect(formatTimeAgo(ts)).toBe('just now')
  })

  it('returns minutes ago for timestamps within the hour', () => {
    const ts = new Date(Date.now() - 5 * 60_000).toISOString()
    expect(formatTimeAgo(ts)).toBe('5m ago')
  })

  it('returns hours ago for timestamps within the day', () => {
    const ts = new Date(Date.now() - 3 * 3600_000).toISOString()
    expect(formatTimeAgo(ts)).toBe('3h ago')
  })

  it('returns days ago for timestamps within a week', () => {
    const ts = new Date(Date.now() - 4 * 86400_000).toISOString()
    expect(formatTimeAgo(ts)).toBe('4d ago')
  })

  it('returns formatted date for timestamps older than 7 days', () => {
    const ts = new Date('2026-07-01T12:00:00Z').toISOString()
    const result = formatTimeAgo(ts)
    expect(result).toContain('7') // July
    expect(result).toContain('2026')
  })

  it('returns "just now" for timestamp exactly at now', () => {
    const ts = new Date(Date.now()).toISOString()
    expect(formatTimeAgo(ts)).toBe('just now')
  })
})
