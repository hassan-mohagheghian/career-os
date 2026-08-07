import { api } from '@/shared/api'
import type {
  CandidateAnalyzeResult,
  CandidateProfile,
  CandidateSourcesResult,
  CandidateVersionsResult,
} from './types'

export const candidateApi = {
  getProfile: () => api.get<CandidateProfile>('/candidates/profile'),
  getSources: () => api.get<CandidateSourcesResult>('/candidates/sources'),
  getVersions: () => api.get<CandidateVersionsResult>('/candidates/versions'),
  uploadSource: (sourceType: string, rawText: string) =>
    api.post<{ id: string; source_type: string; version: number; status: string; raw_text: string }>('/candidates/sources', { source_type: sourceType, raw_text: rawText }),
  analyze: () => api.post<CandidateAnalyzeResult>('/candidates/analyze'),
}
