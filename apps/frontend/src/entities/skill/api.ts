import { api } from '@/shared/api'
import type {
  Skill,
  SkillBreakdownInfo,
  SkillBreakdownResult,
  SkillCategoryInfo,
  SkillCreateInput,
  SkillListItem,
  SkillSearchQuery,
  SkillUpdateInput,
  InfiniteSkillSearchResult,
} from './types'

export const skillApi = {
  listInfinite: (query: SkillSearchQuery) => {
    const params = new URLSearchParams()
    params.set('page_size', String(query.page_size ?? 25))
    if (query.cursor) params.set('cursor', query.cursor)
    if (query.query) params.set('query', query.query)
    if (query.category) params.set('category', query.category)
    if (query.categories && query.categories.length > 0) {
      query.categories.forEach((c) => params.append('categories', c))
    }
    if (query.pinned) params.set('pinned', 'true')
    if (query.sort) params.set('sort', query.sort)
    if (query.order) params.set('order', query.order)
    return api.get<InfiniteSkillSearchResult>(`/skills/list?${params.toString()}`)
  },
  get: (id: number | string) => api.get<Skill>(`/skills/${id}`),
  create: (data: SkillCreateInput) => api.post<SkillListItem>('/skills', data),
  update: (id: number | string, data: SkillUpdateInput) => api.put<SkillListItem>(`/skills/${id}`, data),
  delete: (id: number | string) => api.delete<{ status: string }>(`/skills/${id}`),
  setCategory: (id: number | string, category: string) => api.put<SkillListItem>(`/skills/${id}/category`, { category }),
  setPinned: (id: number | string, pinned: boolean) => api.put<{ id: number; pinned: boolean }>(`/skills/${id}/pinned`, { pinned }),
  rename: (id: number | string, name: string) => api.patch<SkillListItem>(`/skills/${id}/rename`, { name }),
  addAlias: (id: number | string, aliasName: string) => api.post<SkillListItem>(`/skills/${id}/aliases`, { alias_name: aliasName }),
  removeAlias: (id: number | string, aliasName: string) => api.delete<SkillListItem>(`/skills/${id}/aliases?alias_name=${encodeURIComponent(aliasName)}`),
  merge: (targetId: number, sourceIds: number[]) => api.post<{ status: string; target: SkillListItem; merged: string[]; aliases: string[] }>('/skills/merge', { target_id: targetId, source_ids: sourceIds }),
  getCategories: () => api.get<SkillCategoryInfo[]>('/skills/categories'),
  createCategory: (name: string) => api.post<{ id: number; name: string; created: boolean }>('/skills/categories', { name }),
  deleteCategory: (name: string) => api.delete<{ status: string; name: string }>(`/skills/categories/${encodeURIComponent(name)}`),
  breakDown: (id: number, childNames: string[]) => api.post<SkillBreakdownResult>(`/skills/${id}/breakdown`, { child_names: childNames }),
  getBreakdowns: (id: number) => api.get<SkillBreakdownInfo>(`/skills/${id}/breakdowns`),
  promoteAliasToCanonical: (id: number, aliasName: string) => api.patch<SkillListItem>(`/skills/${id}/canonical`, { alias_name: aliasName }),
}
