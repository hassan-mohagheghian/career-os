import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

const roadmapApiMock = {
  list: vi.fn(),
  get: vi.fn(),
  getByApplication: vi.fn(),
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
}

vi.mock('@/entities/roadmap/api', () => ({
  roadmapApi: roadmapApiMock,
}))

const roadmapDetail = {
  id: 'rm-1',
  title: 'Kafka Roadmap',
  description: 'Master event streaming.',
  goal_type: 'JOB',
  source: 'APPLICATION',
  application_id: 'app-1',
  status: 'ACTIVE',
  progress: { completed_tasks: 1, total_tasks: 4, overall_percent: 25, milestone_progress: [] },
  created_at: null,
  updated_at: null,
  goal: {
    id: 'g-1', roadmap_id: 'rm-1', type: 'JOB', title: 'Land a job', description: '',
    target_job_id: 'job-1', target_company_id: null, target_skill_id: null,
  },
  milestones: [
    {
      id: 'ms-1', roadmap_id: 'rm-1', position: 0, title: 'Basics',
      description: 'Learn the fundamentals', status: 'IN_PROGRESS', priority: 'HIGH',
      skills: [],
      tasks: [
        {
          id: 't-1', milestone_id: 'ms-1', position: 0, title: 'Read docs',
          description: '', status: 'NOT_STARTED', priority: 'MEDIUM',
          estimated_effort: '2h', success_criteria: null, completed_at: null, skills: [],
        },
      ],
    },
  ],
  notes: [],
  resources: [],
}

function renderPage(children: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{children}</QueryClientProvider>)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('MyRoadmapsPage', () => {
  it('renders roadmap cards and empty state actions', async () => {
    roadmapApiMock.list.mockResolvedValue([roadmapDetail])
    const { MyRoadmapsPage } = await import('./MyRoadmapsPage')
    renderPage(<MyRoadmapsPage />)

    await waitFor(() => expect(screen.getByText('Kafka Roadmap')).toBeInTheDocument())
    expect(screen.getByText('My Roadmaps')).toBeInTheDocument()
    expect(screen.getByText('1/4 tasks done')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /New Roadmap/ })).toBeInTheDocument()
  })

  it('creates a roadmap via the dialog', async () => {
    roadmapApiMock.list.mockResolvedValue([])
    roadmapApiMock.create.mockResolvedValue(roadmapDetail)
    const { MyRoadmapsPage } = await import('./MyRoadmapsPage')
    renderPage(<MyRoadmapsPage />)

    await waitFor(() => expect(screen.getByText('No roadmaps yet')).toBeInTheDocument())
    fireEvent.click(screen.getAllByRole('button', { name: /New Roadmap/ })[0])
    await waitFor(() => expect(screen.getAllByText('New Roadmap').length).toBeGreaterThan(0))
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Kafka Roadmap' } })
    fireEvent.click(screen.getByRole('button', { name: /Create/ }))
    await waitFor(() => {
      expect(roadmapApiMock.create).toHaveBeenCalledWith({
        title: 'Kafka Roadmap',
        description: '',
        goal: { type: 'CUSTOM', title: '' },
      })
    })
  })
})

