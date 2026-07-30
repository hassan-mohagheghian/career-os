import { api } from '@/shared/api'
import type { LLMConfiguration, CreateLLMConfigurationRequest, UpdateLLMConfigurationRequest, CreateLLMConfigurationResponse } from './types'

export const llmConfigurationApi = {
  list: () => api.get<LLMConfiguration[]>('/llm-configurations'),

  get: (id: string) => api.get<LLMConfiguration>(`/llm-configurations/${id}`),

  create: (body: CreateLLMConfigurationRequest) =>
    api.post<CreateLLMConfigurationResponse>('/llm-configurations', body),

  update: (id: string, body: UpdateLLMConfigurationRequest) =>
    api.patch<LLMConfiguration>(`/llm-configurations/${id}`, body),

  delete: (id: string) => api.delete<{ status: string }>(`/llm-configurations/${id}`),

  enable: (id: string) =>
    api.post<LLMConfiguration>(`/llm-configurations/${id}/enable`),

  disable: (id: string) =>
    api.post<LLMConfiguration>(`/llm-configurations/${id}/disable`),
}
