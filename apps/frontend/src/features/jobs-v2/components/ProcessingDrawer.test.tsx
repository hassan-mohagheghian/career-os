import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { TooltipProvider } from '@/shared/ui/tooltip'
import { ProcessingDrawer } from './ProcessingDrawer'
import { processingApi } from '@/entities/processing/api'
import { subscribeProcessingEvents } from '@/shared/api/processingEvents'

vi.mock('@/shared/ui/sheet', () => ({
  Sheet: ({ children }: any) => <div>{children}</div>,
  SheetContent: ({ children }: any) => <div>{children}</div>,
  SheetHeader: ({ children }: any) => <div>{children}</div>,
  SheetTitle: ({ children }: any) => <div>{children}</div>,
}))
vi.mock('@/shared/ui/scroll-area', () => ({
  ScrollArea: ({ children }: any) => <div>{children}</div>,
}))
vi.mock('@/entities/processing/api', () => ({
  processingApi: {
    queue: vi.fn(),
    get: vi.fn(),
    start: vi.fn(),
    cancel: vi.fn(),
    retry: vi.fn(),
    removeQueueEntry: vi.fn(),
  },
}))
vi.mock('@/shared/api/processingEvents', () => ({
  subscribeProcessingEvents: vi.fn(() => vi.fn()),
}))

const baseEntry = {
  execution_id: 'exec-1',
  job_id: 'job-1',
  title: 'Senior Backend Engineer',
  url: 'https://example.com/job',
  links: [],
  status: 'running',
  current_step: null,
  progress: null,
  error: null,
  failed_step: null,
  started_at: null,
  finished_at: null,
}

function mockSnapshot(overrides: any = {}) {
  vi.mocked(processingApi.queue).mockResolvedValue({
    processing: [],
    queued: [],
    failed: [],
    ...overrides,
  } as any)
  vi.mocked(processingApi.get).mockResolvedValue({ workflow: null } as any)
  vi.mocked(subscribeProcessingEvents).mockReturnValue(vi.fn())
}

function renderDrawer() {
  return render(
    <TooltipProvider>
      <ProcessingDrawer open onOpenChange={vi.fn()} />
    </TooltipProvider>
  )
}

describe('ProcessingDrawer action buttons', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSnapshot()
  })

  it('renders Cancel for running entries', async () => {
    mockSnapshot({ processing: [{ ...baseEntry, execution_id: 'exec-running' }] })
    renderDrawer()
    const cancel = await screen.findByTitle('Cancel')
    expect(cancel).toBeInTheDocument()
    fireEvent.click(cancel)
    await waitFor(() => {
      expect(processingApi.cancel).toHaveBeenCalledWith('exec-running')
    })
  })

  it('renders Start and Remove for queued entries', async () => {
    mockSnapshot({ queued: [{ ...baseEntry, execution_id: 'exec-queued', status: 'queued' }] })
    renderDrawer()
    const start = await screen.findByTitle('Start')
    const remove = screen.getByTitle('Remove')
    expect(start).toBeInTheDocument()
    expect(remove).toBeInTheDocument()
    fireEvent.click(start)
    await waitFor(() => {
      expect(processingApi.start).toHaveBeenCalledWith('exec-queued')
    })
    fireEvent.click(remove)
    await waitFor(() => {
      expect(processingApi.removeQueueEntry).toHaveBeenCalledWith('exec-queued')
    })
  })

  it('renders Retry and Remove for failed entries', async () => {
    mockSnapshot({ failed: [{ ...baseEntry, execution_id: 'exec-failed', status: 'failed', error: 'boom' }] })
    renderDrawer()
    const retry = await screen.findByTitle('Retry')
    const remove = screen.getByTitle('Remove')
    expect(retry).toBeInTheDocument()
    expect(remove).toBeInTheDocument()
    fireEvent.click(retry)
    await waitFor(() => {
      expect(processingApi.retry).toHaveBeenCalledWith('exec-failed')
    })
  })

  it('reloads snapshot after an action', async () => {
    mockSnapshot({ queued: [{ ...baseEntry, execution_id: 'exec-queued', status: 'queued' }] })
    renderDrawer()
    const start = await screen.findByTitle('Start')
    fireEvent.click(start)
    await waitFor(() => {
      expect(processingApi.start).toHaveBeenCalledWith('exec-queued')
    })
    await waitFor(() => {
      expect(processingApi.queue).toHaveBeenCalled()
    })
  })
})
