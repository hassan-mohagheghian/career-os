import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { roadmapApi } from './api'
import {
  useRoadmapsQuery,
  useRoadmapQuery,
  useRoadmapByApplicationQuery,
  useCreateRoadmapMutation,
  useUpdateRoadmapMutation,
  useDeleteRoadmapMutation,
  useAddMilestoneMutation,
  useUpdateMilestoneMutation,
  useDeleteMilestoneMutation,
  useAddTaskMutation,
  useUpdateTaskMutation,
  useDeleteTaskMutation,
  useAddNoteMutation,
  useDeleteNoteMutation,
  useAddResourceMutation,
  useUpdateResourceMutation,
  useDeleteResourceMutation,
  useLinkSkillMutation,
  useRemoveSkillLinkMutation,
} from './hooks'
import type {
  RoadmapDetail,
  RoadmapMilestone,
  RoadmapNote,
  RoadmapResource,
  RoadmapSkillLink,
  RoadmapSummary,
  RoadmapTask,
} from './types'

vi.mock('./api', () => ({
  roadmapApi: {
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
  },
}))

const mockApi = vi.mocked(roadmapApi)

const progress = { completed_tasks: 1, total_tasks: 2, overall_percent: 50, milestone_progress: [] }

const summary: RoadmapSummary = {
  id: 'rm-1',
  title: 'Kafka Roadmap',
  description: '',
  goal_type: 'JOB',
  source: 'APPLICATION',
  application_id: 'app-1',
  status: 'ACTIVE',
  progress,
  created_at: null,
  updated_at: null,
}

const detail: RoadmapDetail = {
  ...summary,
  goal: null,
  milestones: [],
  notes: [],
  resources: [],
}

const milestone: RoadmapMilestone = {
  id: 'ms-1',
  roadmap_id: 'rm-1',
  position: 0,
  title: 'Basics',
  description: '',
  status: 'NOT_STARTED',
  priority: 'HIGH',
  tasks: [],
  skills: [],
}

const task: RoadmapTask = {
  id: 't-1',
  milestone_id: 'ms-1',
  position: 0,
  title: 'Read docs',
  description: '',
  status: 'NOT_STARTED',
  priority: 'MEDIUM',
  estimated_effort: null,
  success_criteria: null,
  completed_at: null,
  skills: [],
}

const note: RoadmapNote = { id: 'n-1', roadmap_id: 'rm-1', milestone_id: 'ms-1', task_id: null, content: 'hi', created_at: null }

const resource: RoadmapResource = {
  id: 'r-1',
  roadmap_id: 'rm-1',
  milestone_id: 'ms-1',
  task_id: null,
  title: 'Docs',
  url: '',
  description: '',
  type: 'OTHER',
  status: 'PLANNED',
  source: 'USER',
  created_at: null,
}

const link: RoadmapSkillLink = {
  id: 'l-1',
  roadmap_id: 'rm-1',
  milestone_id: 'ms-1',
  task_id: null,
  skill_id: 's-1',
  skill_name: 'Kafka',
}

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('roadmap queries', () => {
  it('fetches the roadmap list', async () => {
    mockApi.list.mockResolvedValue([summary])
    const { result } = renderHook(() => useRoadmapsQuery(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.[0].id).toBe('rm-1')
    expect(mockApi.list).toHaveBeenCalledTimes(1)
  })

  it('fetches a roadmap by id', async () => {
    mockApi.get.mockResolvedValue(detail)
    const { result } = renderHook(() => useRoadmapQuery('rm-1'), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.title).toBe('Kafka Roadmap')
    expect(mockApi.get).toHaveBeenCalledWith('rm-1')
  })

  it('disables the by-id query when no id is provided', async () => {
    const { result } = renderHook(() => useRoadmapQuery(null), { wrapper })
    expect(result.current.isFetching).toBe(false)
    expect(result.current.data).toBeUndefined()
  })

  it('fetches a roadmap by application', async () => {
    mockApi.getByApplication.mockResolvedValue(detail)
    const { result } = renderHook(() => useRoadmapByApplicationQuery('app-1'), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.application_id).toBe('app-1')
    expect(mockApi.getByApplication).toHaveBeenCalledWith('app-1')
  })

  it('returns error state when the API rejects', async () => {
    mockApi.getByApplication.mockRejectedValue(new Error('no roadmap'))
    const { result } = renderHook(() => useRoadmapByApplicationQuery('app-1'), { wrapper })
    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.data).toBeUndefined()
  })
})

