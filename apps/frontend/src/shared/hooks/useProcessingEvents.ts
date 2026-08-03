'use client'

import { useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { subscribeProcessingEvents } from '@/shared/api/processingEvents'
import type { SSEEventEnvelope, SSEEventType } from '@/entities/processing/types'
import type { JobListItem, ProcessingStatus } from '@/entities/job/types'

const JOBS_KEY = 'jobs-v2-infinite'

export function useProcessingEvents() {
  const queryClient = useQueryClient()

  const updateJobInCache = useCallback((jobId: string | null, updater: (job: JobListItem) => JobListItem) => {
    if (!jobId) return
    queryClient.setQueriesData<{ pages: { items: JobListItem[] }[] }>(
      { queryKey: [JOBS_KEY] },
      (old) => {
        if (!old) return old
        return {
          ...old,
          pages: old.pages.map((page) => ({
            ...page,
            items: page.items.map((item) =>
              item.id === jobId ? updater(item) : item
            ),
          })),
        }
      }
    )
  }, [queryClient])

  const handleEvent = useCallback((type: SSEEventType, data: SSEEventEnvelope) => {
    const statusMap: Record<string, ProcessingStatus> = {
      QUEUED: 'queued',
      STARTING: 'starting',
      RUNNING: 'running',
      COMPLETED: 'completed',
      FAILED: 'failed',
      CANCELLED: 'cancelled',
    }

    const rawStatus = data.payload.status
    const processingStatus = statusMap[rawStatus] || null
    const jobId = data.job_id

    switch (type) {
      case 'execution.created':
      case 'execution.started':
        updateJobInCache(jobId, (job) => ({
          ...job,
          latest_processing_execution: {
            id: data.execution_id,
            status: processingStatus || 'running',
            started_at: data.payload.updated_at || null,
            finished_at: null,
          },
        }))
        break

      case 'workflow.step.started':
      case 'workflow.step.progress':
        updateJobInCache(jobId, (job) => ({
          ...job,
          latest_processing_execution: job.latest_processing_execution
            ? { ...job.latest_processing_execution, status: 'running' }
            : { id: data.execution_id, status: 'running', started_at: null, finished_at: null },
        }))
        break

      case 'execution.completed':
        updateJobInCache(jobId, (job) => ({
          ...job,
          latest_processing_execution: job.latest_processing_execution
            ? { ...job.latest_processing_execution, status: 'completed', finished_at: data.payload.updated_at || null }
            : { id: data.execution_id, status: 'completed', started_at: null, finished_at: data.payload.updated_at || null },
          updated_at: data.payload.updated_at || job.updated_at,
        }))
        break

      case 'execution.failed':
        updateJobInCache(jobId, (job) => ({
          ...job,
          latest_processing_execution: job.latest_processing_execution
            ? { ...job.latest_processing_execution, status: 'failed', finished_at: data.payload.updated_at || null }
            : { id: data.execution_id, status: 'failed', started_at: null, finished_at: data.payload.updated_at || null },
        }))
        break

      case 'execution.cancelled':
        updateJobInCache(jobId, (job) => ({
          ...job,
          latest_processing_execution: job.latest_processing_execution
            ? { ...job.latest_processing_execution, status: 'cancelled', finished_at: data.payload.updated_at || null }
            : { id: data.execution_id, status: 'cancelled', started_at: null, finished_at: data.payload.updated_at || null },
        }))
        break
    }
  }, [updateJobInCache])

  useEffect(() => {
    return subscribeProcessingEvents((type, data) => {
      handleEvent(type, data)
    })
  }, [handleEvent])
}
