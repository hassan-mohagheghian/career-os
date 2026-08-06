import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useCreateJob } from './useCreateJob'

function jsonResponse(body: unknown, ok = true, status = 201) {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  } as Response
}

describe('useCreateJob', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('posts the form payload including the queue flag', async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ id: 'job-1', status: 'queued', message: 'ok', execution_id: 'exec-1' })
    )

    const { result } = renderHook(() => useCreateJob())
    let response: unknown
    await act(async () => {
      response = await result.current.createJob({
        job_post_url: 'https://example.com/job',
        job_title: 'Engineer',
        queue: true,
      })
    })

    expect(fetch).toHaveBeenCalledWith('/api/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_post_url: 'https://example.com/job',
        job_title: 'Engineer',
        queue: true,
      }),
    })
    expect(response).toEqual({ id: 'job-1', status: 'queued', message: 'ok', execution_id: 'exec-1' })
    expect(result.current.error).toBeNull()
  })

  it('does not send the queue flag when not provided', async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ id: 'job-1', status: 'imported', message: 'ok' })
    )

    const { result } = renderHook(() => useCreateJob())
    await act(async () => {
      await result.current.createJob({ job_post_url: 'https://example.com/job' })
    })

    const body = JSON.parse((fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body)
    expect(body.queue).toBeUndefined()
  })

  it('surfaces server error messages', async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse(
        { error: { message: 'A Job with the same primary URL already exists.' } },
        false,
        409
      )
    )

    const { result } = renderHook(() => useCreateJob())
    let response: unknown
    await act(async () => {
      response = await result.current.createJob({ job_post_url: 'https://example.com/dup' })
    })

    expect(response).toBeNull()
    expect(result.current.error).toBe('A Job with the same primary URL already exists.')
    expect(result.current.existingJobId).toBeNull()
    await waitFor(() => expect(result.current.submitting).toBe(false))
  })

  it('exposes the existing job id on duplicate URL', async () => {
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse(
        {
          error: {
            message: 'A Job with the same primary URL already exists.',
            details: { job_id: 'job-dup' },
          },
        },
        false,
        409
      )
    )

    const { result } = renderHook(() => useCreateJob())
    await act(async () => {
      await result.current.createJob({ job_post_url: 'https://example.com/dup' })
    })

    expect(result.current.error).toBe('A Job with the same primary URL already exists.')
    expect(result.current.existingJobId).toBe('job-dup')
  })

  it('clears previous errors', async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error('network down'))
    vi.mocked(fetch).mockResolvedValue(
      jsonResponse({ id: 'job-1', status: 'imported', message: 'ok' })
    )

    const { result } = renderHook(() => useCreateJob())
    await act(async () => {
      await result.current.createJob({ job_post_url: 'https://example.com/first' })
    })
    expect(result.current.error).toBe('network down')

    result.current.clearError()
    await waitFor(() => expect(result.current.error).toBeNull())
  })
})
