'use client'

import { useAuth } from '@/shared/lib/auth-context'
import { useRouter, usePathname } from 'next/navigation'
import { useEffect } from 'react'

const PUBLIC_PATHS = ['/login']

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  const isPublic = PUBLIC_PATHS.includes(pathname)

  useEffect(() => {
    if (isLoading) return
    if (!isAuthenticated && !isPublic) {
      router.replace('/login')
    }
    if (isAuthenticated && isPublic) {
      router.replace('/jobs')
    }
  }, [isLoading, isAuthenticated, isPublic, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-muted-foreground text-sm">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated && !isPublic) return null
  if (isAuthenticated && isPublic) return null

  return <>{children}</>
}
