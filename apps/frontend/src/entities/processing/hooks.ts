import { useQuery } from '@tanstack/react-query'
import { processingApi } from './api'
import type { ProcessingExecutionDetail } from './types'

const PROCESSING_KEY = 'processing-executions'

export function useProcessingExecutionsQuery() {
  return useQuery<ProcessingExecutionDetail[]>({
    queryKey: [PROCESSING_KEY],
    queryFn: () => processingApi.list(),
    refetchInterval: 10_000,
  })
}

export function useProcessingExecutionQuery(id: string) {
  return useQuery<ProcessingExecutionDetail>({
    queryKey: [PROCESSING_KEY, id],
    queryFn: () => processingApi.get(id),
    enabled: !!id,
  })
}
