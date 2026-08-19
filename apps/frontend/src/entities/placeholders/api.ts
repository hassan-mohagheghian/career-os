import { api } from '@/shared/api'
import type { PlaceholdersList, PlaceholderValues, PlaceholderItem } from './types'

export const placeholdersApi = {
  list: () => api.get<PlaceholdersList>('/placeholders'),
  update: (values: PlaceholderValues) =>
    api.put<{ items: PlaceholderItem[] }>('/placeholders', values),
}