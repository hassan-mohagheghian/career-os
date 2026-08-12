import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApplicationTracker } from './ApplicationTracker'
import { applicationApi } from '@/entities/application/api'
import type { ApplicationDetail } from '@/entities/application/types'

vi.mock('@/entities/application/api', () => ({
  applicationApi: {
    create: vi.fn(),
    update: vi.fn(),
    addFollowUp: vi.fn(),
    updateFollowUp: vi.fn(),
    deleteFollowUp: vi.fn(),
  },
}))

const sampleApplication: ApplicationDetail = {
  id: 'app-1',
  job_id: 'job-1',
  status: 'recommended',
  applied_at: null,
  created_at: null,
  updated_at: null,
  follow_ups: [
    {
      id: 'fu-1',
      application_id: 'app-1',
      scheduled_at: '2026-09-01T09:00:00Z',
      note: 'Follow up after interview',
      completed_at: null,
      created_at: null,
      updated_at: null,
    },
  ],
  documents: [],
}

beforeEach(() => {
  vi.clearAllMocks()
})

function renderTracker(application: ApplicationDetail = sampleApplication) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <ApplicationTracker application={application} />
    </QueryClientProvider>
  )
}

describe('ApplicationTracker', () => {
  it('renders the current status and applied date controls', () => {
    renderTracker()
    expect(screen.getByLabelText('Status')).toBeInTheDocument()
    expect(screen.getByLabelText('Applied at')).toBeInTheDocument()
  })

  it('renders follow-ups and toggles completion', async () => {
    renderTracker()
    expect(screen.getByText('Follow up after interview')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Mark done' }))
    await waitFor(() => {
      expect(applicationApi.updateFollowUp).toHaveBeenCalledWith('fu-1', { completed: true })
    })
  })

  it('deletes a follow-up', async () => {
    renderTracker()
    fireEvent.click(screen.getByRole('button', { name: 'Delete follow-up' }))
    await waitFor(() => {
      expect(applicationApi.deleteFollowUp).toHaveBeenCalledWith('fu-1')
    })
  })

  it('adds a follow-up with note and scheduled date', async () => {
    renderTracker({ ...sampleApplication, follow_ups: [] })

    fireEvent.change(screen.getByPlaceholderText(/Note/), { target: { value: 'Send thank-you email' } })
    fireEvent.change(document.getElementById('follow-up-scheduled-at')!, {
      target: { value: '2026-09-15' },
    })

    const addButton = screen.getByRole('button', { name: /Add/ })
    fireEvent.click(addButton)

    await waitFor(() => {
      expect(applicationApi.addFollowUp).toHaveBeenCalledWith('app-1', {
        note: 'Send thank-you email',
        scheduled_at: '2026-09-15',
      })
    })
  })

  it('shows an empty follow-ups message', () => {
    renderTracker({ ...sampleApplication, follow_ups: [] })
    expect(screen.getByText('No follow-ups scheduled yet.')).toBeInTheDocument()
  })
})
