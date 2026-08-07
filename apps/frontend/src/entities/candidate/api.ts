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
  analyze: () => api.post<CandidateAnalyzeResult>('/candidates/analyze'),
}
