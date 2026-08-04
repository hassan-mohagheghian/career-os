import { describe, it, expect, vi, afterEach } from 'vitest'
import { api, ApiError } from './http-client'

function mockFetchResponse(response: Partial<Response>) {
  const res = {
    ok: true,
    status: 200,
    statusText: 'OK',
    headers: new Headers(),
    json: vi.fn().mockResolvedValue({}),
    ...response,
  } as unknown as Response
  globalThis.fetch = vi.fn().mockResolvedValue(res) as unknown as typeof fetch
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('api.http-client', () => {
  it('returns parsed JSON for 200 responses', async () => {
    mockFetchResponse({ status: 200, ok: true, json: vi.fn().mockResolvedValue({ id: '1' }) })
    await expect(api.get('/jobs/list')).resolves.toEqual({ id: '1' })
  })

  it('resolves to undefined for 204 No Content without parsing the body', async () => {
    const json = vi.fn().mockImplementation(() => {
      throw new SyntaxError('Unexpected end of JSON input')
    })
    mockFetchResponse({ status: 204, ok: true, json })

    await expect(api.delete('/jobs/abc')).resolves.toBeUndefined()
    expect(json).not.toHaveBeenCalled()
  })

  it('throws ApiError with server detail for non-2xx responses', async () => {
    mockFetchResponse({
      status: 404,
      ok: false,
      statusText: 'Not Found',
      json: vi.fn().mockResolvedValue({ error: 'Job abc not found' }),
    })
    await expect(api.delete('/jobs/abc')).rejects.toEqual(
      new ApiError(404, 'Job abc not found')
    )
  })

  it('throws ApiError with statusText when error body cannot be parsed', async () => {
    mockFetchResponse({
      status: 500,
      ok: false,
      statusText: 'Internal Server Error',
      json: vi.fn().mockRejectedValue(new SyntaxError('no body')),
    })
    await expect(api.get('/jobs/list')).rejects.toEqual(
      new ApiError(500, 'Internal Server Error')
    )
  })
})