describe('roadmap mutations invalidate queries', () => {
  function qcWrapper(qc: QueryClient) {
    return function Wrapper({ children }: { children: ReactNode }) {
      return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    }
  }

  it('create invalidates list + by-application', async () => {
    mockApi.create.mockResolvedValue(detail)
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const spy = vi.spyOn(qc, 'invalidateQueries')
    const { result } = renderHook(() => useCreateRoadmapMutation(), { wrapper: qcWrapper(qc) })
    result.current.mutate({ title: 'New', goal: { type: 'CUSTOM', title: 'Go' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.create).toHaveBeenCalledWith({ title: 'New', goal: { type: 'CUSTOM', title: 'Go' } })
    expect(spy).toHaveBeenCalledWith({ queryKey: ['roadmap', 'list'] })
    expect(spy).toHaveBeenCalledWith({ queryKey: ['roadmap', 'by-application'] })
  })

  it('update invalidates the specific roadmap id + list', async () => {
    mockApi.update.mockResolvedValue(detail)
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const spy = vi.spyOn(qc, 'invalidateQueries')
    const { result } = renderHook(() => useUpdateRoadmapMutation(), { wrapper: qcWrapper(qc) })
    result.current.mutate({ roadmapId: 'rm-1', input: { title: 'Renamed' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.update).toHaveBeenCalledWith('rm-1', { title: 'Renamed' })
    expect(spy).toHaveBeenCalledWith({ queryKey: ['roadmap', 'rm-1'] })
    expect(spy).toHaveBeenCalledWith({ queryKey: ['roadmap', 'list'] })
  })

  it('delete invalidates list + by-application', async () => {
    mockApi.remove.mockResolvedValue({ status: 'deleted' })
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const spy = vi.spyOn(qc, 'invalidateQueries')
    const { result } = renderHook(() => useDeleteRoadmapMutation(), { wrapper: qcWrapper(qc) })
    result.current.mutate('rm-1')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.remove).toHaveBeenCalledWith('rm-1')
    expect(spy).toHaveBeenCalledWith({ queryKey: ['roadmap', 'list'] })
  })

  it('add milestone calls the api and invalidates', async () => {
    mockApi.addMilestone.mockResolvedValue(milestone)
    const { result } = renderHook(() => useAddMilestoneMutation(), { wrapper })
    result.current.mutate({ roadmapId: 'rm-1', input: { title: 'Basics' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.addMilestone).toHaveBeenCalledWith('rm-1', { title: 'Basics' })
  })

  it('update milestone calls the api', async () => {
    mockApi.updateMilestone.mockResolvedValue({ ...milestone, status: 'COMPLETED' })
    const { result } = renderHook(() => useUpdateMilestoneMutation(), { wrapper })
    result.current.mutate({ milestoneId: 'ms-1', input: { status: 'COMPLETED' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.updateMilestone).toHaveBeenCalledWith('ms-1', { status: 'COMPLETED' })
  })

  it('delete milestone calls the api', async () => {
    mockApi.removeMilestone.mockResolvedValue({ status: 'deleted' })
    const { result } = renderHook(() => useDeleteMilestoneMutation(), { wrapper })
    result.current.mutate('ms-1')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.removeMilestone).toHaveBeenCalledWith('ms-1')
  })

  it('add task calls the api', async () => {
    mockApi.addTask.mockResolvedValue(task)
    const { result } = renderHook(() => useAddTaskMutation(), { wrapper })
    result.current.mutate({ milestoneId: 'ms-1', input: { title: 'Read docs' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.addTask).toHaveBeenCalledWith('ms-1', { title: 'Read docs' })
  })

  it('update task calls the api', async () => {
    mockApi.updateTask.mockResolvedValue({ ...task, status: 'COMPLETED' })
    const { result } = renderHook(() => useUpdateTaskMutation(), { wrapper })
    result.current.mutate({ taskId: 't-1', input: { status: 'COMPLETED' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.updateTask).toHaveBeenCalledWith('t-1', { status: 'COMPLETED' })
  })

  it('delete task calls the api', async () => {
    mockApi.removeTask.mockResolvedValue({ status: 'deleted' })
    const { result } = renderHook(() => useDeleteTaskMutation(), { wrapper })
    result.current.mutate('t-1')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.removeTask).toHaveBeenCalledWith('t-1')
  })

  it('add note calls the api', async () => {
    mockApi.addNote.mockResolvedValue(note)
    const { result } = renderHook(() => useAddNoteMutation(), { wrapper })
    result.current.mutate({ roadmapId: 'rm-1', input: { content: 'hi', milestone_id: 'ms-1' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.addNote).toHaveBeenCalledWith('rm-1', { content: 'hi', milestone_id: 'ms-1' })
  })

  it('delete note calls the api', async () => {
    mockApi.removeNote.mockResolvedValue({ status: 'deleted' })
    const { result } = renderHook(() => useDeleteNoteMutation(), { wrapper })
    result.current.mutate('n-1')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.removeNote).toHaveBeenCalledWith('n-1')
  })

  it('add resource calls the api', async () => {
    mockApi.addResource.mockResolvedValue(resource)
    const { result } = renderHook(() => useAddResourceMutation(), { wrapper })
    result.current.mutate({ roadmapId: 'rm-1', input: { title: 'Docs', url: '' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.addResource).toHaveBeenCalledWith('rm-1', { title: 'Docs', url: '' })
  })

  it('update resource calls the api', async () => {
    mockApi.updateResource.mockResolvedValue({ ...resource, status: 'COMPLETED' })
    const { result } = renderHook(() => useUpdateResourceMutation(), { wrapper })
    result.current.mutate({ resourceId: 'r-1', input: { status: 'COMPLETED' } })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.updateResource).toHaveBeenCalledWith('r-1', { status: 'COMPLETED' })
  })

  it('delete resource calls the api', async () => {
    mockApi.removeResource.mockResolvedValue({ status: 'deleted' })
    const { result } = renderHook(() => useDeleteResourceMutation(), { wrapper })
    result.current.mutate('r-1')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.removeResource).toHaveBeenCalledWith('r-1')
  })

  it('link skill calls the api', async () => {
    mockApi.linkSkill.mockResolvedValue(link)
    const { result } = renderHook(() => useLinkSkillMutation(), { wrapper })
    result.current.mutate({ skill_name: 'Kafka', milestone_id: 'ms-1' })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.linkSkill).toHaveBeenCalledWith({ skill_name: 'Kafka', milestone_id: 'ms-1' })
  })

  it('removes a skill link via the api', async () => {
    mockApi.removeSkillLink.mockResolvedValue({ status: 'deleted' })
    const { result } = renderHook(() => useRemoveSkillLinkMutation(), { wrapper })
    result.current.mutate('l-1')
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.removeSkillLink).toHaveBeenCalledWith('l-1')
  })
})