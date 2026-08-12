import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApplicationWorkspace } from './ApplicationWorkspace'
import { jobApi } from '@/entities/job/api'
import { applicationApi } from '@/entities/application/api'
import { roadmapApi } from '@/entities/roadmap/api'
import type { JobDetail } from '@/entities/job/types'
import type { ApplicationDetail } from '@/entities/application/types'

vi.mock('@/entities/job/api', () => ({
  jobApi: { getDetail: vi.fn() },
}))

vi.mock('@/entities/application/api', () => ({
  applicationApi: {
    getByJob: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    addFollowUp: vi.fn(),
    updateFollowUp: vi.fn(),
    deleteFollowUp: vi.fn(),
    generateRoadmap: vi.fn(),
    generateDocument: vi.fn(),
    updateDocument: vi.fn(),
    deleteDocument: vi.fn(),
  },
}))

vi.mock('@/entities/roadmap/api', () => ({
  roadmapApi: {
    getByApplication: vi.fn(),
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
    addMilestone: vi.fn(),
    updateMilestone: vi.fn(),
    removeMilestone: vi.fn(),
    addTask: vi.fn(),
    updateTask: vi.fn(),
    removeTask: vi.fn(),
    addNote: vi.fn(),
    removeNote: vi.fn(),
    addResource: vi.fn(),
    updateResource: vi.fn(),
    removeResource: vi.fn(),
    linkSkill: vi.fn(),
    removeSkillLink: vi.fn(),
  },
}))

vi.mock('@/shared/api/processingEvents', () => ({
  subscribeProcessingEvents: () => () => {},
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

const sampleJob: JobDetail = {
  id: 'job-1',
  title: 'Staff Engineer',
  company_name: 'Acme GmbH',
  company_id: 'company-1',
  role: 'Staff',
  location: 'Berlin',
  work_types: ['Hybrid'],
  employment_types: ['Full-time'],
  salary: '100k',
  visa: 'Strong',
  url: 'https://example.com/job',
  status: 'imported',
  scores: { overall: 90, fit: 85, success: 88 },
  latest_processing_execution: null,
  description: 'A great role.',
  notes: [],
  links: [],
  analysis: null,
  related_companies: [],
  updated_at: null,
  created_at: null,
}

const sampleApplication: ApplicationDetail = {
  id: 'app-1',
  job_id: 'job-1',
  status: 'recommended',
  applied_at: null,
  created_at: null,
  updated_at: null,
  follow_ups: [],
  documents: [],
}

const noRoadmap = { status: 404, message: 'no roadmap' }

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(jobApi.getDetail).mockResolvedValue(sampleJob)
  vi.mocked(roadmapApi.getByApplication).mockRejectedValue(noRoadmap)
})

function renderWorkspace(application: ApplicationDetail | null = sampleApplication) {
  vi.mocked(applicationApi.getByJob).mockImplementation(() =>
    application
      ? Promise.resolve(application)
      : Promise.reject({ status: 404, message: 'not found' })
  )
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <ApplicationWorkspace jobId="job-1" />
    </QueryClientProvider>
  )
}

