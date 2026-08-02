import { api } from '@/shared/api'
import type { Skill, SkillRoadmapProgress, DashboardData } from './types'

export const skillApi = {
  list: () => api.get<Skill[]>('/skills'),
  dashboard: () => api.get<DashboardData>('/skills-intelligence/dashboard'),
  roadmapProgress: () => api.get<SkillRoadmapProgress>('/skill-roadmap-progress/all'),
  roadmapJobs: (params?: Record<string, string>) => {
    const search = params ? `?${new URLSearchParams(params).toString()}` : ''
    return api.get<{ items: any[] }>(`/skill-roadmap-jobs${search}`)
  },
}
