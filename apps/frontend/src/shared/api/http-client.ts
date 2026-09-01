const API_BASE = '/api'
const TOKEN_KEY = 'js_auth_token'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public body?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function extractErrorMessage(body: unknown): string | undefined {
  if (!body || typeof body !== 'object') return undefined
  const record = body as Record<string, unknown>
  const err = record.error
  if (typeof err === 'string') return err
  if (err && typeof err === 'object' && typeof (err as Record<string, unknown>).message === 'string') {
    return (err as Record<string, unknown>).message as string
  }
  if (typeof record.message === 'string') return record.message
  return undefined
}

function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {}
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders(), ...options?.headers },
    ...options,
  })
  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem('js_auth_user')
      window.location.href = '/login'
    }
    throw new ApiError(401, 'Unauthorized')
  }
  if (!res.ok) {
    const body = await res.json().catch(() => undefined)
    throw new ApiError(res.status, extractErrorMessage(body) ?? res.statusText, body)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  download: async (path: string): Promise<Blob> => {
    const res = await fetch(`${API_BASE}${path}`)
    if (!res.ok) {
      const body = await res.json().catch(() => undefined)
      throw new ApiError(res.status, extractErrorMessage(body) ?? res.statusText, body)
    }
    return res.blob()
  },
}

export const authApi = {
  login: (username: string, password: string) =>
    api.post<{ token: string; user: { id: string; username: string; display_name: string; created_at: string } }>(
      '/auth/login',
      { username, password },
    ),
  register: (username: string, password: string, display_name: string) =>
    api.post<{ token: string; user: { id: string; username: string; display_name: string; created_at: string } }>(
      '/auth/register',
      { username, password, display_name },
    ),
  me: () =>
    api.get<{ id: string; username: string; display_name: string; created_at: string }>('/auth/me'),
}
