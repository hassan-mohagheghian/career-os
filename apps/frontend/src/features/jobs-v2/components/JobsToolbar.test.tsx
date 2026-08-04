import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import '@testing-library/jest-dom'
import { JobsToolbar } from './JobsToolbar'

function renderToolbar(overrides: Record<string, unknown> = {}) {
  const props = {
    query: '',
    onQueryChange: vi.fn(),
    filterProcessingStatus: '',
    onFilterProcessingStatusChange: vi.fn(),
    filterLocation: '',
    onFilterLocationChange: vi.fn(),
    filterRemote: '',
    onFilterRemoteChange: vi.fn(),
    filterVisa: '',
    onFilterVisaChange: vi.fn(),
    activeFilterCount: 0,
    onClearFilters: vi.fn(),
    ...overrides,
  }
  return render(<JobsToolbar {...(props as any)} />)
}

describe('JobsToolbar location filter', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders a location input', () => {
    renderToolbar()
    expect(screen.getByLabelText('Filter by location')).toBeInTheDocument()
  })

  it('debounces typed locations before reporting them', () => {
    const onFilterLocationChange = vi.fn()
    renderToolbar({ onFilterLocationChange })

    fireEvent.change(screen.getByLabelText('Filter by location'), { target: { value: 'Berlin' } })

    expect(onFilterLocationChange).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(300)
    })

    expect(onFilterLocationChange).toHaveBeenCalledWith('Berlin')
  })

  it('shows a clear button and clears the filter on click', () => {
    const onFilterLocationChange = vi.fn()
    renderToolbar({ filterLocation: 'Berlin', onFilterLocationChange })

    fireEvent.click(screen.getByLabelText('Clear location filter'))

    expect(onFilterLocationChange).toHaveBeenCalledWith('')
  })
})
