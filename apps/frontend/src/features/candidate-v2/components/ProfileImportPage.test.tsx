import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { toast } from 'sonner'
import { ProfileImportPage } from './ProfileImportPage'
import type { CandidateAnalyzeResult, CandidateSource } from '@/entities/candidate/types'

const sources: CandidateSource[] = [
  {
    id: 'src-2',
    profile_id: 'profile-1',
    source_type: 'resume',
    version: 2,
    status: 'pending',
    error: null,
    raw_text: 'Senior Engineer resume text with PII removed',
    processed_at: null,
    created_at: '2026-08-01T10:00:00',
    updated_at: '2026-08-01T10:05:00',
  },
  {
    id: 'src-1',
    profile_id: 'profile-1',
    source_type: 'linkedin',
    version: 1,
    status: 'processed',
    error: null,
    raw_text: 'LinkedIn profile text',
    processed_at: '2026-07-30T09:00:00',
    created_at: '2026-07-30T08:00:00',
    updated_at: '2026-07-30T09:00:00',
  },
]

let analyzeResult: CandidateAnalyzeResult | undefined
const analyzeMutate = vi.fn((_args: undefined, opts?: { onSuccess?: (r: CandidateAnalyzeResult) => void }) => {
  if (analyzeResult && opts?.onSuccess) opts.onSuccess(analyzeResult)
})

vi.mock('@/entities/candidate/hooks', () => ({
  useCandidateProfileQuery: () => ({ data: null, isLoading: false, isError: false }),
  useCandidateSourcesQuery: () => ({ data: { items: sources }, isLoading: false, isError: false }),
  useCandidateVersionsQuery: () => ({ data: { items: [] }, isLoading: false, isError: false }),
  useAnalyzeProfileMutation: () => ({ mutate: analyzeMutate, isPending: false, error: null }),
  useUploadSourceMutation: () => ({ mutate: vi.fn(), isPending: false, variables: null }),
}))

vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}))

vi.mock('@/entities/processing/api', () => ({
  processingApi: {
    queue: vi.fn().mockResolvedValue({ processing: [], queued: [], failed: [] }),
    get: vi.fn().mockResolvedValue({ workflow: null }),
  },
}))

vi.mock('@/shared/api/processingEvents', () => ({
  subscribeProcessingEvents: vi.fn(() => vi.fn()),
}))

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

function renderPage() {
  return render(<ProfileImportPage />, { wrapper })
}

beforeEach(() => {
  vi.clearAllMocks()
  analyzeResult = undefined
})

describe('ProfileImportPage sources', () => {
  it('renders a relative last-updated time for the resume source card', () => {
    renderPage()
    expect(screen.getAllByText('Last updated').length).toBe(2)
    expect(screen.getByText(/v2/)).toBeInTheDocument()
  })

  it('opens the source content dialog when View is clicked on a source card', async () => {
    const user = userEvent.setup()
    renderPage()
    const viewButtons = screen.getAllByRole('button', { name: /view/i })
    await user.click(viewButtons[0])
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/Senior Engineer resume text with PII removed/)).toBeInTheDocument()
  })

  it('shows last-updated and view for every source in the Review tab', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.click(screen.getByRole('tab', { name: /review/i }))
    expect(screen.getByText('resume v2')).toBeInTheDocument()
    expect(screen.getByText('linkedin v1')).toBeInTheDocument()
    const viewButtons = screen.getAllByRole('button', { name: /^view /i })
    expect(viewButtons.length).toBe(2)
  })

  it('renders source raw_text in the dialog from the Review tab', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.click(screen.getByRole('tab', { name: /review/i }))
    await user.click(screen.getByRole('button', { name: 'View linkedin v1' }))
    expect(screen.getByText('LinkedIn profile text')).toBeInTheDocument()
  })

  it('opens the candidate processing drawer from the Analyze card', async () => {
    const user = userEvent.setup()
    renderPage()
    await user.click(screen.getByRole('button', { name: /processing/i }))
    expect(await screen.findByText('Processing Queue')).toBeInTheDocument()
    expect(screen.getAllByText('No candidate analysis in this state.').length).toBe(3)
  })
})

describe('ProfileImportPage analyze', () => {
  it('shows an info toast and stays on Sources when there is nothing new to process', async () => {
    analyzeResult = { execution_id: null, status: 'noop', reason: 'no_new_sources' }
    const user = userEvent.setup()
    renderPage()
    await user.click(screen.getByRole('button', { name: /analyze profile/i }))
    expect(toast.info).toHaveBeenCalledWith(
      'No new resume/LinkedIn version to process — save a new version first'
    )
    expect(screen.getByRole('tab', { name: /review/i })).not.toHaveAttribute('data-state', 'active')
    expect(screen.getByRole('tab', { name: /sources/i })).toHaveAttribute('data-state', 'active')
  })

  it('shows queued toast and switches to Review when an execution is created', async () => {
    analyzeResult = { execution_id: 'exec-1', status: 'queued' }
    const user = userEvent.setup()
    renderPage()
    await user.click(screen.getByRole('button', { name: /analyze profile/i }))
    expect(toast.success).toHaveBeenCalledWith('Profile analysis queued')
    expect(screen.getByRole('tab', { name: /review/i })).toHaveAttribute('data-state', 'active')
  })
})
