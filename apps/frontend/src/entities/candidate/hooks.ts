'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { candidateApi } from './api'

const PROFILE_KEY = 'candidate-profile'
const SOURCES_KEY = 'candidate-sources'
const VERSIONS_KEY = 'candidate-versions'

export function useCandidateProfileQuery() {
  return useQuery({
    queryKey: [PROFILE_KEY],
    queryFn: () => candidateApi.getProfile(),
  })
}

export function useCandidateSourcesQuery() {
  return useQuery({
    queryKey: [SOURCES_KEY],
    queryFn: () => candidateApi.getSources(),
  })
}

export function useCandidateVersionsQuery() {
  return useQuery({
    queryKey: [VERSIONS_KEY],
    queryFn: () => candidateApi.getVersions(),
  })
}

export function useAnalyzeProfileMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => candidateApi.analyze(),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [PROFILE_KEY] })
      queryClient.invalidateQueries({ queryKey: [SOURCES_KEY] })
      queryClient.invalidateQueries({ queryKey: [VERSIONS_KEY] })
    },
  })
}
