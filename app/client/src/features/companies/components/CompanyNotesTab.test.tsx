import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompanyNotesTab from './CompanyNotesTab'

const mockCompany = {
  id: 1,
  name: 'TechCorp',
  notes: [{ id: 'n1', content: 'Test note' }],
  links: [{ id: 'l1', url: 'https://example.com', title: 'Example', status: 'processed' }],
}

describe('CompanyNotesTab', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve(mockCompany.links) })
    ))
  })

  it('renders notes section', () => {
    render(<CompanyNotesTab company={mockCompany} />)
    expect(screen.getByText('Company Notes')).toBeInTheDocument()
  })

  it('renders links section', async () => {
    render(<CompanyNotesTab company={mockCompany} />)
    expect(screen.getByText('Company Links')).toBeInTheDocument()
  })

  it('renders existing notes', () => {
    render(<CompanyNotesTab company={mockCompany} />)
    expect(screen.getByText('Test note')).toBeInTheDocument()
  })

  it('renders add note button', () => {
    render(<CompanyNotesTab company={mockCompany} />)
    expect(screen.getByText('Add Note')).toBeInTheDocument()
  })

  it('renders add link button', () => {
    render(<CompanyNotesTab company={mockCompany} />)
    expect(screen.getByText('Add Link')).toBeInTheDocument()
  })

  it('shows empty state when no notes', () => {
    const emptyCompany = { ...mockCompany, notes: [] }
    render(<CompanyNotesTab company={emptyCompany} />)
    expect(screen.getByText('No notes yet.')).toBeInTheDocument()
  })

  it('renders link form when Add Link clicked', () => {
    render(<CompanyNotesTab company={mockCompany} />)
    fireEvent.click(screen.getByText('Add Link'))
    expect(screen.getByPlaceholderText('URL (https://...)')).toBeInTheDocument()
  })

  it('renders note count badge', () => {
    render(<CompanyNotesTab company={mockCompany} />)
    expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1)
  })
})
