'use client'

import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { SSEEvent, SSEEventType } from '@/entities/processing/types'
import type { JobListItem, ProcessingStatus } from '@/entities/job/types'

const SSE_URL = '/events/processing'
const JOBS_KEY = 'jobs-v2'

export function useProcessingEvents() {
  const queryClient = useQueryClient()
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const updateJobInCache = useCallback((jobId: number, updater: (job: JobListItem) => JobListItem) => {
    queryClient.setQueriesData<{ items: JobListItem[] }>(
      { queryKey: [JOBS_KEY] },
      (old) => {
        if (!old) return old
        return {
          ...old,
          items: old.items.map((item) =>
            item.id === jobId ? updater(item) : item
          ),
        }
      }
    )
  }, [queryClient])

  const handleEvent = useCallback((type: SSEEventType, data: SSEEvent) => {
    const statusMap: Record<string, ProcessingStatus> = {
      QUEUED: 'queued',
      STARTED: 'starting',
      RUNNING: 'running',
      COMPLETED: 'completed',
      FAILED: 'failed',
      CANCELLED: 'cancelled',
    }

    const processingStatus = statusMap[data.status] || null

    switch (type) {
      case 'ExecutionQueued':
        updateJobInCache(data.job_id, (job) => ({
          ...job,
          latest_processing_execution: {
            id: data.execution_id,
            status: processingStatus || 'queued',
            started_at: data.updated_at,
            finished_at: null,
          },
        }))
        break

      case 'ExecutionStarted':
        updateJobInCache(data.job_id, (job) => ({
          ...job,
          latest_processing_execution: job.latest_processing_execution
            ? { ...job.latest_processing_execution, status: processingStatus || 'running', started_at: data.updated_at }
            : { id: data.execution_id, status: processingStatus || 'running', started_at: data.updated_at, finished_at: null },
        }))
        break

      case 'ExecutionStepChanged':
        updateJobInCache(data.job_id, (job) => ({
          ...job,
          latest_processing_execution: job.latest_processing_execution
            ? { ...job.latest_processing_execution, status: processingStatus || 'running' }
            : { id: data.execution_id, status: processingStatus || 'running', started_at: null, finished_at: null },
        }))
        break

      case 'ExecutionCompleted':
        updateJobInCache(data.job_id, (job) => ({
          ...job,
          scores: {
            overall: job.scores.overall,
            fit: job.scores.fit,
            success: job.scores.success,
          },
          latest_processing_execution: job.latest_processing_execution
            ? { ...job.latest_processing_execution, status: 'completed', finished_at: data.updated_at }
            : { id: data.execution_id, status: 'completed', started_at: null, finished_at: data.updated_at },
          updated_at: data.updated_at,
        }))
        break

      case 'ExecutionFailed':
        updateJobInCache(data.job_id, (job) => ({
          ...job,
          latest_processing_execution: job.latest_processing_execution
            ? { ...job.latest_processing_execution, status: 'failed', finished_at: data.updated_at }
            : { id: data.execution_id, status: 'failed', started_at: null, finished_at: data.updated_at },
        }))
        break
    }
  }, [updateJobInCache])

  const connect = useCallback(() => {
    if (eventSourceRef.current) return

    const es = new EventSource(SSE_URL)
    eventSourceRef.current = es

    es.addEventListener('ExecutionQueued', (e) => {
      const data: SSEEvent = JSON.parse(e.data)
      handleEvent('ExecutionQueued', data)
    })

    es.addEventListener('ExecutionStarted', (e) => {
      const data: SSEEvent = JSON.parse(e.data)
      handleEvent('ExecutionStarted', data)
    })

    es.addEventListener('ExecutionStepChanged', (e) => {
      const data: SSEEvent = JSON.parse(e.data)
      handleEvent('ExecutionStepChanged', data)
    })

    es.addEventListener('ExecutionCompleted', (e) => {
      const data: SSEEvent = JSON.parse(e.data)
      handleEvent('ExecutionCompleted', data)
    })

    es.addEventListener('ExecutionFailed', (e) => {
      const data: SSEEvent = JSON.parse(e.data)
      handleEvent('ExecutionFailed', data)
    })

    es.onerror = () => {
      es.close()
      eventSourceRef.current = null
      reconnectTimeoutRef.current = setTimeout(() => {
        connect()
      }, 3000)
    }
  }, [handleEvent])

  useEffect(() => {
    connect()
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [connect])
}
