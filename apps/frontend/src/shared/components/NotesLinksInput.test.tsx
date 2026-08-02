import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import NotesLinksInput, { NoteItemDisplay, LinkItemDisplay } from './NotesLinksInput'

const defaultProps = {
  urlInput: '',
  setUrlInput: vi.fn(),
  notes: [],
  links: [],
  onAddNote: vi.fn(),
  onRemoveNote: vi.fn(),
  onAddLink: vi.fn(),
  onRemoveLink: vi.fn(),
  onSubmit: vi.fn(),
  submitting: false,
  processImmediately: true,
  onToggleProcess: vi.fn(),
}

describe('NotesLinksInput', () => {
  it('renders job link input', () => {
    render(<NotesLinksInput {...defaultProps} />)
    expect(screen.getByText('Job Link')).toBeInTheDocument()
  })

  it('renders notes section', () => {
    render(<NotesLinksInput {...defaultProps} />)
    expect(screen.getByText('Notes')).toBeInTheDocument()
  })

  it('renders links section', () => {
    render(<NotesLinksInput {...defaultProps} />)
    expect(screen.getByText('Links')).toBeInTheDocument()
  })

  it('renders error when provided', () => {
    render(<NotesLinksInput {...defaultProps} error="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('calls onSubmit when submit button clicked', () => {
    const onSubmit = vi.fn()
    render(<NotesLinksInput {...defaultProps} urlInput="https://example.com" onSubmit={onSubmit} />)
    fireEvent.click(screen.getByText('Add & Process'))
    expect(onSubmit).toHaveBeenCalled()
  })

  it('disables submit when urlInput is empty', () => {
    render(<NotesLinksInput {...defaultProps} />)
    const btn = screen.getByText('Add & Process')
    expect(btn).toBeDisabled()
  })

  it('calls onToggleProcess when Auto/Queue clicked', () => {
    const onToggleProcess = vi.fn()
    render(<NotesLinksInput {...defaultProps} onToggleProcess={onToggleProcess} />)
    fireEvent.click(screen.getByText('Auto'))
    expect(onToggleProcess).toHaveBeenCalled()
  })

  it('shows Queue when processImmediately is false', () => {
    render(<NotesLinksInput {...defaultProps} processImmediately={false} />)
    expect(screen.getByText('Queue')).toBeInTheDocument()
  })

  it('adds a note when Enter pressed', () => {
    const onAddNote = vi.fn()
    render(<NotesLinksInput {...defaultProps} onAddNote={onAddNote} />)
    const textarea = screen.getByPlaceholderText('Paste job description text...')
    fireEvent.change(textarea, { target: { value: 'New note' } })
    fireEvent.keyDown(textarea, { key: 'Enter' })
    expect(onAddNote).toHaveBeenCalledWith({ type: 'text', content: 'New note' })
  })

  it('shows editing state when editingId provided', () => {
    render(<NotesLinksInput {...defaultProps} editingId={42} />)
    expect(screen.getByText(/Adding to pending #42/)).toBeInTheDocument()
  })

  it('calls onCancelEdit when cancel editing clicked', () => {
    const onCancelEdit = vi.fn()
    render(<NotesLinksInput {...defaultProps} editingId={42} onCancelEdit={onCancelEdit} />)
    fireEvent.click(screen.getByText(/Adding to pending #42/).closest('div').querySelector('button'))
    expect(onCancelEdit).toHaveBeenCalled()
  })

  it('shows validation for non-http URL', () => {
    render(<NotesLinksInput {...defaultProps} urlInput="not-a-url" />)
    expect(screen.getByText('URL must start with http:// or https://')).toBeInTheDocument()
  })
})

describe('NoteItemDisplay', () => {
  it('renders text note', () => {
    render(<NoteItemDisplay note={{ type: 'text', content: 'My note' }} />)
    expect(screen.getByText('My note')).toBeInTheDocument()
  })

  it('renders URL note with link', () => {
    render(<NoteItemDisplay note={{ type: 'url', content: 'https://example.com' }} />)
    expect(screen.getByText('https://example.com')).toBeInTheDocument()
  })

  it('calls onRemove when X clicked', () => {
    const onRemove = vi.fn()
    render(<NoteItemDisplay note={{ type: 'text', content: 'Note' }} onRemove={onRemove} />)
    fireEvent.click(screen.getByText('Note').closest('div').querySelector('button'))
    expect(onRemove).toHaveBeenCalled()
  })
})

describe('LinkItemDisplay', () => {
  it('renders link URL', () => {
    render(<LinkItemDisplay link={{ url: 'https://example.com', title: 'Example' }} />)
    expect(screen.getByText('https://example.com')).toBeInTheDocument()
    expect(screen.getByText('Example')).toBeInTheDocument()
  })

  it('calls onRemove when X clicked', () => {
    const onRemove = vi.fn()
    render(<LinkItemDisplay link={{ url: 'https://example.com', title: '' }} onRemove={onRemove} />)
    const container = screen.getByText('https://example.com').closest('[class*="group/link"]')
    const btn = container?.querySelector('button')
    if (btn) fireEvent.click(btn)
    expect(onRemove).toHaveBeenCalled()
  })
})
