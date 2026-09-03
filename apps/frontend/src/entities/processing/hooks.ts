import { useQuery } from '@tanstack/react-query'
import { processingApi } from './api'
import type { ProcessingExecutionDetail } from './types'
import { DEFAULT_REFETCH_INTERVAL } from '@/shared/config/constants'

const PROCESSING_KEY = 'processing-executions'

export function useProcessingExecutionsQuery() {
  return useQuery<ProcessingExecutionDetail[]>({
    queryKey: [PROCESSING_KEY],
    queryFn: () => processingApi.list(),
    refetchInterval: DEFAULT_REFETCH_INTERVAL,
  })
}

export function useProcessingExecutionQuery(id: string) {
  return useQuery<ProcessingExecutionDetail>({
    queryKey: [PROCESSING_KEY, id],
    queryFn: () => processingApi.get(id),
    enabled: !!id,
  })
}
