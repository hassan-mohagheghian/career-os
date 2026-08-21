import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApplicationDocuments } from './ApplicationDocuments'
import type { ApplicationDetail } from '@/entities/application/types'

vi.mock('@/entities/application/hooks', () => ({
  useUpdateDocumentMutation: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteDocumentMutation: () => ({ mutate: vi.fn(), isPending: false }),
  useGenerateDocumentMutation: () => ({ mutate: vi.fn(), isPending: false }),
  useDownloadDocumentPdf: () => ({ mutate: vi.fn(), isPending: false }),
}))

vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => (
    <div data-testid="markdown-content">{children}</div>
  ),
}))

const application: ApplicationDetail = {
  id: 'app-1',
  job_id: 'job-1',
  status: 'seen',
  applied_at: null,
  created_at: null,
  updated_at: null,
  status_timeline: [],
  follow_ups: [],
  notes: [],
  documents: [
    {
      id: 'doc-1',
      application_id: 'app-1',
      document_type: 'tailored_resume',
      version: 1,
      content: '# Hassan Khaled\n\nSenior Backend Engineer',
      created_at: null,
      updated_at: null,
    },
  ],
}

function renderDocs() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <ApplicationDocuments
        application={application}
        generatingType={null}
        onGenerate={vi.fn()}
      />
    </QueryClientProvider>
  )
}

describe('ApplicationDocuments', () => {
  it('renders a Preview button and opens the A4 preview dialog', () => {
    renderDocs()

    const previewButton = screen.getByRole('button', { name: 'Preview' })
    expect(previewButton).toBeInTheDocument()

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    fireEvent.click(previewButton)

    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(screen.getByText(/Tailored Resume.*Preview/i)).toBeInTheDocument()
    expect(screen.getByTestId('markdown-content')).toHaveTextContent(
      '# Hassan Khaled'
    )
  })

  it('does not render a Preview button when there is no document', () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <ApplicationDocuments
          application={{ ...application, documents: [] }}
          generatingType={null}
          onGenerate={vi.fn()}
        />
      </QueryClientProvider>
    )

    expect(screen.queryByRole('button', { name: 'Preview' })).not.toBeInTheDocument()
  })

  it('renders a Download as PDF button when a document exists', () => {
    renderDocs()

    const pdfButton = screen.getByRole('button', { name: 'Download as PDF' })
    expect(pdfButton).toBeInTheDocument()
  })

  it('does not render a Download as PDF button when there is no document', () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <ApplicationDocuments
          application={{ ...application, documents: [] }}
          generatingType={null}
          onGenerate={vi.fn()}
        />
      </QueryClientProvider>
    )

    expect(screen.queryByRole('button', { name: 'Download as PDF' })).not.toBeInTheDocument()
  })
})
