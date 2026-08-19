import { describe, it, expect, vi, beforeAll, afterEach } from 'vitest'
import { placeholdersApi } from './api'

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

describe('placeholdersApi', () => {
  it('lists keys and values', async () => {
    const list = {
      keys: [{ key: 'name', label: 'Full name' }, { key: 'email', label: 'Email' }],
      items: [{ key: 'name', value: 'Hassan', updated_at: null }],
      values: { name: 'Hassan' },
    }
    fetchMock.mockResolvedValue(ok(list))

    const result = await placeholdersApi.list()

    expect(fetchMock.mock.calls[0][0]).toBe('/api/placeholders')
    expect(result.keys).toHaveLength(2)
    expect(result.values.name).toBe('Hassan')
  })

  it('updates placeholder values via PUT', async () => {
    fetchMock.mockResolvedValue(ok({ items: [{ key: 'name', value: 'Hassan', updated_at: null }] }))

    const result = await placeholdersApi.update({ name: 'Hassan' })

    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/placeholders')
    expect(options.method).toBe('PUT')
    expect(JSON.parse(options.body)).toEqual({ name: 'Hassan' })
    expect(result.items[0].value).toBe('Hassan')
  })
})