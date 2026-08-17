'use client'

import { useCallback, useState } from 'react'
import { jobApi, type CreateJobRequest, type CreateJobResponse } from '@/entities/job/api'
import type { JobSummary } from '@/entities/job/types'
import { ApiError } from '@/shared/api'

export type { CreateJobRequest, CreateJobResponse }

export function useCreateJob() {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [existingJobId, setExistingJobId] = useState<string | null>(null)
  const [existingJob, setExistingJob] = useState<JobSummary | null>(null)

  const createJob = useCallback(
    async (data: CreateJobRequest): Promise<CreateJobResponse | null> => {
      setSubmitting(true)
      setError(null)
      setExistingJobId(null)
      setExistingJob(null)
      try {
        return await jobApi.create(data)
      } catch (e) {
        const err = e as ApiError
        const details = (err.body as {
          error?: { details?: { job_id?: string; job?: JobSummary } }
        })?.error?.details
        setError(err.message || `Failed to create job (${err.status})`)
        setExistingJobId(details?.job_id ?? null)
        setExistingJob(details?.job ?? null)
        return null
      } finally {
        setSubmitting(false)
      }
    },
    []
  )

  const clearError = useCallback(() => {
    setError(null)
    setExistingJobId(null)
    setExistingJob(null)
  }, [])

  return { createJob, submitting, error, existingJobId, existingJob, clearError }
}
