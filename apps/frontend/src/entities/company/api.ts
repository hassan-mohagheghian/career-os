import { api } from '@/shared/api'
import type { Company } from './types'

export const companyApi = {
  list: () => api.get<Company[]>('/companies'),
  get: (id: number | string) => api.get<Company>(`/companies/${id}`),
  delete: (id: number) => api.delete<void>(`/companies/${id}`),
  reprocess: (id: number) => api.post<void>(`/companies/${id}/reprocess`),
}
