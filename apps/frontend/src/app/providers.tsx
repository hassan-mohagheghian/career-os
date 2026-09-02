'use client'

import { QueryClientProvider } from '@tanstack/react-query'
import { TooltipProvider } from '@/shared/ui/tooltip'
import { Toaster } from '@/shared/ui/sonner'
import { AuthProvider } from '@/shared/lib/auth-context'
import { AuthGuard } from '@/shared/lib/auth-guard'
import { queryClient } from '@/shared/lib/query-client'
import type { ReactNode } from 'react'

export function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <AuthGuard>
        <QueryClientProvider client={queryClient}>
          <TooltipProvider>
            {children}
            <Toaster />
          </TooltipProvider>
        </QueryClientProvider>
      </AuthGuard>
    </AuthProvider>
  )
}
