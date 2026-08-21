import { api } from '@/shared/api'
import type { CityListResponse, CityListItem, CitySearchQuery, InfiniteCitySearchResult } from './types'

export interface CityMergeResult {
  status: string
  target: CityListItem
  merged: string[]
  aliases: string[]
}

export const cityApi = {
  listInfinite: (query: CitySearchQuery) => {
    const params = new URLSearchParams()
    params.set('page_size', String(query.page_size ?? 25))
    if (query.cursor) params.set('cursor', query.cursor)
    if (query.query) params.set('query', query.query)
    if (query.sort) params.set('sort', query.sort)
    if (query.order) params.set('order', query.order)
    return api.get<CityListResponse>(`/cities/list?${params.toString()}`).then((res) => ({
      items: res.items,
      next_cursor: res.next_cursor,
      has_more: res.has_more,
      total_items: res.total_items,
    } satisfies InfiniteCitySearchResult))
  },
  merge: (targetId: string, sourceIds: string[]) =>
    api.post<CityMergeResult>('/cities/merge', { target_id: targetId, source_ids: sourceIds }),
  addAlias: (cityId: string, aliasName: string) =>
    api.post<CityListItem>(`/cities/${cityId}/aliases`, { alias_name: aliasName }),
  removeAlias: (cityId: string, aliasName: string) =>
    api.delete<CityListItem>(`/cities/${cityId}/aliases?alias_name=${encodeURIComponent(aliasName)}`),
  promoteAliasToCanonical: (cityId: string, aliasName: string) =>
    api.patch<CityListItem>(`/cities/${cityId}/canonical`, { alias_name: aliasName }),
}