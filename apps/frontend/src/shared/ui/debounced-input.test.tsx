import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { DebouncedInput, type DebouncedInputProps } from './debounced-input'

type SetupProps = Omit<Partial<DebouncedInputProps>, 'value' | 'onValueChange'>

function setup(initial = '', props: SetupProps = {}) {
  const onValueChange = vi.fn()
  const utils = render(<DebouncedInput value={initial} onValueChange={onValueChange} {...props} />)
  return { onValueChange, ...utils }
}

describe('DebouncedInput', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('reflects typing immediately', () => {
    setup()
    const input = screen.getByRole('textbox')

    fireEvent.change(input, { target: { value: 'Ber' } })

    expect(input).toHaveValue('Ber')
  })

  it('debounces onValueChange until the delay elapses', () => {
    const { onValueChange } = setup()
    const input = screen.getByRole('textbox')

    fireEvent.change(input, { target: { value: 'Berlin' } })
    expect(onValueChange).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(300)
    })

    expect(onValueChange).toHaveBeenCalledTimes(1)
    expect(onValueChange).toHaveBeenCalledWith('Berlin')
  })

  it('resets the debounce timer on continued typing', () => {
    const { onValueChange } = setup()
    const input = screen.getByRole('textbox')

    fireEvent.change(input, { target: { value: 'Ber' } })
    act(() => {
      vi.advanceTimersByTime(200)
    })
    expect(onValueChange).not.toHaveBeenCalled()

    fireEvent.change(input, { target: { value: 'Berlin' } })
    act(() => {
      vi.advanceTimersByTime(200)
    })
    expect(onValueChange).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(100)
    })
    expect(onValueChange).toHaveBeenCalledTimes(1)
    expect(onValueChange).toHaveBeenCalledWith('Berlin')
  })

  it('fires onValueChange immediately when the input is emptied', () => {
    const { onValueChange } = setup('Berlin')
    const input = screen.getByRole('textbox')

    fireEvent.change(input, { target: { value: '' } })

    expect(input).toHaveValue('')
    expect(onValueChange).toHaveBeenCalledWith('')
  })

  it('clears immediately via the clear button and cancels pending debounce', () => {
    const { onValueChange } = setup('', { clearable: true, clearLabel: 'Clear' })
    const input = screen.getByRole('textbox')

    fireEvent.change(input, { target: { value: 'Be' } })
    fireEvent.click(screen.getByRole('button', { name: 'Clear' }))

    expect(input).toHaveValue('')
    expect(onValueChange).toHaveBeenLastCalledWith('')

    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(onValueChange).toHaveBeenCalledTimes(1)
  })

  it('syncs to external value changes and drops stale debounces', () => {
    const onValueChange = vi.fn()
    const { rerender } = render(<DebouncedInput value="Berlin" onValueChange={onValueChange} />)
    const input = screen.getByRole('textbox')

    fireEvent.change(input, { target: { value: 'Ber' } })
    rerender(<DebouncedInput value="" onValueChange={onValueChange} />)
    expect(input).toHaveValue('')

    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(onValueChange).not.toHaveBeenCalled()
  })

  it('does not fire onValueChange after unmount', () => {
    const { onValueChange, unmount } = setup()
    const input = screen.getByRole('textbox')

    fireEvent.change(input, { target: { value: 'Ber' } })
    unmount()

    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(onValueChange).not.toHaveBeenCalled()
  })
})
