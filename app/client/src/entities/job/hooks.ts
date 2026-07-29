import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobApi } from './api'
import type { JobsResponse } from './types'

const JOBS_KEY = 'jobs'

export function useJobsQuery(params: Record<string, string>) {
  return useQuery<JobsResponse>({
    queryKey: [JOBS_KEY, params],
    queryFn: () => jobApi.list(params),
  })
}

export function useJobQuery(num: number) {
  return useQuery({
    queryKey: [JOBS_KEY, num],
    queryFn: () => jobApi.get(num),
    enabled: !!num,
  })
}

export function useUpdateJobMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ num, fields }: { num: number; fields: Record<string, any> }) =>
      jobApi.update(num, fields),
    onSuccess: () => qc.invalidateQueries({ queryKey: [JOBS_KEY] }),
  })
}

export function useDeleteJobMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (num: number) => jobApi.delete(num),
    onSuccess: () => qc.invalidateQueries({ queryKey: [JOBS_KEY] }),
  })
}

export function useRequeueJobMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (num: number) => jobApi.requeue(num),
    onSuccess: () => qc.invalidateQueries({ queryKey: [JOBS_KEY] }),
  })
}

export function useRescoreJobMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (num: number) => jobApi.rescore(num),
    onSuccess: () => qc.invalidateQueries({ queryKey: [JOBS_KEY] }),
  })
}

export function useSummariesQuery() {
  return useQuery({
    queryKey: ['summaries'],
    queryFn: () => jobApi.summaries(),
  })
}

export function useLinkCompanyMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ num, companyId }: { num: number; companyId: string }) =>
      jobApi.linkCompany(num, companyId),
    onSuccess: () => qc.invalidateQueries({ queryKey: [JOBS_KEY] }),
  })
}
