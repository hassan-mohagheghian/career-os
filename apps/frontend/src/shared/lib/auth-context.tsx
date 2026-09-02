'use client'

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { User } from '@/shared/types/auth'
import { clearQueryCache } from '@/shared/lib/query-client'

const TOKEN_KEY = 'js_auth_token'
const USER_KEY = 'js_auth_user'

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
}

interface AuthContextValue extends AuthState {
  login: (token: string, user: User) => void
  logout: () => void
  setUser: (user: User) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
    isAuthenticated: false,
  })

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    const userJson = localStorage.getItem(USER_KEY)
    if (token && userJson) {
      try {
        const user = JSON.parse(userJson) as User
        setState({ user, token, isLoading: false, isAuthenticated: true })
      } catch {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setState({ user: null, token: null, isLoading: false, isAuthenticated: false })
      }
    } else {
      setState({ user: null, token: null, isLoading: false, isAuthenticated: false })
    }
  }, [])

  const login = useCallback((token: string, user: User) => {
    clearQueryCache()
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    setState({ user, token, isLoading: false, isAuthenticated: true })
  }, [])

  const logout = useCallback(() => {
    clearQueryCache()
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setState({ user: null, token: null, isLoading: false, isAuthenticated: false })
  }, [])

  const setUser = useCallback((user: User) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    setState((prev) => ({ ...prev, user }))
  }, [])

  const value = useMemo(
    () => ({ ...state, login, logout, setUser }),
    [state, login, logout, setUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
