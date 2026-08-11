import { api } from '@/shared/api'
import type {
  ApplicationDetail,
  ApplicationDocument,
  ApplicationDocumentType,
  ApplicationFollowUp,
  CreateFollowUpInput,
  DeleteResponse,
  GenerateResponse,
  UpdateApplicationInput,
  UpdateFollowUpInput,
} from './types'

export const applicationApi = {
  getByJob: (jobId: string) => api.get<ApplicationDetail>(`/applications/by-job/${jobId}`),
  get: (applicationId: string) => api.get<ApplicationDetail>(`/applications/${applicationId}`),
  create: (jobId: string) =>
    api.post<ApplicationDetail>(`/applications`, { job_id: jobId }),
  update: (applicationId: string, data: UpdateApplicationInput) =>
    api.patch<ApplicationDetail>(`/applications/${applicationId}`, data),
  addFollowUp: (applicationId: string, input: CreateFollowUpInput) =>
    api.post<ApplicationFollowUp>(`/applications/${applicationId}/follow-ups`, input),
  updateFollowUp: (followUpId: string, input: UpdateFollowUpInput) =>
    api.patch<ApplicationFollowUp>(`/applications/follow-ups/${followUpId}`, input),
  deleteFollowUp: (followUpId: string) =>
    api.delete<void>(`/applications/follow-ups/${followUpId}`),
  generatePreparation: (applicationId: string) =>
    api.post<GenerateResponse>(`/applications/${applicationId}/preparation/generate`),
  generateDocument: (applicationId: string, documentType: ApplicationDocumentType) =>
    api.post<GenerateResponse>(`/applications/${applicationId}/documents/${documentType}/generate`),
  updateDocument: (documentId: string, content: string) =>
    api.patch<ApplicationDocument>(`/applications/documents/${documentId}`, { content }),
  deleteDocument: (documentId: string) =>
    api.delete<DeleteResponse>(`/applications/documents/${documentId}`),
}
