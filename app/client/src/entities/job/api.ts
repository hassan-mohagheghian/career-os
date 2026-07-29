import { api } from '@/shared/api'
import type { Job, JobsResponse } from './types'

export const jobApi = {
  list: (params: Record<string, string>) => {
    const search = new URLSearchParams(params).toString()
    return api.get<JobsResponse>(`/jobs?${search}`)
  },
  get: (num: number) => api.get<Job>(`/jobs/${num}`),
  update: (num: number, fields: Record<string, any>) => api.put<Job>(`/jobs/${num}`, fields),
  delete: (num: number) => api.delete<void>(`/jobs/${num}`),
  requeue: (num: number) => api.post<void>(`/jobs/${num}/requeue`),
  rescore: (num: number) => api.post<void>(`/jobs/${num}/rescore`),
  summaries: () => api.get<any[]>('/summaries'),
  linkCompany: (num: number, companyId: string) =>
    api.post<Job>(`/jobs/${num}/link-company`, { company_id: companyId }),
}
