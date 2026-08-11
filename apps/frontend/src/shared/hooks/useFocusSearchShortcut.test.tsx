import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { useRef } from 'react'
import { useFocusSearchShortcut } from './useFocusSearchShortcut'

function fireKey(key: string, options: KeyboardEventInit = {}) {
  act(() => {
    window.dispatchEvent(new KeyboardEvent('keydown', { key, cancelable: true, bubbles: true, ...options }))
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

function SearchBox() {
  const ref = useRef<HTMLInputElement>(null)
  useFocusSearchShortcut(ref)
  return (
    <input
      ref={ref}
      defaultValue="existing"
      aria-label="Search"
    />
  )
}

describe('useFocusSearchShortcut', () => {
  it('focuses and selects the search input when F is pressed', () => {
    render(<SearchBox />)
    const input = screen.getByLabelText('Search') as HTMLInputElement

    expect(document.activeElement).not.toBe(input)
    fireKey('f')
    expect(document.activeElement).toBe(input)
    expect(input.selectionStart).toBe(0)
    expect(input.selectionEnd).toBe(input.value.length)
  })

  it('does not fire when typing in an input', () => {
    render(<SearchBox />)
    const input = screen.getByLabelText('Search') as HTMLInputElement

    fireEvent.keyDown(input, { key: 'f' })

    expect(document.activeElement).not.toBe(input)
  })

  it('ignores modifier combos', () => {
    render(<SearchBox />)
    const input = screen.getByLabelText('Search') as HTMLInputElement

    fireKey('f', { ctrlKey: true })
    fireKey('f', { metaKey: true })
    fireKey('f', { altKey: true })
    fireKey('f', { shiftKey: true })

    expect(document.activeElement).not.toBe(input)
  })

  it('cleans up the listener on unmount', () => {
    const { unmount } = render(<SearchBox />)
    const input = screen.getByLabelText('Search') as HTMLInputElement
    unmount()
    fireKey('f')
    expect(document.activeElement).not.toBe(input)
  })
})
