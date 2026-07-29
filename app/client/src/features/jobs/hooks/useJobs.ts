import { useState, useMemo, useRef, useCallback, useEffect } from 'react'
import { useSocketIO, cancelJob, resetJob, watchJob, unwatchJob } from '@/shared/hooks/useSocketIO'

const API = '/api'
const PAGE_SIZE = 30

interface Job {
  num: number
  company: string
  role: string
  location: string
  score: string
  match: string
  overall_score: number | null
  fit_score: number | null
  success_score: number | null
  stack: string
  visa: string
  work_type: string
  employment_type: string
  posted_at: string | null
  created_at: string
  applicants: string | null
  locations: string | null
  linked_company: number | null
  status: string
  current_node: string | null
  progress_pct: number
  error: string | null
  [key: string]: any
}

interface JobAgg {
  total: number
  high_match: number
  apply_now: number
  remote: number
  [key: string]: number
}

interface JobWithLocations extends Job {
  parsedLocations: string[]
}

interface JobsResponse {
  jobs: Job[]
  total: number
  agg: JobAgg
}

type SortField = 'created_at' | 'overall_score' | 'fit_score' | 'success_score' | 'num' | 'company' | 'location' | 'applicants' | 'posted_at' | 'apply_time' | 'response_time'

export function useJobs() {
  const [jobs, setJobs] = useState<Job[] | null>(null)
  const [summaries, setSummaries] = useState<any[]>([])
  const [jobsPage, setJobsPage] = useState(0)
  const [jobsTotal, setJobsTotal] = useState(0)
  const [jobAgg, setJobAgg] = useState<JobAgg>({ total: 0, high_match: 0, apply_now: 0, remote: 0 })
  const [loadingMore, setLoadingMore] = useState(false)
  const [sortBy, setSortBy] = useState<SortField>('created_at')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const jobsScrollRef = useRef<HTMLDivElement>(null)
  const jobsSentinelRef = useRef<HTMLDivElement>(null)
  const socket = useSocketIO()
  const watchedRef = useRef(new Set<number>())

  const syncWatchRooms = useCallback((list: Job[]) => {
    const newIds = new Set(list.map(j => j.num))
    for (const id of watchedRef.current) {
      if (!newIds.has(id)) {
        unwatchJob(id)
        watchedRef.current.delete(id)
      }
    }
    for (const id of newIds) {
      if (!watchedRef.current.has(id)) {
        watchJob(id)
        watchedRef.current.add(id)
      }
    }
  }, [])

  useEffect(() => {
    return () => {
      for (const id of watchedRef.current) {
        unwatchJob(id)
      }
      watchedRef.current.clear()
    }
  }, [])

  const [filterCities, setFilterCities] = useState<string[]>([])
  const [filterCompanies, setFilterCompanies] = useState<string[]>([])
  const [filterTech, setFilterTech] = useState('')
  const [filterMatches, setFilterMatches] = useState<string[]>([])
  const [filterWorkTypes, setFilterWorkTypes] = useState<string[]>([])
  const [filterEmploymentTypes, setFilterEmploymentTypes] = useState<string[]>([])
  const [filterResponseStatus, setFilterResponseStatus] = useState<string[]>([])
  const [filterApplied, setFilterApplied] = useState(false)
  const [filterScores, setFilterScores] = useState<string[]>([])

  const activeFilterCount = filterCities.length + filterCompanies.length + filterMatches.length +
    filterWorkTypes.length + filterEmploymentTypes.length + filterResponseStatus.length +
    filterScores.length + (filterTech ? 1 : 0) + (filterApplied ? 1 : 0)

  const buildParams = useCallback((offset = 0) => {
    const params = new URLSearchParams()
    params.set('offset', String(offset))
    params.set('limit', String(PAGE_SIZE))
    params.set('sort_by', sortBy)
    params.set('sort_dir', sortDir)
    if (filterCities.length) params.set('filter_cities', filterCities.join(','))
    if (filterCompanies.length) params.set('filter_companies', filterCompanies.join(','))
    if (filterMatches.length) params.set('filter_matches', filterMatches.join(','))
    if (filterWorkTypes.length) params.set('filter_work_types', filterWorkTypes.join(','))
    if (filterEmploymentTypes.length) params.set('filter_employment_types', filterEmploymentTypes.join(','))
    if (filterTech) params.set('filter_tech', filterTech)
    if (filterResponseStatus.length) params.set('filter_response_status', filterResponseStatus.join(','))
    if (filterApplied) params.set('filter_applied', 'true')
    if (filterScores.length) params.set('filter_scores', filterScores.join(','))
    return params
  }, [sortBy, sortDir, filterCities, filterCompanies, filterMatches, filterWorkTypes, filterEmploymentTypes, filterTech, filterResponseStatus, filterApplied, filterScores])

  const refreshJobs = useCallback(() => {
    setJobsPage(0)
    const params = buildParams(0)
    fetch(`${API}/jobs?${params}`).then(r => r.json()).then((d: JobsResponse) => {
      setJobs(d.jobs || [])
      setJobsTotal(d.total || 0)
      setJobAgg(d.agg || { total: 0, high_match: 0, apply_now: 0, remote: 0 })
    })
  }, [buildParams])

  const loadMoreJobs = useCallback(async () => {
    if (loadingMore) return
    const nextPage = jobsPage + 1
    const offset = nextPage * PAGE_SIZE
    if (offset >= jobsTotal) return
    setLoadingMore(true)
    try {
      const params = buildParams(offset)
      const res = await fetch(`${API}/jobs?${params}`)
      const data: JobsResponse = await res.json()
      setJobs(prev => [...(prev || []), ...(data.jobs || [])])
      setJobsPage(nextPage)
    } finally {
      setLoadingMore(false)
    }
  }, [jobsPage, jobsTotal, loadingMore, buildParams])

  const fetchJobs = useCallback(() => {
    return fetch(`${API}/jobs?offset=0&limit=${PAGE_SIZE}&sort_by=created_at&sort_dir=desc`)
      .then(r => r.json())
      .then((d: JobsResponse) => {
        setJobs(d.jobs || [])
        setJobsTotal(d.total || 0)
        setJobAgg(d.agg || { total: 0, high_match: 0, apply_now: 0, remote: 0 })
        setJobsPage(0)
      })
  }, [])

  const fetchSummaries = useCallback(() => {
    return fetch(`${API}/summaries`).then(r => r.json()).then(setSummaries)
  }, [])

  const deleteJob = useCallback(async (num: number) => {
    await fetch(`${API}/jobs/${num}`, { method: 'DELETE' })
    refreshJobs()
  }, [refreshJobs])

  const requeueJob = useCallback(async (num: number) => {
    await fetch(`${API}/jobs/${num}/requeue`, { method: 'POST' })
    refreshJobs()
  }, [refreshJobs])

  const rescoreJob = useCallback(async (num: number) => {
    await fetch(`${API}/jobs/${num}/rescore`, { method: 'POST' })
    refreshJobs()
  }, [refreshJobs])

  const updateJob = useCallback(async (num: number, fields: Record<string, any>) => {
    const res = await fetch(`${API}/jobs/${num}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fields)
    })
    if (res.ok) {
      const updated = await res.json()
      setJobs(prev => prev ? prev.map(j => j.num === num ? { ...j, ...updated } : j) : prev)
      return updated
    }
    return null
  }, [])

  const clearFilters = useCallback(() => {
    setFilterCities([])
    setFilterCompanies([])
    setFilterTech('')
    setFilterMatches([])
    setFilterWorkTypes([])
    setFilterEmploymentTypes([])
    setFilterResponseStatus([])
    setFilterScores([])
    setFilterApplied(false)
  }, [])

  const jobsWithLocations = useMemo(() => {
    if (!jobs) return []
    return jobs.map(j => {
      let locations: string[] = []
      if (j.locations) {
        try { locations = typeof j.locations === 'string' ? JSON.parse(j.locations) : j.locations }
        catch { locations = [] }
      }
      if (!locations.length && j.location) locations = [j.location]
      return { ...j, parsedLocations: locations } as JobWithLocations
    })
  }, [jobs])

  const allCities = useMemo(() =>
    jobsWithLocations ? [...new Set(jobsWithLocations.flatMap(j => j.parsedLocations))].sort() : [],
    [jobsWithLocations]
  )

  const allCompanies = useMemo(() =>
    jobsWithLocations ? [...new Set(jobsWithLocations.map(j => j.company))].sort() : [],
    [jobsWithLocations]
  )

  const cancelJobAction = useCallback((num: number) => {
    cancelJob(num, 'job')
    refreshJobs()
  }, [refreshJobs])

  const resetJobAction = useCallback((num: number) => {
    resetJob(num, 'job')
    refreshJobs()
  }, [refreshJobs])

  useEffect(() => {
    const handleUpdate = (data: any) => {
      setJobs(prev => prev ? prev.map(j => j.num === data.id ? { ...j, ...data } : j) : prev)
    }
    const handleProgress = (data: any) => {
      setJobs(prev => prev ? prev.map(j => {
        if (j.num !== data.id) return j
        return { ...j, status: data.status || j.status, current_node: data.current_node, progress_pct: data.progress_pct }
      }) : prev)
    }
    const handleComplete = (data: any) => {
      setJobs(prev => prev ? prev.map(j => j.num === data.id ? { ...j, status: 'completed', ...data } : j) : prev)
      fetchJobs()
    }
    const handleError = (data: any) => {
      setJobs(prev => prev ? prev.map(j => j.num === data.id ? { ...j, status: 'failed', error: data.msg } : j) : prev)
    }

    socket.on('job:update', handleUpdate)
    socket.on('job:progress', handleProgress)
    socket.on('job:complete', handleComplete)
    socket.on('job:error', handleError)
    fetchJobs()

    return () => {
      socket.off('job:update', handleUpdate)
      socket.off('job:progress', handleProgress)
      socket.off('job:complete', handleComplete)
      socket.off('job:error', handleError)
    }
  }, [socket, fetchJobs])

  useEffect(() => {
    const sentinel = jobsSentinelRef.current
    if (!sentinel) return
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting) loadMoreJobs()
      },
      { root: jobsScrollRef.current, rootMargin: '200px' }
    )
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [loadMoreJobs])

  const filteredJobs = useMemo(() => {
    if (!jobsWithLocations) return []
    let r = [...jobsWithLocations]
    r.sort((a, b) => {
      if (sortBy === 'overall_score') { const aVal = a.overall_score ?? 0; const bVal = b.overall_score ?? 0; return sortDir === 'desc' ? bVal - aVal : aVal - bVal }
      if (sortBy === 'fit_score') { const aVal = a.fit_score ?? 0; const bVal = b.fit_score ?? 0; return sortDir === 'desc' ? bVal - aVal : aVal - bVal }
      if (sortBy === 'success_score') { const aVal = a.success_score ?? 0; const bVal = b.success_score ?? 0; return sortDir === 'desc' ? bVal - aVal : aVal - bVal }
      if (sortBy === 'num') return sortDir === 'desc' ? b.num - a.num : a.num - b.num
      if (sortBy === 'company') return sortDir === 'desc' ? b.company.localeCompare(a.company) : a.company.localeCompare(b.company)
      if (sortBy === 'location') return sortDir === 'desc' ? b.location.localeCompare(a.location) : a.location.localeCompare(b.location)
      if (sortBy === 'applicants') {
        const aVal = parseInt(String(a.applicants).replace(/\D/g, '')) || 999
        const bVal = parseInt(String(b.applicants).replace(/\D/g, '')) || 999
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal
      }
      if (sortBy === 'created_at' || sortBy === 'posted_at' || sortBy === 'apply_time' || sortBy === 'response_time') {
        const field = sortBy as keyof Job
        const aVal = a[field] ? new Date(a[field] as string).getTime() : 0
        const bVal = b[field] ? new Date(b[field] as string).getTime() : 0
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal
      }
      return 0
    })
    return r
  }, [jobsWithLocations, sortBy, sortDir])

  return {
    jobs, setJobs, summaries, setSummaries,
    jobsTotal, jobAgg, loadingMore,
    jobsScrollRef, jobsSentinelRef,
    sortBy, setSortBy, sortDir, setSortDir,
    filterCities, setFilterCities,
    filterCompanies, setFilterCompanies,
    filterTech, setFilterTech,
    filterMatches, setFilterMatches,
    filterWorkTypes, setFilterWorkTypes,
    filterEmploymentTypes, setFilterEmploymentTypes,
    filterResponseStatus, setFilterResponseStatus,
    filterApplied, setFilterApplied,
    filterScores, setFilterScores,
    activeFilterCount,
    jobsWithLocations, allCities, allCompanies, filteredJobs,
    refreshJobs, loadMoreJobs, fetchJobs, fetchSummaries,
    deleteJob, requeueJob, rescoreJob, updateJob, clearFilters,
    cancelJobAction, resetJobAction
  }
}
