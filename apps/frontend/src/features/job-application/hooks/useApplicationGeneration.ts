'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { subscribeProcessingEvents } from '@/shared/api/processingEvents'
import type { SSEEventEnvelope, SSEEventType, WorkflowStep } from '@/entities/processing/types'

export interface ApplicationGenerationState {
  executionId: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  artifact?: string
  progress: number | null
  currentStep: string | null
  error: string | null
}

export function useApplicationGeneration(applicationId: string | null) {
  const queryClient = useQueryClient()
  const [generation, setGeneration] = useState<ApplicationGenerationState | null>(null)
  const applicationIdRef = useRef(applicationId)

  useEffect(() => {
    applicationIdRef.current = applicationId
  }, [applicationId])

  const resolveStep = useCallback((steps: WorkflowStep[] | undefined): { title: string | null; progress: number | null } => {
    if (!steps) return { title: null, progress: null }
    for (const step of steps) {
      if (step.status === 'processing' || step.status === 'pending') {
        const child = resolveStep(step.children)
        return {
          title: step.title,
          progress: child.progress ?? step.progress ?? 0,
        }
      }
      if (step.status === 'completed' && step.children.length > 0) {
        const child = resolveStep(step.children)
        if (child.title) return child
      }
    }
    return { title: null, progress: null }
  }, [])

  const handleEvent = useCallback((type: SSEEventType, data: SSEEventEnvelope) => {
    if (data.target_type !== 'application') return
    if (data.target_id !== applicationIdRef.current) return

    const isStart = type === 'execution.started' || type === 'execution.created'
    const isStep = type === 'workflow.step.started' || type === 'workflow.step.progress' || type === 'workflow.step.completed'
    const isDone = type === 'execution.completed' || type === 'execution.failed' || type === 'execution.cancelled'

    if (isStart) {
      setGeneration({
        executionId: data.execution_id,
        status: 'running',
        progress: 0,
        currentStep: null,
        error: null,
      })
      return
    }

    if (isStep) {
      const step = data.payload.step
      const resolved = resolveStep(step ? [step] : undefined)
      setGeneration((prev) => ({
        executionId: data.execution_id,
        status: 'running',
        progress: resolved.progress ?? prev?.progress ?? 0,
        currentStep: resolved.title ?? prev?.currentStep ?? null,
        error: null,
      }))
      return
    }

    if (isDone) {
      const failed = type === 'execution.failed'
      setGeneration({
        executionId: data.execution_id,
        status: failed ? 'failed' : 'completed',
        progress: failed ? null : 100,
        currentStep: null,
        error: failed ? (data.payload.message ?? null) : null,
      })
      queryClient.invalidateQueries({ queryKey: ['application', applicationIdRef.current] })
      queryClient.invalidateQueries({ queryKey: ['application', 'by-job'] })
      queryClient.invalidateQueries({ queryKey: ['roadmap', 'by-application'] })
      queryClient.invalidateQueries({ queryKey: ['roadmap', 'list'] })
    }
  }, [queryClient, resolveStep])

  useEffect(() => {
    return subscribeProcessingEvents((type, data) => {
      handleEvent(type, data)
    })
  }, [handleEvent])

  const clearGeneration = useCallback(() => setGeneration(null), [])

  return { generation, clearGeneration }
}
