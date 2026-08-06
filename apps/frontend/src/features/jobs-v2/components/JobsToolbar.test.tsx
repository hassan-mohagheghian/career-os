import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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
    filterPinned: false,
    onFilterPinnedChange: vi.fn(),
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

describe('JobsToolbar pinned filter', () => {
  it('renders the pinned toggle', () => {
    renderToolbar()
    expect(screen.getByLabelText('Show pinned only')).toBeInTheDocument()
  })

  it('toggles the pinned filter on click', () => {
    const onFilterPinnedChange = vi.fn()
    renderToolbar({ onFilterPinnedChange })

    fireEvent.click(screen.getByLabelText('Show pinned only'))

    expect(onFilterPinnedChange).toHaveBeenCalledWith(true)
  })

  it('toggles the pinned filter off when active', () => {
    const onFilterPinnedChange = vi.fn()
    renderToolbar({ filterPinned: true, onFilterPinnedChange })

    fireEvent.click(screen.getByLabelText('Show pinned only'))

    expect(onFilterPinnedChange).toHaveBeenCalledWith(false)
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

describe('JobsToolbar columns toggle', () => {
  it('renders a Columns dropdown when a toggle handler is provided', () => {
    renderToolbar({ onTogglePinnedColumn: vi.fn() })
    expect(screen.getByText('Columns')).toBeInTheDocument()
  })

  it('does not render the Columns dropdown without a toggle handler', () => {
    renderToolbar()
    expect(screen.queryByText('Columns')).not.toBeInTheDocument()
  })

  it('shows a check on the Pinned option when the column is visible', async () => {
    const user = userEvent.setup()
    renderToolbar({ showPinnedColumn: true, onTogglePinnedColumn: vi.fn() })
    await user.click(screen.getByText('Columns'))
    const menu = await screen.findByRole('menu')
    expect(within(menu).getByText('Pinned')).toBeInTheDocument()
  })

  it('reports a column toggle when the Pinned option is clicked', async () => {
    const user = userEvent.setup()
    const onTogglePinnedColumn = vi.fn()
    renderToolbar({ showPinnedColumn: false, onTogglePinnedColumn })
    await user.click(screen.getByText('Columns'))
    const option = within(await screen.findByRole('menu')).getByText('Pinned')
    await user.click(option)
    expect(onTogglePinnedColumn).toHaveBeenCalledWith(true)
  })
})
