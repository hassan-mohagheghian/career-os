import { describe, it, expect } from 'vitest'
import { gradeForScore } from './grade'

describe('gradeForScore', () => {
  it('returns A++ for scores >= 90', () => {
    expect(gradeForScore(90)).toBe('A++')
    expect(gradeForScore(95)).toBe('A++')
  })

  it('returns A+ for scores >= 80', () => {
    expect(gradeForScore(80)).toBe('A+')
    expect(gradeForScore(89)).toBe('A+')
  })

  it('returns A for scores >= 70', () => {
    expect(gradeForScore(70)).toBe('A')
    expect(gradeForScore(79)).toBe('A')
  })

  it('returns B for scores >= 50', () => {
    expect(gradeForScore(50)).toBe('B')
    expect(gradeForScore(69)).toBe('B')
  })

  it('returns C for scores >= 30', () => {
    expect(gradeForScore(30)).toBe('C')
    expect(gradeForScore(49)).toBe('C')
  })

  it('returns D for scores >= 0', () => {
    expect(gradeForScore(0)).toBe('D')
    expect(gradeForScore(29)).toBe('D')
  })

  it('returns P for null, undefined or NaN', () => {
    expect(gradeForScore(null)).toBe('P')
    expect(gradeForScore(undefined)).toBe('P')
    expect(gradeForScore(NaN)).toBe('P')
  })
})
