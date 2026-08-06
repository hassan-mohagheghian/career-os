import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import NotesLinksReadOnly from './NotesLinksReadOnly'

describe('NotesLinksReadOnly', () => {
  it('renders nothing when there are no notes or links', () => {
    const { container } = render(<NotesLinksReadOnly />)
    expect(container.firstChild).toBeNull()
  })

  it('renders notes with title and content', () => {
    render(<NotesLinksReadOnly notes={[{ id: 'n1', title: 'Research', content: 'Good culture' }]} />)
    expect(screen.getByText('Research:')).toBeInTheDocument()
    expect(screen.getByText('Good culture')).toBeInTheDocument()
  })

  it('skips notes without content', () => {
    const { container } = render(<NotesLinksReadOnly notes={[{ id: 'n1' }, { id: 'n2', content: 'Real note' }]} />)
    expect(screen.getByText('Real note')).toBeInTheDocument()
    expect(container.querySelectorAll('.rounded-lg').length).toBe(1)
  })

  it('renders links with title fallback to url', () => {
    render(<NotesLinksReadOnly links={[{ id: 'l1', url: 'https://acme.example', title: 'Website' }]} />)
    const link = screen.getByRole('link', { name: 'Website' })
    expect(link).toHaveAttribute('href', 'https://acme.example')
    expect(link).toHaveAttribute('target', '_blank')
  })

  it('skips links without url', () => {
    render(<NotesLinksReadOnly links={[{ id: 'l1' }, { id: 'l2', url: 'https://a.example' }]} />)
    expect(screen.getByRole('link')).toBeInTheDocument()
  })

  it('uses a custom heading', () => {
    render(<NotesLinksReadOnly heading="Company Notes" notes={[{ content: 'x' }]} />)
    expect(screen.getByText('Company Notes')).toBeInTheDocument()
  })
})
