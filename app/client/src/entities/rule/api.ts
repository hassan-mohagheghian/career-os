import { api } from '@/shared/api'
import type { Rule } from './types'

export const ruleApi = {
  list: () => api.get<Rule[]>('/rules'),
  update: (rules: Rule[]) => api.put<Rule[]>('/rules', rules),
}
