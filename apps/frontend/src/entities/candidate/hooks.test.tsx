import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { candidateApi } from './api'
import { useAnalyzeProfileMutation, useCandidateProfileQuery, useCandidateSourcesQuery, useCandidateVersionsQuery, useUploadSourceMutation } from './hooks'
import type { CandidateProfile, CandidateSource, CandidateVersion } from './types'

vi.mock('./api', () => ({
  candidateApi: {
    getProfile: vi.fn(),
    getSources: vi.fn(),
    getVersions: vi.fn(),
    uploadSource: vi.fn(),
    analyze: vi.fn(),
  },
}))

const mockApi = vi.mocked(candidateApi)

const profile: CandidateProfile = {
  id: 'profile-1',
  candidate_id: 'cand-1',
  version: 2,
  name: 'Jane Doe',
  title: 'Backend Engineer',
  headline: 'Go + Python',
  summary: '8 years experience.',
  location: 'Berlin',
  skills: [
    { id: 's1', profile_id: 'profile-1', skill_id: 5, name: 'Python', level: 4, category: 'language', confidence: 0.96, origin: 'explicit', years_of_experience: 6, last_used: '2026', evidence: { sources: ['resume v1'] }, created_at: null, updated_at: null },
  ],
  experiences: [],
  projects: [],
  educations: [],
  certificates: [],
  interests: [],
  languages: [],
  created_at: null,
  updated_at: null,
}

const sources: CandidateSource[] = [
  { id: 'src-1', profile_id: 'profile-1', source_type: 'resume', version: 1, status: 'processed', error: null, raw_text: 'Resume text', processed_at: '2026-01-01T00:00:00', created_at: null, updated_at: null },
]

const versions: CandidateVersion[] = [
  { id: 'v-1', profile_id: 'profile-1', version: 2, snapshot: { name: 'Jane Doe' }, source_versions: { resume: 1 }, change_summary: 'added linkedin', created_at: null, updated_at: null },
]

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('candidate queries', () => {
  it('fetches the profile', async () => {
    mockApi.getProfile.mockResolvedValue(profile)
    const { result } = renderHook(() => useCandidateProfileQuery(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.name).toBe('Jane Doe')
  })

  it('returns error state when the API rejects', async () => {
    mockApi.getProfile.mockRejectedValue(new Error('no profile'))
    const { result } = renderHook(() => useCandidateProfileQuery(), { wrapper })
    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.data).toBeUndefined()
  })

  it('fetches sources', async () => {
    mockApi.getSources.mockResolvedValue({ items: sources })
    const { result } = renderHook(() => useCandidateSourcesQuery(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items).toHaveLength(1)
  })

  it('fetches versions', async () => {
    mockApi.getVersions.mockResolvedValue({ items: versions })
    const { result } = renderHook(() => useCandidateVersionsQuery(), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items[0].version).toBe(2)
  })
})

describe('useAnalyzeProfileMutation', () => {
  it('calls analyze and reports the result', async () => {
    mockApi.analyze.mockResolvedValue({ execution_id: 'exec-1', status: 'queued' })
    const { result } = renderHook(() => useAnalyzeProfileMutation(), { wrapper })
    result.current.mutate(undefined)
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.analyze).toHaveBeenCalledTimes(1)
    expect(result.current.data?.execution_id).toBe('exec-1')
  })

  it('passes through a noop result', async () => {
    mockApi.analyze.mockResolvedValue({ execution_id: null, status: 'noop', reason: 'no_new_sources' })
    const { result } = renderHook(() => useAnalyzeProfileMutation(), { wrapper })
    result.current.mutate(undefined)
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.status).toBe('noop')
    expect(result.current.data?.reason).toBe('no_new_sources')
  })
})

describe('useUploadSourceMutation', () => {
  it('calls uploadSource with the source type and raw text', async () => {
    mockApi.uploadSource.mockResolvedValue({ id: 'src-2', source_type: 'resume', version: 2, status: 'pending', raw_text: '...' })
    const { result } = renderHook(() => useUploadSourceMutation(), { wrapper })
    result.current.mutate({ sourceType: 'resume', rawText: 'Hello world' })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(mockApi.uploadSource).toHaveBeenCalledWith('resume', 'Hello world')
  })

  it('invalidates the sources query on success', async () => {
    mockApi.uploadSource.mockResolvedValue({ id: 'src-2', source_type: 'linkedin', version: 1, status: 'pending', raw_text: '...' })
    mockApi.getSources.mockResolvedValue({ items: sources })
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const qcSpy = vi.spyOn(qc, 'invalidateQueries')
    function TestWrapper({ children }: { children: ReactNode }) {
      return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    }
    const { result } = renderHook(() => useUploadSourceMutation(), { wrapper: TestWrapper })
    result.current.mutate({ sourceType: 'linkedin', rawText: 'LinkedIn text' })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(qcSpy).toHaveBeenCalledWith({ queryKey: ['candidate-sources'] })
  })
})
