import { describe, it, expect } from 'vitest'
import { formatCityLocation } from '@/shared/lib/formatLocation'

describe('formatCityLocation', () => {
  it('joins city and country', () => {
    expect(formatCityLocation('Berlin', 'Germany')).toBe('Berlin, Germany')
  })

  it('handles missing country', () => {
    expect(formatCityLocation('Remote', null)).toBe('Remote')
  })

  it('handles missing city', () => {
    expect(formatCityLocation(null, 'Germany')).toBe('Germany')
  })

  it('returns empty string when both are missing', () => {
    expect(formatCityLocation(undefined, null)).toBe('')
  })
})