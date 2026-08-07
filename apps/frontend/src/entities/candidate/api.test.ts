import { describe, it, expect, vi, beforeAll, afterEach } from 'vitest'
import { candidateApi } from './api'

const fetchMock = vi.fn()

beforeAll(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.resetAllMocks()
})

describe('candidateApi.uploadSource', () => {
  it('posts source_type and raw_text to /api/candidates/sources', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve({ id: 'src-1', source_type: 'resume', version: 1, status: 'pending', raw_text: '' }) })

    await candidateApi.uploadSource('resume', 'My resume text')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/candidates/sources')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ source_type: 'resume', raw_text: 'My resume text' })
  })

  it('posts a linkedin source', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: () => Promise.resolve({ id: 'src-2', source_type: 'linkedin', version: 2, status: 'pending', raw_text: '' }) })

    await candidateApi.uploadSource('linkedin', 'My LinkedIn text')

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/candidates/sources')
    expect(JSON.parse(options.body)).toEqual({ source_type: 'linkedin', raw_text: 'My LinkedIn text' })
  })

  it('rejects when the request fails', async () => {
    fetchMock.mockResolvedValue({ ok: false, status: 400, json: () => Promise.resolve({ error: 'unsupported source type' }) })

    await expect(candidateApi.uploadSource('github', 'x')).rejects.toThrow(/unsupported source type/)
  })
})
