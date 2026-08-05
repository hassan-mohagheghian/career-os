import { api } from '@/shared/api'
import type {
  CompanyDetail,
  CompanyEditInput,
  CompanyListItem,
  CompanySearchQuery,
  InfiniteCompanySearchResult,
  PendingCompany,
} from './types'

export const companyApi = {
  listInfinite: (query: CompanySearchQuery) => {
    const params = new URLSearchParams()
    params.set('page_size', String(query.page_size ?? 25))
    if (query.cursor) params.set('cursor', query.cursor)
    if (query.query) params.set('query', query.query)
    if (query.industry) params.set('industry', query.industry)
    if (query.sort) params.set('sort', query.sort)
    if (query.order) params.set('order', query.order)
    return api.get<InfiniteCompanySearchResult>(`/companies/list?${params.toString()}`)
  },
  get: (id: number | string) => api.get<CompanyDetail>(`/companies/${id}`),
  update: (id: string, data: CompanyEditInput) => api.put<CompanyDetail>(`/companies/${id}`, data),
  delete: (id: string) => api.delete<void>(`/companies/${id}`),
  reprocess: (id: string) => api.post<void>(`/companies/${id}/reprocess`),
  pendingCreate: (data: { notes?: Array<Record<string, unknown>>; links?: Array<Record<string, unknown>>; source?: string; input_text?: string; name?: string; queue?: boolean }) =>
    api.post<PendingCompany>('/pending-companies', data),  pendingList: () => api.get<PendingCompany[]>('/pending-companies'),
  pendingDelete: (id: number | string) => api.delete<void>(`/pending-companies/${id}`),
  pendingProcess: (id: number | string) => api.post<void>(`/pending-companies/${id}/process`),
  pendingNotes: (id: number | string, note: string, noteType = 'text') =>
    api.post<void>(`/pending-companies/${id}/notes`, { note, note_type: noteType }),
  pendingLinks: (id: number | string, links: Array<{ url: string; title?: string }>) =>
    api.post<void>(`/pending-companies/${id}/links`, { links }),
}
