import { useState } from 'react'

const API = '/api'

export interface CreateJobLinkItem {
  title?: string
  url: string
}

export interface CreateJobNoteItem {
  title?: string
  content: string
}

export interface CreateJobRequest {
  job_post_url: string
  job_title?: string
  links?: CreateJobLinkItem[]
  notes?: CreateJobNoteItem[]
  queue?: boolean
}

export interface CreateJobResponse {
  id: string
  status: string
  message: string
  execution_id?: string | null
}

export function useCreateJob() {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createJob = async (data: CreateJobRequest): Promise<CreateJobResponse | null> => {
    setSubmitting(true)
    setError(null)
    try {
      const res = await fetch(`${API}/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        const msg = body?.error?.message || `Failed to create job (${res.status})`
        setError(msg)
        return null
      }
      return await res.json()
    } catch (e: any) {
      setError(e.message || 'Network error')
      return null
    } finally {
      setSubmitting(false)
    }
  }

  const clearError = () => setError(null)

  return { createJob, submitting, error, clearError }
}
