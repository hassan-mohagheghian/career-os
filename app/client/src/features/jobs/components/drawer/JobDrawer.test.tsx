import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import JobDrawer from './JobDrawer'

vi.mock('@/shared/hooks', () => ({
  useLocalHistory: () => ({ items: [], refresh: vi.fn() }),
}))

const mockDrawer = {
  job: {
    num: 1,
    role: 'Senior Engineer',
    company: 'TechCorp',
    location: 'Berlin',
    score: 'A',
    overall_score: 85,
    fit_score: 80,
    success_score: 90,
    match: 'High',
    url: 'https://example.com/job',
    work_type: 'remote',
  },
  summary: { summary: 'Great role' },
}

describe('JobDrawer', () => {
  it('returns null when drawer is null', () => {
    const { container } = render(<JobDrawer drawer={null} drawerTab="details" activeGens={{}} companies={[]} onClose={vi.fn()} onSetDrawerTab={vi.fn()} onRescoreJob={vi.fn()} onRequeueJob={vi.fn()} onUpdateJob={vi.fn()} onSetToast={vi.fn()} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} onLinkCompany={vi.fn()} onOpenCompany={vi.fn()} onNavigateToCompany={vi.fn()} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders company name when drawer provided', () => {
    render(<JobDrawer drawer={mockDrawer} drawerTab="details" activeGens={{}} companies={[]} onClose={vi.fn()} onSetDrawerTab={vi.fn()} onRescoreJob={vi.fn()} onRequeueJob={vi.fn()} onUpdateJob={vi.fn()} onSetToast={vi.fn()} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} onLinkCompany={vi.fn()} onOpenCompany={vi.fn()} onNavigateToCompany={vi.fn()} />)
    expect(screen.getByText('TechCorp')).toBeInTheDocument()
  })

  it('renders role', () => {
    render(<JobDrawer drawer={mockDrawer} drawerTab="details" activeGens={{}} companies={[]} onClose={vi.fn()} onSetDrawerTab={vi.fn()} onRescoreJob={vi.fn()} onRequeueJob={vi.fn()} onUpdateJob={vi.fn()} onSetToast={vi.fn()} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} onLinkCompany={vi.fn()} onOpenCompany={vi.fn()} onNavigateToCompany={vi.fn()} />)
    expect(screen.getByText('Senior Engineer')).toBeInTheDocument()
  })

  it('renders tabs', () => {
    render(<JobDrawer drawer={mockDrawer} drawerTab="details" activeGens={{}} companies={[]} onClose={vi.fn()} onSetDrawerTab={vi.fn()} onRescoreJob={vi.fn()} onRequeueJob={vi.fn()} onUpdateJob={vi.fn()} onSetToast={vi.fn()} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} onLinkCompany={vi.fn()} onOpenCompany={vi.fn()} onNavigateToCompany={vi.fn()} />)
    expect(screen.getByText('Details')).toBeInTheDocument()
    expect(screen.getByText('Structured')).toBeInTheDocument()
    expect(screen.getByText('Summary')).toBeInTheDocument()
    expect(screen.getByText('Company')).toBeInTheDocument()
    expect(screen.getByText('Documents')).toBeInTheDocument()
  })

  it('renders Open Job Page button', () => {
    render(<JobDrawer drawer={mockDrawer} drawerTab="details" activeGens={{}} companies={[]} onClose={vi.fn()} onSetDrawerTab={vi.fn()} onRescoreJob={vi.fn()} onRequeueJob={vi.fn()} onUpdateJob={vi.fn()} onSetToast={vi.fn()} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} onLinkCompany={vi.fn()} onOpenCompany={vi.fn()} onNavigateToCompany={vi.fn()} />)
    expect(screen.getByText('Open Job Page')).toBeInTheDocument()
  })

  it('renders Copy URL button', () => {
    render(<JobDrawer drawer={mockDrawer} drawerTab="details" activeGens={{}} companies={[]} onClose={vi.fn()} onSetDrawerTab={vi.fn()} onRescoreJob={vi.fn()} onRequeueJob={vi.fn()} onUpdateJob={vi.fn()} onSetToast={vi.fn()} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} onLinkCompany={vi.fn()} onOpenCompany={vi.fn()} onNavigateToCompany={vi.fn()} />)
    expect(screen.getByText('Copy URL')).toBeInTheDocument()
  })

  it('renders match badge', () => {
    render(<JobDrawer drawer={mockDrawer} drawerTab="details" activeGens={{}} companies={[]} onClose={vi.fn()} onSetDrawerTab={vi.fn()} onRescoreJob={vi.fn()} onRequeueJob={vi.fn()} onUpdateJob={vi.fn()} onSetToast={vi.fn()} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} onLinkCompany={vi.fn()} onOpenCompany={vi.fn()} onNavigateToCompany={vi.fn()} />)
    expect(screen.getByText('High')).toBeInTheDocument()
  })

  it('renders location', () => {
    render(<JobDrawer drawer={mockDrawer} drawerTab="details" activeGens={{}} companies={[]} onClose={vi.fn()} onSetDrawerTab={vi.fn()} onRescoreJob={vi.fn()} onRequeueJob={vi.fn()} onUpdateJob={vi.fn()} onSetToast={vi.fn()} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} onLinkCompany={vi.fn()} onOpenCompany={vi.fn()} onNavigateToCompany={vi.fn()} />)
    expect(screen.getByText('Berlin')).toBeInTheDocument()
  })

  it('renders work type', () => {
    render(<JobDrawer drawer={mockDrawer} drawerTab="details" activeGens={{}} companies={[]} onClose={vi.fn()} onSetDrawerTab={vi.fn()} onRescoreJob={vi.fn()} onRequeueJob={vi.fn()} onUpdateJob={vi.fn()} onSetToast={vi.fn()} onGenerateResume={vi.fn()} onGenerateCover={vi.fn()} onCancelGeneration={vi.fn()} onLinkCompany={vi.fn()} onOpenCompany={vi.fn()} onNavigateToCompany={vi.fn()} />)
    expect(screen.getAllByText('remote').length).toBeGreaterThan(0)
  })
})
