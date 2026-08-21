import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApplicationNotes } from './ApplicationNotes'
import { applicationApi } from '@/entities/application/api'
import type { ApplicationDetail } from '@/entities/application/types'

vi.mock('@/entities/application/api', () => ({
  applicationApi: {
    addNote: vi.fn(),
    deleteNote: vi.fn(),
  },
}))

const sampleApplication: ApplicationDetail = {
  id: 'app-1',
  job_id: 'job-1',
  status: 'applied',
  applied_at: null,
  created_at: null,
  updated_at: null,
  status_timeline: [],
  follow_ups: [],
  notes: [
    {
      id: 'note-2',
      application_id: 'app-1',
      content: 'Recruiter call — positive signal',
      created_at: '2026-08-21T14:02:00Z',
      updated_at: null,
    },
    {
      id: 'note-1',
      application_id: 'app-1',
      content: 'Sent tailored resume via LinkedIn',
      created_at: '2026-08-20T09:47:00Z',
      updated_at: null,
    },
  ],
  documents: [],
}

function renderNotes(app: ApplicationDetail = sampleApplication) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ApplicationNotes application={app} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ApplicationNotes', () => {
  it('renders notes newest first with timestamps', () => {
    renderNotes()
    expect(screen.getByText('Recruiter call — positive signal')).toBeInTheDocument()
    expect(screen.getByText('Sent tailored resume via LinkedIn')).toBeInTheDocument()
    const items = screen.getAllByText(/Recruiter call|Sent tailored resume/)
    expect(items[0]).toHaveTextContent('Recruiter call')
  })

  it('shows the empty state when there are no notes', () => {
    renderNotes({ ...sampleApplication, notes: [] })
    expect(screen.getByText(/No notes yet/)).toBeInTheDocument()
  })

  it('disables Add Note while the textarea is empty', () => {
    renderNotes()
    expect(screen.getByRole('button', { name: /add note/i })).toBeDisabled()
  })

  it('adds a note and clears the textarea', async () => {
    vi.mocked(applicationApi.addNote).mockResolvedValue({
      id: 'note-3',
      application_id: 'app-1',
      content: 'Called HR',
      created_at: '2026-08-21T15:00:00Z',
      updated_at: null,
    })
    renderNotes()
    fireEvent.change(screen.getByPlaceholderText(/What happened/), {
      target: { value: 'Called HR' },
    })
    fireEvent.click(screen.getByRole('button', { name: /add note/i }))
    await waitFor(() => {
      expect(applicationApi.addNote).toHaveBeenCalledWith('app-1', { content: 'Called HR' })
    })
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/What happened/)).toHaveValue('')
    })
  })

  it('submits with Enter without shift', async () => {
    vi.mocked(applicationApi.addNote).mockResolvedValue({
      id: 'note-3',
      application_id: 'app-1',
      content: 'Called HR',
      created_at: null,
      updated_at: null,
    })
    renderNotes()
    const textarea = screen.getByPlaceholderText(/What happened/)
    fireEvent.change(textarea, { target: { value: 'Called HR' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    await waitFor(() => {
      expect(applicationApi.addNote).toHaveBeenCalled()
    })
  })

  it('does not submit with Shift+Enter', () => {
    renderNotes()
    const textarea = screen.getByPlaceholderText(/What happened/)
    fireEvent.change(textarea, { target: { value: 'multi' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })
    expect(applicationApi.addNote).not.toHaveBeenCalled()
  })

  it('deletes a note', async () => {
    vi.mocked(applicationApi.deleteNote).mockResolvedValue(undefined)
    renderNotes()
    fireEvent.click(screen.getAllByLabelText('Delete note')[0])
    await waitFor(() => {
      expect(applicationApi.deleteNote).toHaveBeenCalledWith('note-2')
    })
  })
})
