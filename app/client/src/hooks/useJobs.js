import { useState, useEffect, useMemo, useRef, useCallback } from 'react'

const API = '/api'
const PAGE_SIZE = 30

export function useJobs() {
  const [jobs, setJobs] = useState(null)
  const [summaries, setSummaries] = useState([])
  const [jobsPage, setJobsPage] = useState(0)
  const [jobsTotal, setJobsTotal] = useState(0)
  const [jobAgg, setJobAgg] = useState({ total: 0, high_match: 0, apply_now: 0, remote: 0 })
  const [loadingMore, setLoadingMore] = useState(false)
  const [sortBy, setSortBy] = useState('created_at')
  const [sortDir, setSortDir] = useState('desc')
  const jobsScrollRef = useRef(null)
  const jobsSentinelRef = useRef(null)

  const [filterCities, setFilterCities] = useState([])
  const [filterCompanies, setFilterCompanies] = useState([])
  const [filterTech, setFilterTech] = useState('')
  const [filterMatches, setFilterMatches] = useState([])
  const [filterWorkTypes, setFilterWorkTypes] = useState([])
  const [filterEmploymentTypes, setFilterEmploymentTypes] = useState([])
  const [filterResponseStatus, setFilterResponseStatus] = useState([])
  const [filterApplied, setFilterApplied] = useState(false)

  const activeFilterCount = filterCities.length + filterCompanies.length + filterMatches.length +
    filterWorkTypes.length + filterEmploymentTypes.length + filterResponseStatus.length +
    (filterTech ? 1 : 0) + (filterApplied ? 1 : 0)

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
    return params
  }, [sortBy, sortDir, filterCities, filterCompanies, filterMatches, filterWorkTypes, filterEmploymentTypes, filterTech, filterResponseStatus, filterApplied])

  const refreshJobs = useCallback(() => {
    setJobsPage(0)
    const params = buildParams(0)
    fetch(`${API}/jobs?${params}`).then(r => r.json()).then(d => {
      setJobs(d.jobs || [])
      setJobsTotal(d.total || 0)
      setJobAgg(d.agg || {})
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
      const data = await res.json()
      setJobs(prev => [...prev, ...(data.jobs || [])])
      setJobsPage(nextPage)
    } finally {
      setLoadingMore(false)
    }
  }, [jobsPage, jobsTotal, loadingMore, buildParams])

  const fetchJobs = useCallback(() => {
    return fetch(`${API}/jobs?offset=0&limit=${PAGE_SIZE}&sort_by=created_at&sort_dir=desc`)
      .then(r => r.json())
      .then(d => {
        setJobs(d.jobs || [])
        setJobsTotal(d.total || 0)
        setJobAgg(d.agg || {})
        setJobsPage(0)
      })
  }, [])

  const fetchSummaries = useCallback(() => {
    return fetch(`${API}/summaries`).then(r => r.json()).then(setSummaries)
  }, [])

  const deleteJob = useCallback(async (num) => {
    await fetch(`${API}/jobs/${num}`, { method: 'DELETE' })
    refreshJobs()
  }, [refreshJobs])

  const requeueJob = useCallback(async (num) => {
    await fetch(`${API}/jobs/${num}/requeue`, { method: 'POST' })
    refreshJobs()
  }, [refreshJobs])

  const rescoreJob = useCallback(async (num) => {
    await fetch(`${API}/jobs/${num}/rescore`, { method: 'POST' })
    refreshJobs()
  }, [refreshJobs])

  const updateJob = useCallback(async (num, fields) => {
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
    setFilterApplied(false)
  }, [])

  const jobsWithLocations = useMemo(() => {
    if (!jobs) return []
    return jobs.map(j => {
      let locations = []
      if (j.locations) {
        try { locations = typeof j.locations === 'string' ? JSON.parse(j.locations) : j.locations }
        catch { locations = [] }
      }
      if (!locations.length && j.location) locations = [j.location]
      return { ...j, parsedLocations: locations }
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
        const field = sortBy
        const aVal = a[field] ? new Date(a[field]).getTime() : 0
        const bVal = b[field] ? new Date(b[field]).getTime() : 0
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
    activeFilterCount,
    jobsWithLocations, allCities, allCompanies, filteredJobs,
    refreshJobs, loadMoreJobs, fetchJobs, fetchSummaries,
    deleteJob, requeueJob, rescoreJob, updateJob, clearFilters
  }
}
