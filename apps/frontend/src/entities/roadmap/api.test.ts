import { describe, it, expect, vi, beforeAll, afterEach } from 'vitest'
import { roadmapApi } from './api'

const fetchMock = vi.fn()

beforeAll(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.resetAllMocks()
})

function ok(body: unknown) {
  return { ok: true, json: () => Promise.resolve(body) }
}

function detail(id: string) {
  return { id, title: 'Roadmap', description: '', goal_type: 'CUSTOM', source: 'MANUAL', application_id: null, status: 'ACTIVE', progress: { completed_tasks: 0, total_tasks: 0, overall_percent: 0, milestone_progress: [] }, goal: null, milestones: [], notes: [], resources: [], created_at: null, updated_at: null }
}

const rmd = detail('rm-1')

describe('roadmapApi', () => {
  it('lists roadmaps', async () => {
    fetchMock.mockResolvedValue(ok([rmd]))
    await roadmapApi.list()
    const [url] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps')
  })

  it('gets a roadmap by id', async () => {
    fetchMock.mockResolvedValue(ok(rmd))
    await roadmapApi.get('rm-1')
    const [url] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/rm-1')
  })

  it('gets a roadmap by application', async () => {
    fetchMock.mockResolvedValue(ok(rmd))
    await roadmapApi.getByApplication('app-1')
    const [url] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/by-application/app-1')
  })

  it('creates a roadmap', async () => {
    fetchMock.mockResolvedValue(ok(rmd))
    await roadmapApi.create({ title: 'New', goal: { type: 'CUSTOM', title: 'Go' } })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ title: 'New', goal: { type: 'CUSTOM', title: 'Go' } })
  })

  it('updates a roadmap status', async () => {
    fetchMock.mockResolvedValue(ok(rmd))
    await roadmapApi.update('rm-1', { status: 'COMPLETED' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/rm-1')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ status: 'COMPLETED' })
  })

  it('deletes a roadmap', async () => {
    fetchMock.mockResolvedValue(ok({ status: 'deleted' }))
    await roadmapApi.remove('rm-1')
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/rm-1')
    expect(options.method).toBe('DELETE')
  })

  it('adds a milestone to a roadmap', async () => {
    fetchMock.mockResolvedValue(ok({ id: 'ms-1', roadmap_id: 'rm-1', position: 0, title: 'M', status: 'NOT_STARTED', priority: 'MEDIUM', tasks: [], skills: [] }))
    await roadmapApi.addMilestone('rm-1', { title: 'M' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/rm-1/milestones')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ title: 'M' })
  })

  it('updates a milestone', async () => {
    fetchMock.mockResolvedValue(ok({ id: 'ms-1', roadmap_id: 'rm-1', position: 0, title: 'M', status: 'COMPLETED', priority: 'MEDIUM', tasks: [], skills: [] }))
    await roadmapApi.updateMilestone('ms-1', { status: 'COMPLETED' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/milestones/ms-1')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ status: 'COMPLETED' })
  })

  it('deletes a milestone', async () => {
    fetchMock.mockResolvedValue(ok({ status: 'deleted' }))
    await roadmapApi.removeMilestone('ms-1')
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/milestones/ms-1')
    expect(options.method).toBe('DELETE')
  })

  it('adds a task to a milestone', async () => {
    fetchMock.mockResolvedValue(ok({ id: 't-1', milestone_id: 'ms-1', position: 0, title: 'T', status: 'NOT_STARTED', priority: 'MEDIUM', skills: [] }))
    await roadmapApi.addTask('ms-1', { title: 'T' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/milestones/ms-1/tasks')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ title: 'T' })
  })

  it('updates a task status', async () => {
    fetchMock.mockResolvedValue(ok({ id: 't-1', milestone_id: 'ms-1', position: 0, title: 'T', status: 'IN_PROGRESS', priority: 'MEDIUM', skills: [] }))
    await roadmapApi.updateTask('t-1', { status: 'IN_PROGRESS' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/tasks/t-1')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ status: 'IN_PROGRESS' })
  })

  it('deletes a task', async () => {
    fetchMock.mockResolvedValue(ok({ status: 'deleted' }))
    await roadmapApi.removeTask('t-1')
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/tasks/t-1')
    expect(options.method).toBe('DELETE')
  })

  it('adds a note', async () => {
    fetchMock.mockResolvedValue(ok({ id: 'n-1', roadmap_id: 'rm-1', content: 'hi', created_at: null }))
    await roadmapApi.addNote('rm-1', { content: 'hi' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/rm-1/notes')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ content: 'hi' })
  })

  it('deletes a note', async () => {
    fetchMock.mockResolvedValue(ok({ status: 'deleted' }))
    await roadmapApi.removeNote('n-1')
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/notes/n-1')
    expect(options.method).toBe('DELETE')
  })

  it('adds a resource', async () => {
    fetchMock.mockResolvedValue(ok({ id: 'r-1', roadmap_id: 'rm-1', title: 'Docs', url: '', type: 'OTHER', status: 'PLANNED', source: 'USER', created_at: null }))
    await roadmapApi.addResource('rm-1', { title: 'Docs', url: 'https://x' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/rm-1/resources')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ title: 'Docs', url: 'https://x' })
  })

  it('updates a resource status', async () => {
    fetchMock.mockResolvedValue(ok({ id: 'r-1', roadmap_id: 'rm-1', title: 'Docs', url: '', type: 'OTHER', status: 'COMPLETED', source: 'USER', created_at: null }))
    await roadmapApi.updateResource('r-1', { status: 'COMPLETED' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/resources/r-1')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ status: 'COMPLETED' })
  })

  it('deletes a resource', async () => {
    fetchMock.mockResolvedValue(ok({ status: 'deleted' }))
    await roadmapApi.removeResource('r-1')
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/resources/r-1')
    expect(options.method).toBe('DELETE')
  })

  it('links a skill to a milestone', async () => {
    fetchMock.mockResolvedValue(ok({ id: 'l-1', roadmap_id: 'rm-1', milestone_id: 'ms-1', task_id: null, skill_id: 's-1', skill_name: 'Kafka' }))
    await roadmapApi.linkSkill({ skill_name: 'kafka', milestone_id: 'ms-1' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/skills')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ skill_name: 'kafka', milestone_id: 'ms-1' })
  })

  it('removes a skill link', async () => {
    fetchMock.mockResolvedValue(ok({ status: 'deleted' }))
    await roadmapApi.removeSkillLink('l-1')
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/roadmaps/skills/l-1')
    expect(options.method).toBe('DELETE')
  })
})