import { useQuery } from '@tanstack/react-query'
import { processingApi } from './api'
import type { ProcessingExecution } from './types'

const PROCESSING_KEY = 'processing-executions'

export function useProcessingExecutionsQuery() {
  return useQuery<ProcessingExecution[]>({
    queryKey: [PROCESSING_KEY],
    queryFn: () => processingApi.list(),
    refetchInterval: 10_000,
  })
}

export function useProcessingExecutionQuery(id: string) {
  return useQuery<ProcessingExecution>({
    queryKey: [PROCESSING_KEY, id],
    queryFn: () => processingApi.get(id),
    enabled: !!id,
  })
}
