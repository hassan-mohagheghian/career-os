import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { FavoriteButton } from './FavoriteButton'

describe('FavoriteButton', () => {
  it('shows add-to-favorites state when not favorited', () => {
    render(<FavoriteButton favorite={false} onToggle={() => {}} />)
    const button = screen.getByLabelText('Add to favorites')
    expect(button).toBeInTheDocument()
    expect(button).toHaveAttribute('aria-pressed', 'false')
  })

  it('shows remove-from-favorites state when favorited', () => {
    render(<FavoriteButton favorite={true} onToggle={() => {}} />)
    const button = screen.getByLabelText('Remove from favorites')
    expect(button).toBeInTheDocument()
    expect(button).toHaveAttribute('aria-pressed', 'true')
  })

  it('calls onToggle on click', () => {
    const onToggle = vi.fn()
    render(<FavoriteButton favorite={false} onToggle={onToggle} />)
    fireEvent.click(screen.getByLabelText('Add to favorites'))
    expect(onToggle).toHaveBeenCalledTimes(1)
  })
})
