import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import '@testing-library/jest-dom'
import { useCreateJob } from './useCreateJob'
import { jobApi } from '@/entities/job/api'
import { ApiError } from '@/shared/api'

vi.mock('@/entities/job/api', () => ({
  jobApi: {
    create: vi.fn(),
  },
}))

const mockCreate = vi.mocked(jobApi.create)

describe('useCreateJob', () => {
  beforeEach(() => {
    mockCreate.mockReset()
  })

  it('creates a job successfully and returns response', async () => {
    mockCreate.mockResolvedValue({ id: 'job-1', status: 'queued', message: 'ok' })

    const { result } = renderHook(() => useCreateJob())
    let response: any = null
    await act(async () => { response = await result.current.createJob({ job_post_url: 'https://example.com/job' }) })

    expect(mockCreate).toHaveBeenCalledWith({ job_post_url: 'https://example.com/job' })
    expect(response).toEqual({ id: 'job-1', status: 'queued', message: 'ok' })
  })

  it('handles API error with job_id details', async () => {
    mockCreate.mockRejectedValue(new ApiError(409, 'Duplicate job', {
      error: { code: 'JOB_ALREADY_EXISTS', message: 'Duplicate job', details: { job_id: 'job-1' } },
    }))

    const { result } = renderHook(() => useCreateJob())
    let response: any = null
    await act(async () => { response = await result.current.createJob({ job_post_url: 'https://example.com/job' }) })

    expect(response).toBeNull()
    expect(result.current.error).toBe('Duplicate job')
    expect(result.current.existingJobId).toBe('job-1')
  })

  it('handles network error', async () => {
    mockCreate.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useCreateJob())
    let response: any = null
    await act(async () => { response = await result.current.createJob({ job_post_url: 'https://example.com/job' }) })

    expect(response).toBeNull()
    expect(result.current.error).toBe('Network error')
    expect(result.current.existingJobId).toBeNull()
  })
})
