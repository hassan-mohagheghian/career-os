import { api } from '@/shared/api'
import type { ProcessingExecution } from './types'

export const processingApi = {
  list: (params?: Record<string, string>) => {
    const search = params ? `?${new URLSearchParams(params).toString()}` : ''
    return api.get<ProcessingExecution[]>(`/processing/executions${search}`)
  },
  get: (id: string) => api.get<ProcessingExecution>(`/processing/executions/${id}`),
}
