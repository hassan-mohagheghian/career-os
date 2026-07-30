export interface LLMConfiguration {
  id: string
  name: string
  model: string
  model_version: string | null
  enabled: boolean
  executor: string
  provider: string
  created_at: string | null
  updated_at: string | null
}

export interface CreateLLMConfigurationRequest {
  name: string
  model: string
  model_version?: string | null
  enabled?: boolean
}

export interface UpdateLLMConfigurationRequest {
  name?: string
  model?: string
  model_version?: string | null
  enabled?: boolean
}

export interface CreateLLMConfigurationResponse {
  id: string
}
