import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, createEvent } from '@testing-library/react'
import { useAddJobPasteShortcut } from './useAddJobPasteShortcut'

function clipboardData(text: string) {
  return { getData: (type: string) => (type === 'text/plain' ? text : '') }
}

function firePaste(target: Element, data: ReturnType<typeof clipboardData>) {
  const event = createEvent.paste(target, { clipboardData: data })
  fireEvent(target, event)
  return event
}

function PasteProbe({ onPasteUrl }: { onPasteUrl: (url: string) => void }) {
  useAddJobPasteShortcut(onPasteUrl)
  return <div data-testid="target">page content</div>
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('useAddJobPasteShortcut', () => {
  it('opens the drawer with the pasted URL', () => {
    const onPasteUrl = vi.fn()
    render(<PasteProbe onPasteUrl={onPasteUrl} />)
    const event = firePaste(
      screen.getByTestId('target'),
      clipboardData('https://linkedin.com/jobs/view/123'),
    )
    expect(onPasteUrl).toHaveBeenCalledTimes(1)
    expect(onPasteUrl).toHaveBeenCalledWith('https://linkedin.com/jobs/view/123')
    expect(event.defaultPrevented).toBe(true)
  })

  it('trims surrounding whitespace from the pasted URL', () => {
    const onPasteUrl = vi.fn()
    render(<PasteProbe onPasteUrl={onPasteUrl} />)
    firePaste(screen.getByTestId('target'), clipboardData('  https://example.com/job/9  \n'))
    expect(onPasteUrl).toHaveBeenCalledWith('https://example.com/job/9')
  })

  it('ignores pasted text that is not a URL and keeps native behavior', () => {
    const onPasteUrl = vi.fn()
    render(<PasteProbe onPasteUrl={onPasteUrl} />)
    const event = firePaste(screen.getByTestId('target'), clipboardData('just some notes'))
    expect(onPasteUrl).not.toHaveBeenCalled()
    expect(event.defaultPrevented).toBe(false)
  })

  it('ignores paste inside editable targets so native paste still works', () => {
    const onPasteUrl = vi.fn()
    const { container } = render(<PasteProbe onPasteUrl={onPasteUrl} />)
    const input = document.createElement('input')
    container.appendChild(input)
    const event = firePaste(input, clipboardData('https://example.com/job'))
    expect(onPasteUrl).not.toHaveBeenCalled()
    expect(event.defaultPrevented).toBe(false)
  })

  it('cleans up the listener on unmount', () => {
    const onPasteUrl = vi.fn()
    const { unmount } = render(<PasteProbe onPasteUrl={onPasteUrl} />)
    unmount()
    const probe = document.createElement('div')
    document.body.appendChild(probe)
    const event = createEvent.paste(probe, {
      clipboardData: clipboardData('https://example.com/job'),
    })
    fireEvent(probe, event)
    expect(onPasteUrl).not.toHaveBeenCalled()
  })
})
