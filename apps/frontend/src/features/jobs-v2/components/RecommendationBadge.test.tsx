import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { RecommendationBadge } from './RecommendationBadge'

describe('RecommendationBadge', () => {
  it('renders Apply for apply', () => {
    render(<RecommendationBadge recommendation="apply" />)
    expect(screen.getByText('Apply')).toBeInTheDocument()
  })

  it('renders Consider for consider', () => {
    render(<RecommendationBadge recommendation="consider" />)
    expect(screen.getByText('Consider')).toBeInTheDocument()
  })

  it('renders Skip for skip', () => {
    render(<RecommendationBadge recommendation="skip" />)
    expect(screen.getByText('Skip')).toBeInTheDocument()
  })

  it('renders an em dash for no recommendation', () => {
    const { container } = render(<RecommendationBadge recommendation={null} />)
    expect(container.textContent).toBe('—')
  })
})
