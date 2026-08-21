import { describe, it, expect, vi, beforeAll, afterEach } from 'vitest'
import { jobApi } from './api'

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

describe('jobApi.timeline', () => {
  it('fetches per-day created-job counts from /jobs/timeline', async () => {
    const body = { days: [{ date: '2026-08-19', count: 3 }], total: 3 }
    fetchMock.mockResolvedValue(ok(body))

    const result = await jobApi.timeline()

    expect(fetchMock.mock.calls[0][0]).toBe('/api/jobs/timeline')
    expect(result.total).toBe(3)
    expect(result.days[0]).toEqual({ date: '2026-08-19', count: 3 })
  })
})