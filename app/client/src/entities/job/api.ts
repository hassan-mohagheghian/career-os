import { api } from '@/shared/api'
import type { Job, JobsResponse, JobSearchQuery, JobSearchResult, InfiniteJobSearchResult } from './types'

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
  search: (query: JobSearchQuery) => {
    const params = new URLSearchParams()
    if (query.page !== undefined) params.set('page', String(query.page))
    if (query.page_size !== undefined) params.set('page_size', String(query.page_size))
    if (query.cursor) params.set('cursor', query.cursor)
    if (query.query) params.set('query', query.query)
    if (query.company_id !== undefined) params.set('company_id', String(query.company_id))
    if (query.processing_status) params.set('processing_status', query.processing_status)
    if (query.job_status) params.set('job_status', query.job_status)
    if (query.location) params.set('location', query.location)
    if (query.remote !== undefined) params.set('remote', String(query.remote))
    if (query.visa !== undefined) params.set('visa', String(query.visa))
    if (query.overall_score_min !== undefined) params.set('overall_score_min', String(query.overall_score_min))
    if (query.overall_score_max !== undefined) params.set('overall_score_max', String(query.overall_score_max))
    if (query.fit_score_min !== undefined) params.set('fit_score_min', String(query.fit_score_min))
    if (query.fit_score_max !== undefined) params.set('fit_score_max', String(query.fit_score_max))
    if (query.success_score_min !== undefined) params.set('success_score_min', String(query.success_score_min))
    if (query.success_score_max !== undefined) params.set('success_score_max', String(query.success_score_max))
    if (query.sort) params.set('sort', query.sort)
    if (query.order) params.set('order', query.order)
    return api.get<JobSearchResult>(`/jobs/list?${params.toString()}`)
  },
  searchInfinite: (query: JobSearchQuery) => {
    const params = new URLSearchParams()
    params.set('page_size', String(query.page_size ?? 25))
    if (query.cursor) params.set('cursor', query.cursor)
    if (query.query) params.set('query', query.query)
    if (query.company_id !== undefined) params.set('company_id', String(query.company_id))
    if (query.processing_status) params.set('processing_status', query.processing_status)
    if (query.job_status) params.set('job_status', query.job_status)
    if (query.location) params.set('location', query.location)
    if (query.remote !== undefined) params.set('remote', String(query.remote))
    if (query.visa !== undefined) params.set('visa', String(query.visa))
    if (query.overall_score_min !== undefined) params.set('overall_score_min', String(query.overall_score_min))
    if (query.overall_score_max !== undefined) params.set('overall_score_max', String(query.overall_score_max))
    if (query.fit_score_min !== undefined) params.set('fit_score_min', String(query.fit_score_min))
    if (query.fit_score_max !== undefined) params.set('fit_score_max', String(query.fit_score_max))
    if (query.success_score_min !== undefined) params.set('success_score_min', String(query.success_score_min))
    if (query.success_score_max !== undefined) params.set('success_score_max', String(query.success_score_max))
    if (query.sort) params.set('sort', query.sort)
    if (query.order) params.set('order', query.order)
    return api.get<JobSearchResult>(`/jobs/list?${params.toString()}`).then(res => {
      const cp = res.cursor_pagination
      return {
        items: res.items,
        next_cursor: cp?.next_cursor ?? null,
        has_more: cp?.has_more ?? false,
        total_items: cp?.total_items ?? res.pagination.total_items,
      } satisfies InfiniteJobSearchResult
    })
  },
  processJob: (jobId: string) =>
    api.post<{ execution_id: string; status: string }>(`/jobs/${jobId}/process`),
}
