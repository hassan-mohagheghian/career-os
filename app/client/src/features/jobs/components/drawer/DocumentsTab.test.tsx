import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import DocumentsTab from './DocumentsTab'

vi.mock('@/shared/hooks', () => ({
  useLocalHistory: () => ({ items: [], refresh: vi.fn() }),
}))

const mockJob = { num: 1, role: 'Senior Engineer', company_name: 'TechCorp' }

describe('DocumentsTab', () => {
  it('renders resume and cover letter tabs', () => {
    render(<DocumentsTab job={mockJob} resume={null} coverLetter={null} activeGens={{}} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} />)
    expect(screen.getAllByText(/Resume/).length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText(/Cover Letter/).length).toBeGreaterThanOrEqual(1)
  })

  it('shows no resume generated message', () => {
    render(<DocumentsTab job={mockJob} resume={null} coverLetter={null} activeGens={{}} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} />)
    expect(screen.getByText('No resume generated yet')).toBeInTheDocument()
  })

  it('renders resume preview when resume exists', () => {
    render(<DocumentsTab job={mockJob} resume={{ content: '<p>My resume</p>' }} coverLetter={null} activeGens={{}} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} />)
    expect(screen.getByText('Regenerate')).toBeInTheDocument()
  })

  it('renders Generate button when no resume', () => {
    render(<DocumentsTab job={mockJob} resume={null} coverLetter={null} activeGens={{}} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} />)
    expect(screen.getByText('Generate')).toBeInTheDocument()
  })

  it('renders history section', () => {
    render(<DocumentsTab job={mockJob} resume={null} coverLetter={null} activeGens={{}} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} />)
    expect(screen.getByText('History')).toBeInTheDocument()
  })

  it('renders generation progress when resume generating', () => {
    render(<DocumentsTab job={mockJob} resume={null} coverLetter={null} activeGens={{ resume: { running: true, step: 1 } }} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} />)
    expect(screen.getByText('Generating Resume')).toBeInTheDocument()
  })

  it('renders cover letter generation progress', () => {
    render(<DocumentsTab job={mockJob} resume={null} coverLetter={null} activeGens={{ cover: { running: true, step: 1 } }} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} />)
    expect(screen.getByText('Cover Letter')).toBeInTheDocument()
  })
})
