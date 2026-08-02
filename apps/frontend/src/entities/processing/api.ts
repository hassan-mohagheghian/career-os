import { api } from '@/shared/api'
import type { ProcessingExecutionDetail, QueueSnapshot } from './types'

export const processingApi = {
  list: () => api.get<ProcessingExecutionDetail[]>('/processing/executions'),
  get: (id: string) => api.get<ProcessingExecutionDetail>(`/processing/executions/${id}`),
  cancel: (id: string) => api.post<void>(`/processing/executions/${id}/cancel`),
  retry: (id: string) => api.post<void>(`/processing/executions/${id}/retry`),
  queue: () => api.get<QueueSnapshot>('/processing/queue'),
  removeQueueEntry: (id: string) => api.delete<void>(`/processing/queue/${id}`),
}
