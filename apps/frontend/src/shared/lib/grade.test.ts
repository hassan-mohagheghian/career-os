import { describe, it, expect } from 'vitest'
import { gradeForScore, scoreColor } from './grade'

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

describe('scoreColor', () => {
  it('returns green for scores >= 90', () => {
    expect(scoreColor(90)).toBe('text-green-500')
    expect(scoreColor(95)).toBe('text-green-500')
  })

  it('returns emerald for scores >= 70', () => {
    expect(scoreColor(70)).toBe('text-emerald-500')
    expect(scoreColor(89)).toBe('text-emerald-500')
  })

  it('returns yellow for scores >= 50', () => {
    expect(scoreColor(50)).toBe('text-yellow-500')
    expect(scoreColor(69)).toBe('text-yellow-500')
  })

  it('returns orange for scores >= 30', () => {
    expect(scoreColor(30)).toBe('text-orange-500')
    expect(scoreColor(49)).toBe('text-orange-500')
  })

  it('returns red for scores < 30', () => {
    expect(scoreColor(0)).toBe('text-red-500')
    expect(scoreColor(29)).toBe('text-red-500')
  })

  it('returns muted for null, undefined or NaN', () => {
    expect(scoreColor(null)).toBe('text-muted-foreground')
    expect(scoreColor(undefined)).toBe('text-muted-foreground')
    expect(scoreColor(NaN)).toBe('text-muted-foreground')
  })
})