describe('ApplicationWorkspace', () => {
  it('renders the workspace header and sections for an existing application', async () => {
    renderWorkspace()

    await waitFor(() => expect(screen.getByText('Staff Engineer')).toBeInTheDocument())
    expect(screen.getByText('Back to Job')).toBeInTheDocument()
    expect(screen.getByText('Application')).toBeInTheDocument()
    expect(screen.getByText('Roadmap')).toBeInTheDocument()
    expect(screen.getByText('Documents')).toBeInTheDocument()
  })

  it('shows the empty state and creates an application', async () => {
    renderWorkspace(null)

    await waitFor(() => expect(screen.getByText('No application yet')).toBeInTheDocument())
    vi.mocked(applicationApi.create).mockResolvedValue(sampleApplication)

    fireEvent.click(screen.getByRole('button', { name: /Create Application/ }))
    await waitFor(() => {
      expect(applicationApi.create).toHaveBeenCalledWith('job-1')
    })
  })

  it('renders the roadmap generate button without a roadmap', async () => {
    renderWorkspace()

    await waitFor(() => expect(screen.getByText('Roadmap')).toBeInTheDocument())
    const section = screen.getByText('Roadmap').closest('div')!
    expect(within(section).getByText(/No roadmap yet/)).toBeInTheDocument()
    fireEvent.click(within(section).getByRole('button', { name: /Generate roadmap/ }))
    await waitFor(() => {
      expect(applicationApi.generateRoadmap).toHaveBeenCalledWith('app-1')
    })
  })

  it('renders a ready roadmap with view + progress', async () => {
    vi.mocked(roadmapApi.getByApplication).mockResolvedValue({
      id: 'rm-1',
      title: 'Kafka Roadmap',
      description: '',
      goal_type: 'JOB',
      source: 'APPLICATION',
      application_id: 'app-1',
      status: 'ACTIVE',
      progress: { completed_tasks: 1, total_tasks: 4, overall_percent: 25, milestone_progress: [] },
      goal: { id: 'g-1', roadmap_id: 'rm-1', type: 'JOB', title: 'Get the job', description: '', target_job_id: 'job-1', target_company_id: null, target_skill_id: null },
      milestones: [
        {
          id: 'ms-1',
          roadmap_id: 'rm-1',
          position: 0,
          title: 'Basics',
          description: '',
          status: 'IN_PROGRESS',
          priority: 'HIGH',
          tasks: [
            { id: 't-1', milestone_id: 'ms-1', position: 0, title: 'Read docs', description: '', status: 'COMPLETED', priority: 'MEDIUM', estimated_effort: null, success_criteria: null, completed_at: null, skills: [] },
            { id: 't-2', milestone_id: 'ms-1', position: 1, title: 'Write demo', description: '', status: 'NOT_STARTED', priority: 'MEDIUM', estimated_effort: null, success_criteria: null, completed_at: null, skills: [] },
          ],
          skills: [],
        },
        {
          id: 'ms-2',
          roadmap_id: 'rm-1',
          position: 1,
          title: 'Apply',
          description: '',
          status: 'NOT_STARTED',
          priority: 'CRITICAL',
          tasks: [],
          skills: [],
        },
      ],
      notes: [],
      resources: [],
      created_at: null,
      updated_at: null,
    })
    renderWorkspace()

    await waitFor(() => expect(screen.getByText('Kafka Roadmap')).toBeInTheDocument())
    const section = screen.getByText('Roadmap').closest('div')!
    expect(within(section).getByRole('button', { name: /View roadmap/ })).toBeInTheDocument()
    expect(within(section).getByText('1/4 tasks done')).toBeInTheDocument()
    expect(within(section).getByText('25%')).toBeInTheDocument()

    expect(within(section).getByText('Milestones')).toBeInTheDocument()
    expect(within(section).getByText('Basics')).toBeInTheDocument()
    expect(within(section).getByText('IN PROGRESS')).toBeInTheDocument()
    expect(within(section).getByText('HIGH')).toBeInTheDocument()
    expect(within(section).getByText('1/2')).toBeInTheDocument()
    expect(within(section).getByText('Apply')).toBeInTheDocument()
    expect(within(section).getByText('CRITICAL')).toBeInTheDocument()
    expect(within(section).getByText('0/0')).toBeInTheDocument()
  })

  it('renders document generate buttons without documents', async () => {
    renderWorkspace()

    await waitFor(() => expect(screen.getByText('Documents')).toBeInTheDocument())
    const section = screen.getByText('Documents').closest('div')!
    expect(within(section).getByText('Tailored Resume')).toBeInTheDocument()
    expect(within(section).getByText('Cover Letter')).toBeInTheDocument()
  })
})
