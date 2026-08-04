import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import DateTime from './DateTime'
import { parseDateTime } from '@/shared/lib/parseDateTime'

const ORIGINAL_TZ = process.env.TZ

describe('DateTime', () => {
  beforeEach(() => {
    process.env.TZ = 'America/New_York'
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-07-27T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
    if (ORIGINAL_TZ === undefined) delete process.env.TZ
    else process.env.TZ = ORIGINAL_TZ
  })

  it('renders the fallback for empty or invalid values', () => {
    const { container } = render(<DateTime value={null} />)
    expect(container.textContent).toBe('—')
    render(<DateTime value="garbage" fallback="-" />)
    expect(screen.getByText('-')).toBeInTheDocument()
  })

  it('renders the local datetime for a naive UTC string (not the raw UTC value)', () => {
    // Backend sends naive UTC ("10:00") which must be shown as local (06:00 in
    // America/New_York during DST), not interpreted as local 10:00.
    const value = '2026-08-04T10:00:00'
    render(<DateTime value={value} />)

    const expected = parseDateTime(value)!.toLocaleString()
    expect(screen.getByText(expected)).toBeInTheDocument()
    expect(screen.queryByText(new Date(value).toLocaleString())).not.toBeInTheDocument()
    expect(expected).toContain('6:00:00')
  })

  it('renders a relative time for the relative format', () => {
    render(<DateTime value="2026-07-27T11:00:00" format="relative" />)
    expect(screen.getByText('1h ago')).toBeInTheDocument()
  })

  it('shows the full local datetime on hover for compact formats', () => {
    const value = '2026-07-27T10:00:00'
    render(<DateTime value={value} format="relative" />)
    expect(screen.getByText('2h ago')).toHaveAttribute(
      'title',
      parseDateTime(value)!.toLocaleString()
    )
  })

  it('renders date and time formats from the parsed local date', () => {
    const value = '2026-08-04T10:00:00'
    const parsed = parseDateTime(value)!

    render(<DateTime value={value} format="date" />)
    expect(screen.getByText(parsed.toLocaleDateString())).toBeInTheDocument()

    render(<DateTime value={value} format="time" />)
    expect(screen.getByText(parsed.toLocaleTimeString())).toBeInTheDocument()
  })
})
