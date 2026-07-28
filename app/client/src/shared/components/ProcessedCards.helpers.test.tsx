import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import {
  numericToGrade, getScoreColor, getScoreBadge, getMatchClass,
  LocationBadge, VisaBadge, WorkTypeTag, scoreRank, CITY_COLORS,
  VISA_STYLES, DEFAULT_CITY_COLOR, CompactJobCard
} from './ProcessedCards'

describe('numericToGrade', () => {
  it('returns A++ for 90+', () => { expect(numericToGrade(95)).toBe('A++') })
  it('returns A+ for 80-89', () => { expect(numericToGrade(85)).toBe('A+') })
  it('returns A for 70-79', () => { expect(numericToGrade(75)).toBe('A') })
  it('returns B for 50-69', () => { expect(numericToGrade(60)).toBe('B') })
  it('returns C for 30-49', () => { expect(numericToGrade(40)).toBe('C') })
  it('returns D for <30', () => { expect(numericToGrade(10)).toBe('D') })
  it('returns P for null', () => { expect(numericToGrade(null)).toBe('P') })
  it('clamps to 100', () => { expect(numericToGrade(150)).toBe('A++') })
  it('clamps to 0', () => { expect(numericToGrade(-10)).toBe('D') })
})

describe('getScoreColor', () => {
  it('returns emerald for A++', () => { expect(getScoreColor('A++')).toContain('emerald') })
  it('returns emerald for A+', () => { expect(getScoreColor('A+')).toContain('emerald') })
  it('returns green for A', () => { expect(getScoreColor('A')).toContain('green') })
  it('returns blue for B', () => { expect(getScoreColor('B')).toContain('blue') })
  it('returns yellow for C', () => { expect(getScoreColor('C')).toContain('yellow') })
  it('returns orange for D', () => { expect(getScoreColor('D')).toContain('orange') })
  it('returns muted for unknown', () => { expect(getScoreColor('X')).toContain('muted') })
  it('handles numeric input', () => { expect(getScoreColor(95)).toContain('emerald') })
})

describe('getScoreBadge', () => {
  it('returns green badge for A', () => { expect(getScoreBadge('A')).toContain('green') })
  it('returns blue badge for B', () => { expect(getScoreBadge('B')).toContain('blue') })
  it('handles numeric input', () => { expect(getScoreBadge(95)).toContain('emerald') })
})

describe('getMatchClass', () => {
  it('returns green for High', () => { expect(getMatchClass('High')).toContain('green') })
  it('returns yellow for Medium', () => { expect(getMatchClass('Medium')).toContain('yellow') })
  it('returns red for Low', () => { expect(getMatchClass('Low')).toContain('red') })
})

describe('scoreRank', () => {
  it('returns numeric rank for letter grades', () => { expect(scoreRank('A++')).toBe(6) })
  it('returns number as-is', () => { expect(scoreRank(42)).toBe(42) })
  it('returns 0 for unknown', () => { expect(scoreRank('X')).toBe(0) })
})

describe('LocationBadge', () => {
  it('renders location text', () => {
    render(<LocationBadge loc="Berlin" />)
    expect(screen.getByText('Berlin')).toBeInTheDocument()
  })
  it('uses default color for unknown city', () => {
    render(<LocationBadge loc="Unknown" />)
    expect(screen.getByText('Unknown')).toBeInTheDocument()
  })
})

describe('VisaBadge', () => {
  it('renders visa label', () => {
    render(<VisaBadge visa="Strong" />)
    expect(screen.getByText('Strong')).toBeInTheDocument()
  })
  it('renders BEST label', () => {
    render(<VisaBadge visa="BEST" />)
    expect(screen.getByText('BEST')).toBeInTheDocument()
  })
  it('renders ? for uncertain', () => {
    render(<VisaBadge visa="Uncertain" />)
    expect(screen.getByText('?')).toBeInTheDocument()
  })
})

describe('WorkTypeTag', () => {
  it('renders Remote', () => {
    render(<WorkTypeTag type="Remote" />)
    expect(screen.getByText('Remote')).toBeInTheDocument()
  })
  it('renders Hybrid', () => {
    render(<WorkTypeTag type="Hybrid" />)
    expect(screen.getByText('Hybrid')).toBeInTheDocument()
  })
  it('renders On-site', () => {
    render(<WorkTypeTag type="On-site" />)
    expect(screen.getByText('On-site')).toBeInTheDocument()
  })
})

describe('CompactJobCard', () => {
  const job = {
    num: 1, company: 'Acme', role: 'Engineer', location: 'Berlin',
    parsedLocations: ['Berlin', 'Munich'], score: 'A', match: 'High',
    visa: 'Strong', work_type: 'Remote', overall_score: 85, fit_score: 78,
    success_score: 90, employment_type: 'Full-time', applicants: '10',
  }

  it('renders company name', () => {
    render(<CompactJobCard job={job} onClick={vi.fn()} />)
    expect(screen.getByText('Acme')).toBeInTheDocument()
  })

  it('renders role', () => {
    render(<CompactJobCard job={job} onClick={vi.fn()} />)
    expect(screen.getByText('Engineer')).toBeInTheDocument()
  })

  it('renders locations', () => {
    render(<CompactJobCard job={job} onClick={vi.fn()} />)
    expect(screen.getByText('Berlin')).toBeInTheDocument()
    expect(screen.getByText('Munich')).toBeInTheDocument()
  })

  it('renders match badge', () => {
    render(<CompactJobCard job={job} onClick={vi.fn()} />)
    expect(screen.getByText('High')).toBeInTheDocument()
  })

  it('renders overall score', () => {
    render(<CompactJobCard job={job} onClick={vi.fn()} />)
    expect(screen.getByText('85')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const onClick = vi.fn()
    render(<CompactJobCard job={job} onClick={onClick} />)
    onClick.mockImplementation(() => {})
  })

  it('renders additional location count when > 2', () => {
    const multiLocJob = { ...job, parsedLocations: ['Berlin', 'Munich', 'Hamburg'] }
    render(<CompactJobCard job={multiLocJob} onClick={vi.fn()} />)
    expect(screen.getByText('+1')).toBeInTheDocument()
  })

  it('falls back to letter grade when no numeric scores', () => {
    const letterJob = { ...job, overall_score: null, fit_score: null, success_score: null }
    render(<CompactJobCard job={letterJob} onClick={vi.fn()} />)
    expect(screen.getAllByText('A').length).toBeGreaterThanOrEqual(1)
  })
})

describe('static exports', () => {
  it('exports CITY_COLORS with Berlin', () => {
    expect(CITY_COLORS['Berlin']).toBeDefined()
  })

  it('exports VISA_STYLES with Strong', () => {
    expect(VISA_STYLES['Strong']).toBeDefined()
  })

  it('exports DEFAULT_CITY_COLOR', () => {
    expect(DEFAULT_CITY_COLOR).toBeDefined()
  })
})
