import { api } from '@/shared/api'
import type {
  CompanyDetail,
  CompanyEditInput,
  CompanyListItem,
  CompanySearchQuery,
  InfiniteCompanySearchResult,
} from './types'

export interface CreateCompanyResult {
  id: string
  name: string
  status: string
  execution_id?: string
}

export const companyApi = {
  listInfinite: (query: CompanySearchQuery) => {
    const params = new URLSearchParams()
    params.set('page_size', String(query.page_size ?? 25))
    if (query.cursor) params.set('cursor', query.cursor)
    if (query.query) params.set('query', query.query)
    if (query.industry) params.set('industry', query.industry)
    if (query.status) params.set('status', query.status)
    if (query.pinned !== undefined) params.set('pinned', String(query.pinned))
    if (query.sort) params.set('sort', query.sort)
    if (query.order) params.set('order', query.order)
    return api.get<InfiniteCompanySearchResult>(`/companies/list?${params.toString()}`)
  },
  get: (id: number | string) => api.get<CompanyDetail>(`/companies/${id}`),
  update: (id: string, data: CompanyEditInput) => api.put<CompanyDetail>(`/companies/${id}`, data),
  setMain: (id: string, mainCompanyId: string | null) => api.put<CompanyDetail>(`/companies/${id}/main`, { main_company_id: mainCompanyId }),
  setPinned: (id: string, pinned: boolean) => api.put<{ id: string; pinned: boolean }>(`/companies/${id}/pinned`, { pinned }),
  delete: (id: string) => api.delete<void>(`/companies/${id}`),
  reprocess: (id: string) => api.post<{ status: string; execution_id: string }>(`/companies/${id}/reprocess`),
  create: (data: { name?: string; notes?: Array<Record<string, unknown>>; links?: Array<Record<string, unknown>>; source?: string; queue?: boolean }) =>
    api.post<CreateCompanyResult>('/companies', data),
}
