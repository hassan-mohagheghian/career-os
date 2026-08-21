'use client'

import { useQuery } from '@tanstack/react-query'
import { jobApi } from '@/entities/job/api'

const JOBS_TIMELINE_KEY = 'jobs-timeline'

export function useJobTimeline() {
  return useQuery({
    queryKey: [JOBS_TIMELINE_KEY],
    queryFn: () => jobApi.timeline(),
    staleTime: 30_000,
  })
}