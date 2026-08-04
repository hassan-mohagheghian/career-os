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
    filterFavorite: false,
    onFilterFavoriteChange: vi.fn(),
    filterRecommendation: '',
    onFilterRecommendationChange: vi.fn(),
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

describe('JobsToolbar favorite filter', () => {
  it('renders the favorites toggle', () => {
    renderToolbar()
    expect(screen.getByLabelText('Show favorites only')).toBeInTheDocument()
  })

  it('toggles the favorite filter on click', () => {
    const onFilterFavoriteChange = vi.fn()
    renderToolbar({ onFilterFavoriteChange })

    fireEvent.click(screen.getByLabelText('Show favorites only'))

    expect(onFilterFavoriteChange).toHaveBeenCalledWith(true)
  })

  it('toggles the favorite filter off when active', () => {
    const onFilterFavoriteChange = vi.fn()
    renderToolbar({ filterFavorite: true, onFilterFavoriteChange })

    fireEvent.click(screen.getByLabelText('Show favorites only'))

    expect(onFilterFavoriteChange).toHaveBeenCalledWith(false)
  })
})

describe('JobsToolbar recommendation filter', () => {
  it('renders a recommendation select', () => {
    renderToolbar()
    expect(screen.getByText('Recommendation')).toBeInTheDocument()
  })

  it('reports the selected recommendation', () => {
    const onFilterRecommendationChange = vi.fn()
    renderToolbar({ onFilterRecommendationChange })

    fireEvent.click(screen.getByText('Recommendation'))
    fireEvent.click(screen.getByText('Apply'))

    expect(onFilterRecommendationChange).toHaveBeenCalledWith('apply')
  })

  it('shows the selected recommendation label when active', () => {
    renderToolbar({ filterRecommendation: 'consider' })
    expect(screen.getByText('Consider')).toBeInTheDocument()
  })
})
