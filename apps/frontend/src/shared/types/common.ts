export interface PaginatedResponse<T> {
  items: T[]
  total: number
  offset: number
  limit: number
}

export interface ApiErrorResponse {
  error: string
  message?: string
}
