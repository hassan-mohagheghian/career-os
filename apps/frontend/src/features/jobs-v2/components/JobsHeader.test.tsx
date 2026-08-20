import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { JobsHeader } from './JobsHeader'

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

function baseProps(overrides: Partial<Parameters<typeof JobsHeader>[0]> = {}): Parameters<typeof JobsHeader>[0] {
  return {
    total: 10,
    loadedCount: 5,
    processingCount: 0,
    onOpenQueue: vi.fn(),
    onAddJob: vi.fn(),
    onAddJobUrl: vi.fn(),
    ...overrides,
  }
}

function urlDataTransfer(url: string): DataTransfer {
  const values: Record<string, string> = {
    'text/uri-list': url,
    'text/plain': url,
  }
  return {
    types: Object.keys(values),
    getData: (type: string) => values[type] ?? '',
    dropEffect: '',
  } as unknown as DataTransfer
}

describe('JobsHeader', () => {
  it('renders the total count and add job shortcut hint', () => {
    render(<JobsHeader {...baseProps()} />)
    expect(screen.getByText(/Jobs \(10\)/)).toBeInTheDocument()
    expect(screen.getByText('N')).toBeInTheDocument()
  })

  it('triggers onRefresh when the refresh button is clicked', () => {
    const onRefresh = vi.fn()
    render(<JobsHeader {...baseProps({ onRefresh })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Refresh jobs' }))
    expect(onRefresh).toHaveBeenCalledTimes(1)
  })

  it('does not render the refresh button when onRefresh is not provided', () => {
    render(<JobsHeader {...baseProps()} />)
    expect(screen.queryByRole('button', { name: 'Refresh jobs' })).not.toBeInTheDocument()
  })

  it('disables the refresh button while refreshing', () => {
    render(<JobsHeader {...baseProps({ onRefresh: vi.fn(), isRefreshing: true })} />)
    expect(screen.getByRole('button', { name: 'Refresh jobs' })).toBeDisabled()
  })

  it('shows a queue badge when there are processing items', () => {
    render(<JobsHeader {...baseProps({ processingCount: 3 })} />)
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('calls onAddJobUrl with the dropped url', () => {
    const onAddJobUrl = vi.fn()
    render(<JobsHeader {...baseProps({ onAddJobUrl })} />)
    const addJobButton = screen.getByRole('button', { name: /Add Job/ })
    fireEvent.drop(addJobButton, { dataTransfer: urlDataTransfer('https://example.com/job') })
    expect(onAddJobUrl).toHaveBeenCalledWith('https://example.com/job')
  })

  it('allows the drop by preventing default on dragover', () => {
    const onAddJobUrl = vi.fn()
    render(<JobsHeader {...baseProps({ onAddJobUrl })} />)
    const addJobButton = screen.getByRole('button', { name: /Add Job/ })
    const evt = new Event('dragover', { bubbles: true, cancelable: true })
    Object.defineProperty(evt, 'dataTransfer', { value: urlDataTransfer('https://example.com/job') })
    addJobButton.dispatchEvent(evt)
    expect(evt.defaultPrevented).toBe(true)
    expect(onAddJobUrl).not.toHaveBeenCalled()
  })

  it('ignores drops without a url', () => {
    const onAddJobUrl = vi.fn()
    render(<JobsHeader {...baseProps({ onAddJobUrl })} />)
    const addJobButton = screen.getByRole('button', { name: /Add Job/ })
    const dt = { types: ['text/plain'], getData: () => 'hello world' } as unknown as DataTransfer
    fireEvent.drop(addJobButton, { dataTransfer: dt })
    expect(onAddJobUrl).not.toHaveBeenCalled()
  })
})
