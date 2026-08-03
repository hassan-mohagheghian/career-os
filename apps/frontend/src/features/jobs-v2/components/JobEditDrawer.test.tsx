import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { JobEditDrawer } from './JobEditDrawer'
import { jobApi } from '@/entities/job/api'

vi.mock('@/entities/job/api', () => ({
  jobApi: {
    getDetail: vi.fn(),
    updateJob: vi.fn(),
  },
}))

const sampleDetail = {
  id: 'job-1',
  title: 'Staff Engineer',
  company_name: 'Acme GmbH',
  role: 'Staff',
  location: 'Berlin',
  work_type: 'Hybrid',
  employment_type: 'Full-time',
  salary: '100k',
  visa: 'Strong',
  url: 'https://example.com/job',
  status: 'imported',
  scores: { overall: 90, fit: 85, success: 88 },
  latest_processing_execution: null,
  description: 'Original desc',
  notes: [],
  links: [],
  updated_at: null,
  created_at: null,
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(jobApi.getDetail).mockResolvedValue(sampleDetail as any)
  vi.mocked(jobApi.updateJob).mockResolvedValue(sampleDetail as any)
})

function renderEdit(jobId: string | null, onChange: (id: string | null) => void = vi.fn()) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <JobEditDrawer jobId={jobId} onOpenChange={onChange} />
    </QueryClientProvider>
  )
}

describe('JobEditDrawer', () => {
  it('prefills fields from job detail', async () => {
    renderEdit('job-1')
    await screen.findByDisplayValue('Staff Engineer')
    expect(screen.getByDisplayValue('Acme GmbH')).toBeInTheDocument()
    expect(screen.getByDisplayValue('https://example.com/job')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Original desc')).toBeInTheDocument()
  })

  it('submits updateJob with changed payload on save', async () => {
    renderEdit('job-1')
    const titleInput = await screen.findByDisplayValue('Staff Engineer')
    fireEvent.change(titleInput, { target: { value: 'Principal Engineer' } })
    fireEvent.click(screen.getByRole('button', { name: /save/i }))

    await waitFor(() => {
      expect(jobApi.updateJob).toHaveBeenCalledWith('job-1', expect.objectContaining({
        title: 'Principal Engineer',
        url: 'https://example.com/job',
      }))
    })
  })

  it('shows validation error for invalid url', async () => {
    renderEdit('job-1')
    const urlInput = await screen.findByDisplayValue('https://example.com/job')
    fireEvent.change(urlInput, { target: { value: 'not-a-url' } })
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    const messages = await screen.findAllByText(/URL must start with/)
    expect(messages.length).toBeGreaterThan(0)
    expect(jobApi.updateJob).not.toHaveBeenCalled()
  })

  it('closes drawer via Cancel without saving', async () => {
    const onChange = vi.fn()
    renderEdit('job-1', onChange)
    await screen.findByDisplayValue('Staff Engineer')
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onChange).toHaveBeenCalledWith(null)
    expect(jobApi.updateJob).not.toHaveBeenCalled()
  })

  it('prefills notes and links from detail', async () => {
    vi.mocked(jobApi.getDetail).mockResolvedValue({
      ...sampleDetail,
      notes: [{ content: 'existing note' }],
      links: [{ url: 'https://existing.example', title: 'Ref' }],
    } as any)
    renderEdit('job-1')
    expect(await screen.findByText('existing note')).toBeInTheDocument()
    const link = await screen.findByText('https://existing.example')
    expect(link).toHaveAttribute('href', 'https://existing.example')
  })

  it('adds a note before saving', async () => {
    const onChange = vi.fn()
    renderEdit('job-1', onChange)
    await screen.findByDisplayValue('Staff Engineer')
    const noteDraft = screen.getByPlaceholderText('Add a note...')
    fireEvent.change(noteDraft, { target: { value: 'new note content' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add note' }))
    expect(screen.getByText('new note content')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    await waitFor(() => {
      expect(jobApi.updateJob).toHaveBeenCalledWith('job-1', expect.objectContaining({
        notes: expect.arrayContaining([{ content: 'new note content' }]),
      }))
    })
  })

  it('adds a link before saving', async () => {
    const onChange = vi.fn()
    renderEdit('job-1', onChange)
    await screen.findByDisplayValue('Staff Engineer')
    const urlInput = screen.getByPlaceholderText('Link URL (https://...)')
    fireEvent.change(urlInput, { target: { value: 'https://newlink.example' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add link' }))
    expect(screen.getByText('https://newlink.example')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    await waitFor(() => {
      expect(jobApi.updateJob).toHaveBeenCalledWith('job-1', expect.objectContaining({
        links: expect.arrayContaining([{ url: 'https://newlink.example', title: null }]),
      }))
    })
  })
})