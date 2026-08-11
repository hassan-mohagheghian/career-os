import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import CompanyNotesTab from './CompanyNotesTab'
import { companyApi } from '@/entities/company/api'

vi.mock('@/entities/company/api', () => ({
  companyApi: {
    listNotes: vi.fn(),
    addNote: vi.fn(),
    updateNote: vi.fn(),
    deleteNote: vi.fn(),
    addLink: vi.fn(),
    updateLink: vi.fn(),
    deleteLink: vi.fn(),
  },
}))

const mockCompany = {
  id: 1,
  name: 'TechCorp',
  notes: [{ id: 'n1', content: 'Test note' }],
  links: [{ id: 'l1', url: 'https://example.com', title: 'Example', status: 'processed' }],
}

describe('CompanyNotesTab', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders notes section', () => {
    render(<CompanyNotesTab company={mockCompany} />)
    expect(screen.getByText('Company Notes')).toBeInTheDocument()
  })

  it('renders links section', () => {
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

  it('adds a note via companyApi', async () => {
    vi.mocked(companyApi.addNote).mockResolvedValue({ id: 99, content: 'New note' })
    vi.mocked(companyApi.listNotes).mockResolvedValue([
      { id: 'n1', content: 'Test note' },
      { id: 99, content: 'New note' },
    ] as any)
    render(<CompanyNotesTab company={{ ...mockCompany, notes: [] }} />)
    fireEvent.change(screen.getByPlaceholderText('Add a note (any information about the company)...'), {
      target: { value: 'New note' },
    })
    fireEvent.click(screen.getByText('Add Note'))
    await screen.findByText('New note')
    expect(companyApi.addNote).toHaveBeenCalledWith(1, { content: 'New note' })
  })
})
