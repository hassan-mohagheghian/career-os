'use client'

import { useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { subscribeProcessingEvents } from '@/shared/api/processingEvents'
import type { SSEEventEnvelope, SSEEventType } from '@/entities/processing/types'
import type { JobListItem, ProcessingStatus } from '@/entities/job/types'
import type { CompanyListItem } from '@/entities/company/types'

const JOBS_KEY = 'jobs-v2-infinite'
const COMPANIES_KEY = 'companies-v2-infinite'

type ProcessingItem = JobListItem | CompanyListItem

export function useProcessingEvents() {
  const queryClient = useQueryClient()

  const updateItemInCache = useCallback((itemId: string | null, updater: (item: ProcessingItem) => ProcessingItem) => {
    if (!itemId) return
    for (const key of [JOBS_KEY, COMPANIES_KEY]) {
      queryClient.setQueriesData<{ pages: { items: ProcessingItem[] }[] }>(
        { queryKey: [key] },
        (old) => {
          if (!old) return old
          return {
            ...old,
            pages: old.pages.map((page) => ({
              ...page,
              items: page.items.map((item) =>
                item.id === itemId ? updater(item) : item
              ),
            })),
          }
        }
      )
    }
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
    const isCompany = data.target_type === 'company'
    const itemId = isCompany ? data.target_id : data.job_id
    const detailKey = isCompany ? 'company-detail' : 'job-detail'

    switch (type) {
      case 'execution.created':
      case 'execution.started':
        updateItemInCache(itemId, (item) => ({
          ...item,
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
        updateItemInCache(itemId, (item) => ({
          ...item,
          latest_processing_execution: item.latest_processing_execution
            ? { ...item.latest_processing_execution, status: 'running' }
            : { id: data.execution_id, status: 'running', started_at: null, finished_at: null },
        }))
        break

      case 'execution.completed':
        updateItemInCache(itemId, (item) => ({
          ...item,
          latest_processing_execution: item.latest_processing_execution
            ? { ...item.latest_processing_execution, status: 'completed', finished_at: data.payload.updated_at || null }
            : { id: data.execution_id, status: 'completed', started_at: null, finished_at: data.payload.updated_at || null },
          updated_at: data.payload.updated_at || item.updated_at,
        }))
        if (itemId) {
          queryClient.invalidateQueries({ queryKey: [detailKey, itemId] })
          queryClient.invalidateQueries({ queryKey: [JOBS_KEY] })
          queryClient.invalidateQueries({ queryKey: [COMPANIES_KEY] })
        }
        break

      case 'execution.failed':
        updateItemInCache(itemId, (item) => ({
          ...item,
          latest_processing_execution: item.latest_processing_execution
            ? { ...item.latest_processing_execution, status: 'failed', finished_at: data.payload.updated_at || null }
            : { id: data.execution_id, status: 'failed', started_at: null, finished_at: data.payload.updated_at || null },
        }))
        if (itemId) {
          queryClient.invalidateQueries({ queryKey: [detailKey, itemId] })
          queryClient.invalidateQueries({ queryKey: [JOBS_KEY] })
          queryClient.invalidateQueries({ queryKey: [COMPANIES_KEY] })
        }
        break

      case 'execution.cancelled':
        updateItemInCache(itemId, (item) => ({
          ...item,
          latest_processing_execution: item.latest_processing_execution
            ? { ...item.latest_processing_execution, status: 'cancelled', finished_at: data.payload.updated_at || null }
            : { id: data.execution_id, status: 'cancelled', started_at: null, finished_at: data.payload.updated_at || null },
        }))
        if (itemId) {
          queryClient.invalidateQueries({ queryKey: [JOBS_KEY] })
          queryClient.invalidateQueries({ queryKey: [COMPANIES_KEY] })
        }
        break
    }
  }, [updateItemInCache, queryClient])

  useEffect(() => {
    return subscribeProcessingEvents((type, data) => {
      handleEvent(type, data)
    })
  }, [handleEvent])
}
