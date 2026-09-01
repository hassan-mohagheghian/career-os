export interface User {
  id: string
  username: string
  display_name: string
  created_at: string
}

export interface AuthResponse {
  token: string
  user: User
}