describe('RoadmapDetailPage', () => {
  it('renders goal header, milestones and tasks', async () => {
    roadmapApiMock.get.mockResolvedValue(roadmapDetail)
    const { RoadmapDetailPage } = await import('./RoadmapDetailPage')
    renderPage(<RoadmapDetailPage roadmapId="rm-1" />)

    await waitFor(() => expect(screen.getByText('Kafka Roadmap')).toBeInTheDocument())
    expect(screen.getByText('Master event streaming.')).toBeInTheDocument()
    expect(screen.getByText('Basics')).toBeInTheDocument()
    expect(screen.getByText('Read docs')).toBeInTheDocument()
    expect(screen.getByText('1/4 tasks done')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Add Milestone/ })).toBeInTheDocument()
  })

  it('cycles task status and updates via the API', async () => {
    roadmapApiMock.get.mockResolvedValue(roadmapDetail)
    roadmapApiMock.updateTask.mockResolvedValue({ ...roadmapDetail.milestones[0].tasks[0], status: 'IN_PROGRESS' })
    const { RoadmapDetailPage } = await import('./RoadmapDetailPage')
    renderPage(<RoadmapDetailPage roadmapId="rm-1" />)

    await waitFor(() => expect(screen.getByText('Read docs')).toBeInTheDocument())
    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)
    await waitFor(() => {
      expect(roadmapApiMock.updateTask).toHaveBeenCalledWith('t-1', { status: 'IN_PROGRESS' })
    })
  })

  it('adds a milestone via the dialog', async () => {
    roadmapApiMock.get.mockResolvedValue(roadmapDetail)
    roadmapApiMock.addMilestone.mockResolvedValue({})
    const { RoadmapDetailPage } = await import('./RoadmapDetailPage')
    renderPage(<RoadmapDetailPage roadmapId="rm-1" />)

    await waitFor(() => expect(screen.getByText('Kafka Roadmap')).toBeInTheDocument())
    fireEvent.click(screen.getAllByRole('button', { name: /Add Milestone/ })[0])
    await waitFor(() => expect(screen.getAllByText('Add Milestone').length).toBeGreaterThan(0))
    fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Advanced' } })
    fireEvent.click(screen.getByRole('button', { name: /^Add$/ }))
    await waitFor(() => {
      expect(roadmapApiMock.addMilestone).toHaveBeenCalledWith('rm-1', {
        title: 'Advanced',
        description: '',
        priority: 'MEDIUM',
      })
    })
  })

  it('adds a note to a milestone', async () => {
    roadmapApiMock.get.mockResolvedValue(roadmapDetail)
    roadmapApiMock.addNote.mockResolvedValue({})
    const { RoadmapDetailPage } = await import('./RoadmapDetailPage')
    renderPage(<RoadmapDetailPage roadmapId="rm-1" />)

    await waitFor(() => expect(screen.getByText('Read docs')).toBeInTheDocument())
    fireEvent.click(screen.getAllByRole('button', { name: /^Add$/ })[0])
    await waitFor(() => expect(screen.getByText('Add Note')).toBeInTheDocument())
    fireEvent.change(screen.getByLabelText('Note'), { target: { value: 'Remember Kafka basics' } })
    fireEvent.click(screen.getAllByRole('button', { name: /^Add$/ })[0])
    await waitFor(() => {
      expect(roadmapApiMock.addNote).toHaveBeenCalledWith('rm-1', {
        content: 'Remember Kafka basics',
        milestone_id: 'ms-1',
        task_id: null,
      })
    })
  })

  it('links a skill to a milestone via the popover', async () => {
    roadmapApiMock.get.mockResolvedValue(roadmapDetail)
    roadmapApiMock.linkSkill.mockResolvedValue({})
    const { RoadmapDetailPage } = await import('./RoadmapDetailPage')
    renderPage(<RoadmapDetailPage roadmapId="rm-1" />)

    await waitFor(() => expect(screen.getByText('Read docs')).toBeInTheDocument())
    const linkTrigger = screen.getAllByTitle('Link skill to milestone')[0]
    fireEvent.click(linkTrigger)
    await waitFor(() => expect(screen.getByPlaceholderText('Skill name (e.g. Kafka)')).toBeInTheDocument())
    fireEvent.change(screen.getByPlaceholderText('Skill name (e.g. Kafka)'), { target: { value: 'Kafka' } })
    fireEvent.click(screen.getAllByRole('button', { name: /Link skill/ }).pop()!)
    await waitFor(() => {
      expect(roadmapApiMock.linkSkill).toHaveBeenCalledWith({
        skill_name: 'Kafka',
        milestone_id: 'ms-1',
        task_id: null,
      })
    })
  })
})