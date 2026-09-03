'use client'

import { useQuery } from '@tanstack/react-query'
import { jobApi } from '@/entities/job/api'
import { DEFAULT_STALE_TIME } from '@/shared/config/constants'

const JOBS_TIMELINE_KEY = 'jobs-timeline'

export function useJobTimeline() {
  return useQuery({
    queryKey: [JOBS_TIMELINE_KEY],
    queryFn: () => jobApi.timeline(),
    staleTime: DEFAULT_STALE_TIME,
  })
}