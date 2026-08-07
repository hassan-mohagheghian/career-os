import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Select, SelectContent, SelectItem, SelectTrigger } from './select'

function renderTrigger(triggerProps: React.ComponentProps<typeof SelectTrigger> = {}) {
  render(
    <Select>
      <SelectTrigger {...triggerProps} data-testid="trigger">
        Open
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="a">A</SelectItem>
      </SelectContent>
    </Select>
  )
  return screen.getByTestId('trigger')
}

describe('SelectTrigger height', () => {
  it('renders at h-10 by default so it matches the design system inputs', () => {
    const trigger = renderTrigger()
    expect(trigger).toHaveClass('h-10')
  })

  it('renders at h-9 when size="sm"', () => {
    const trigger = renderTrigger({ size: 'sm' })
    expect(trigger).toHaveClass('h-9')
  })

  it('honors an explicit h-* override (e.g. toolbar h-7) instead of the data-size height', () => {
    const trigger = renderTrigger({ className: 'h-7 w-auto text-2xs gap-1 text-primary' })
    expect(trigger).toHaveClass('h-7')
    expect(trigger).not.toHaveClass('data-[size=default]:h-10')
    expect(trigger).not.toHaveClass('data-[size=sm]:h-9')
  })
})
