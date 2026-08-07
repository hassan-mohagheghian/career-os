import { api } from '@/shared/api'

export const linkedinApi = {
  upload: (rawText: string) => api.post<{ status: string; version: number }>('/linkedin', { raw_text: rawText }),
}
