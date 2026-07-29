import { api } from '@/shared/api'
import type { Resume, LinkedInProfile, ActiveGeneration } from './types'

export const resumeApi = {
  list: () => api.get<Resume[]>('/resumes'),
  linkedin: () => api.get<LinkedInProfile[]>('/linkedin'),
  activeGenerations: () => api.get<ActiveGeneration[]>('/resumes/active-generations'),
  generateResume: (num: number) => api.post<{ gen_id: number }>(`/jobs/${num}/generate-resume`),
  generateCover: (num: number) => api.post<{ gen_id: number }>(`/jobs/${num}/generate-cover`),
  cancelGeneration: (id: number) => api.post<void>(`/generations/${id}/cancel`),
}
