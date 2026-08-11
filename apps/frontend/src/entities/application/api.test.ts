import { describe, it, expect, vi, beforeAll, afterEach } from 'vitest'
import { applicationApi } from './api'

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

describe('applicationApi', () => {
  it('creates an application with a job_id', async () => {
    const detail = { id: 'app-1', job_id: 'job-1', status: 'recommended', follow_ups: [], documents: [], preparation: null }
    fetchMock.mockResolvedValue(ok(detail))

    const result = await applicationApi.create('job-1')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/applications')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ job_id: 'job-1' })
    expect(result.id).toBe('app-1')
  })

  it('updates an application status', async () => {
    const detail = { id: 'app-1', job_id: 'job-1', status: 'applied', applied_at: '2026-08-11T10:00:00Z', follow_ups: [], documents: [], preparation: null }
    fetchMock.mockResolvedValue(ok(detail))

    await applicationApi.update('app-1', { status: 'applied', applied_at: '2026-08-11T10:00:00Z' })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/applications/app-1')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ status: 'applied', applied_at: '2026-08-11T10:00:00Z' })
  })

  it('gets the application for a job', async () => {
    fetchMock.mockResolvedValue(ok({ id: 'app-1', job_id: 'job-1', status: 'preparing', follow_ups: [], documents: [], preparation: null }))

    await applicationApi.getByJob('job-1')

    const [url] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/applications/by-job/job-1')
  })

  it('adds a follow-up', async () => {
    fetchMock.mockResolvedValue(ok({ id: 'fu-1', application_id: 'app-1', scheduled_at: null, note: 'ping', completed_at: null }))

    await applicationApi.addFollowUp('app-1', { note: 'ping' })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/applications/app-1/follow-ups')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ note: 'ping' })
  })

  it('generates a preparation', async () => {
    fetchMock.mockResolvedValue(ok({ execution_id: 'exec-1', status: 'queued', artifact: 'preparation' }))

    const result = await applicationApi.generatePreparation('app-1')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/applications/app-1/preparation/generate')
    expect(options.method).toBe('POST')
    expect(result.artifact).toBe('preparation')
  })

  it('generates a cover letter document', async () => {
    fetchMock.mockResolvedValue(ok({ execution_id: 'exec-2', status: 'queued', artifact: 'cover_letter' }))

    await applicationApi.generateDocument('app-1', 'cover_letter')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/applications/app-1/documents/cover_letter/generate')
    expect(options.method).toBe('POST')
  })

  it('updates a document content', async () => {
    fetchMock.mockResolvedValue(ok({ id: 'doc-1', application_id: 'app-1', document_type: 'tailored_resume', version: 2, content: '# Updated' }))

    await applicationApi.updateDocument('doc-1', '# Updated')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/applications/documents/doc-1')
    expect(options.method).toBe('PATCH')
    expect(JSON.parse(options.body)).toEqual({ content: '# Updated' })
  })

  it('deletes a document', async () => {
    fetchMock.mockResolvedValue(ok({ status: 'deleted' }))

    await applicationApi.deleteDocument('doc-1')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/applications/documents/doc-1')
    expect(options.method).toBe('DELETE')
  })

  it('rejects when generation fails', async () => {
    fetchMock.mockResolvedValue({ ok: false, status: 409, json: () => Promise.resolve({ error: 'an execution is already running' }) })

    await expect(applicationApi.generatePreparation('app-1')).rejects.toThrow(/already running/)
  })
})
