import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import JobsPage from './JobsPage'

vi.mock('@/shared/ui/tooltip', () => ({
  TooltipProvider: ({ children }: any) => <>{children}</>,
  Tooltip: ({ children }: any) => <>{children}</>,
  TooltipTrigger: ({ children, asChild, ...props }: any) => <span {...props}>{children}</span>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
}))

vi.mock('@/shared/ui/select', () => ({
  Select: ({ children }: any) => <div>{children}</div>,
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children }: any) => <div>{children}</div>,
  SelectTrigger: ({ children }: any) => <div>{children}</div>,
  SelectValue: () => null,
}))

const defaultProps = {
  pending: [],
  jobs: [],
  filteredJobs: [],
  jobsTotal: 0,
  filteredJobsCount: 0,
  sortBy: 'created_at',
  setSortBy: vi.fn(),
  sortDir: 'desc',
  setSortDir: vi.fn(),
  filterTech: '',
  setFilterTech: vi.fn(),
  filterCities: [],
  setFilterCities: vi.fn(),
  filterCompanies: [],
  setFilterCompanies: vi.fn(),
  filterMatches: [],
  setFilterMatches: vi.fn(),
  filterWorkTypes: [],
  setFilterWorkTypes: vi.fn(),
  filterEmploymentTypes: [],
  setFilterEmploymentTypes: vi.fn(),
  filterResponseStatus: [],
  setFilterResponseStatus: vi.fn(),
  filterApplied: null,
  setFilterApplied: vi.fn(),
  filterScores: [],
  setFilterScores: vi.fn(),
  allCities: [],
  allCompanies: [],
  activeFilterCount: 0,
  loadingMore: false,
  jobsScrollRef: { current: null },
  jobsSentinelRef: { current: null },
  rescoreJob: vi.fn(),
  deleteJob: vi.fn(),
  requeueJob: vi.fn(),
  openDrawer: vi.fn(),
  refreshJobs: vi.fn(),
  clearFilters: vi.fn(),
  loadMoreJobs: vi.fn(),
  onOpenCompany: vi.fn(),
  openWorkflow: vi.fn(),
  onOpenQueueDrawer: vi.fn(),
  onOpenAddJobDrawer: vi.fn(),
}

describe('JobsPage', () => {
  it('renders Jobs section', () => {
    render(<JobsPage {...defaultProps} />)
    expect(screen.getByText('Jobs List')).toBeInTheDocument()
  })

  it('renders all jobs loaded state', () => {
    render(<JobsPage {...defaultProps} jobsTotal={5} filteredJobsCount={5} />)
    expect(screen.getByText('All 5 jobs loaded')).toBeInTheDocument()
  })

  it('renders job cards when jobs exist', () => {
    const jobs = [
      { num: 1, company: 'Acme', role: 'Engineer', location: 'Berlin', score: 'A', match: 'High', overall_score: 85, fit_score: 78, success_score: 90 },
    ]
    render(<JobsPage {...defaultProps} jobs={jobs} filteredJobs={jobs} jobsTotal={1} filteredJobsCount={1} />)
    expect(screen.getByText('Acme')).toBeInTheDocument()
  })

  it('renders Clear all button when filters active', () => {
    render(<JobsPage {...defaultProps} activeFilterCount={3} />)
    expect(screen.getByText('Clear all')).toBeInTheDocument()
  })

  it('renders score count badge', () => {
    render(<JobsPage {...defaultProps} jobsTotal={5} filteredJobsCount={3} />)
    expect(screen.getByText('3/5')).toBeInTheDocument()
  })
})
