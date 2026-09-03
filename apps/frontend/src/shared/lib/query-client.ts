'use client'

import { QueryClient } from '@tanstack/react-query'
import { DEFAULT_STALE_TIME, DEFAULT_RETRY_COUNT } from '@/shared/config/constants'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: DEFAULT_STALE_TIME,
      refetchOnWindowFocus: false,
      retry: DEFAULT_RETRY_COUNT,
    },
  },
})

export function clearQueryCache() {
  queryClient.clear()
}
