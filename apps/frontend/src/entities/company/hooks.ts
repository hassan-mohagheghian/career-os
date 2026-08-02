import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { companyApi } from './api'

const COMPANIES_KEY = 'companies'

export function useCompaniesQuery() {
  return useQuery({
    queryKey: [COMPANIES_KEY],
    queryFn: () => companyApi.list(),
  })
}

export function useCompanyQuery(id: number | string) {
  return useQuery({
    queryKey: [COMPANIES_KEY, id],
    queryFn: () => companyApi.get(id),
    enabled: !!id,
  })
}

export function useDeleteCompanyMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => companyApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [COMPANIES_KEY] }),
  })
}

export function useReprocessCompanyMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => companyApi.reprocess(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [COMPANIES_KEY] }),
  })
}
