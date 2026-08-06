import { describe, it, expect, vi, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAddJobShortcut } from './useAddJobShortcut'

function fireKey(key: string) {
  act(() => {
    window.dispatchEvent(new KeyboardEvent('keydown', { key, cancelable: true, bubbles: true }))
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('useAddJobShortcut', () => {
  it('opens the add-job drawer when N is pressed', () => {
    const onAddJob = vi.fn()
    renderHook(() => useAddJobShortcut(onAddJob))
    fireKey('n')
    expect(onAddJob).toHaveBeenCalledTimes(1)
  })

  it('ignores uppercase-shifted letters with modifiers', () => {
    const onAddJob = vi.fn()
    renderHook(() => useAddJobShortcut(onAddJob))
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', ctrlKey: true, cancelable: true }))
    })
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', metaKey: true, cancelable: true }))
    })
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', altKey: true, cancelable: true }))
    })
    expect(onAddJob).not.toHaveBeenCalled()
  })

  it('does not fire when typing in an input', () => {
    const onAddJob = vi.fn()
    renderHook(() => useAddJobShortcut(onAddJob))
    const input = document.createElement('input')
    document.body.appendChild(input)
    act(() => {
      input.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', bubbles: true, cancelable: true }))
    })
    expect(onAddJob).not.toHaveBeenCalled()
    document.body.removeChild(input)
  })

  it('cleans up the listener on unmount', () => {
    const onAddJob = vi.fn()
    const { unmount } = renderHook(() => useAddJobShortcut(onAddJob))
    unmount()
    fireKey('n')
    expect(onAddJob).not.toHaveBeenCalled()
  })
})
