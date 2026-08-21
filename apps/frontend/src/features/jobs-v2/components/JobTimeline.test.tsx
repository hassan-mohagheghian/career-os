import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { JobTimeline } from './JobTimeline'
import type { JobTimelineDay } from '@/entities/job/types'

const days: JobTimelineDay[] = [
  { date: '2026-08-19', count: 3 },
  { date: '2026-08-18', count: 5 },
  { date: '2026-07-30', count: 4 },
]

describe('JobTimeline', () => {
  it('renders the header', () => {
    render(<JobTimeline days={days} />)
    expect(screen.getByText('Jobs added')).toBeInTheDocument()
  })

  it('renders a row per day with the count', () => {
    render(<JobTimeline days={days} />)
    expect(screen.getByText('Aug 19')).toBeInTheDocument()
    expect(screen.getByText('Aug 18')).toBeInTheDocument()
    expect(screen.getByText('Jul 30')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
  })

  it('inserts a month divider when the month changes', () => {
    render(<JobTimeline days={days} />)
    expect(screen.getByText('Aug 2026')).toBeInTheDocument()
    expect(screen.getByText('Jul 2026')).toBeInTheDocument()
  })

  it('does not repeat a month divider within the same month', () => {
    render(<JobTimeline days={days} />)
    expect(screen.getAllByText('Aug 2026')).toHaveLength(1)
  })

  it('shows an empty state when there are no days', () => {
    render(<JobTimeline days={[]} />)
    expect(screen.getByText('No jobs yet')).toBeInTheDocument()
  })
})