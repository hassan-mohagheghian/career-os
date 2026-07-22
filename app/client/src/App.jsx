import { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import {
  Briefcase, Gear, Brain, X, Check, Buildings, FileText
} from '@phosphor-icons/react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import ConfirmDialog from '@/components/shared/ConfirmDialog'

import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import JobDrawer from '@/components/JobDrawer'
import CompanyDrawer from '@/components/companies/CompanyDrawer'
import IntelligenceTab from '@/components/intelligence/IntelligenceTab'
import ResumeTab from '@/components/ResumeTab'
import RulesTab from '@/components/RulesTab'
import CompaniesPage from '@/components/companies/CompaniesPage'
import JobsPage from '@/components/jobs/JobsPage'
import WorkflowTerminal from '@/components/shared/WorkflowTerminal'
import DuplicateJobDialog from '@/components/shared/DuplicateJobDialog'

const API = '/api'

function App() {
  const [jobs, setJobs] = useState(null)
  const [summaries, setSummaries] = useState([])
  const [resumes, setResumes] = useState([])
  const [linkedinProfiles, setLinkedinProfiles] = useState([])
  const [cities, setCities] = useState([])
  const parseHash = () => {
    const h = window.location.hash.replace('#', '') || 'jobs'
    const parts = h.split('/')
    return { tab: parts[0] || 'jobs', id: parts[1] ? parseInt(parts[1]) : null }
  }
  const [tab, setTab] = useState(() => parseHash().tab)
  const [deepLinkId, setDeepLinkId] = useState(() => parseHash().id)
  const [drawer, setDrawer] = useState(null)
  const [drawerTab, setDrawerTab] = useState('details')
  const [companyDrawer, setCompanyDrawer] = useState(null)
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [pending, setPending] = useState([])
  const [urlInput, setUrlInput] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [processImmediately, setProcessImmediately] = useState(true)
  const [urlError, setUrlError] = useState('')
  const [duplicateJob, setDuplicateJob] = useState(null)
  const [toast, setToast] = useState(null)
  const [confirmDialog, setConfirmDialog] = useState(null)
  const [sortBy, setSortBy] = useState('created_at')
  const [sortDir, setSortDir] = useState('desc')
  const [filterCities, setFilterCities] = useState([])
  const [filterCompanies, setFilterCompanies] = useState([])
  const [filterTech, setFilterTech] = useState('')
  const [filterMatches, setFilterMatches] = useState([])
  const [filterWorkTypes, setFilterWorkTypes] = useState([])
  const [filterEmploymentTypes, setFilterEmploymentTypes] = useState([])
  const [filterResponseStatus, setFilterResponseStatus] = useState([])
  const [filterApplied, setFilterApplied] = useState(false)
  const [collapsedSections, setCollapsedSections] = useState({})
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const JOBS_PAGE_SIZE = 30
  const [jobsPage, setJobsPage] = useState(0)
  const [jobsTotal, setJobsTotal] = useState(0)
  const [jobAgg, setJobAgg] = useState({ total: 0, high_match: 0, apply_now: 0, remote: 0 })
  const [loadingMore, setLoadingMore] = useState(false)
  const jobsScrollRef = useRef(null)
  const jobsSentinelRef = useRef(null)
  const [workflowDrawer, setWorkflowDrawer] = useState(null)
  const [workflowLogs, setWorkflowLogs] = useState([])
  const workflowWs = useRef(null)
  const workflowEndRef = useRef(null)
  const [rules, setRules] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [intelligenceSubTab, setIntelligenceSubTab] = useState('market')
  const [refreshing, setRefreshing] = useState({})
  const [companies, setCompanies] = useState([])
  const [pendingCompanies, setPendingCompanies] = useState([])

  // Toast listener
  useEffect(() => {
    const handler = (e) => { setToast(e.detail); setTimeout(() => setToast(null), 2000) }
    window.addEventListener('toast', handler)
    return () => window.removeEventListener('toast', handler)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    Promise.all([
      fetch(`${API}/jobs?offset=0&limit=${JOBS_PAGE_SIZE}&sort_by=created_at&sort_dir=desc`).then(r => r.json()),
      fetch(`${API}/summaries`).then(r => r.json()),
      fetch(`${API}/resumes`).then(r => r.json()),
      fetch(`${API}/linkedin`).then(r => r.json()),
      fetch(`${API}/cities`).then(r => r.json()),
    ]).then(([jobsData, sums, res, linkedin, cits]) => {
      setJobs(jobsData.jobs || []); setJobsTotal(jobsData.total || 0); setJobAgg(jobsData.agg || {}); setJobsPage(0)
      setSummaries(sums); setResumes(res); setLinkedinProfiles(linkedin); setCities(cits)
    })
    fetchPending(); fetchRules(); fetchAnalysis(); fetchCompanies(); fetchPendingCompanies()
  }, [])

  const fetchRules = () => fetch(`${API}/rules`).then(r => r.json()).then(setRules)
  const fetchAnalysis = () => fetch(`${API}/intelligence`).then(r => r.ok ? r.json() : null).then(data => setAnalysis(data)).catch(() => setAnalysis(null))
  const fetchCompanies = () => fetch(`${API}/companies`).then(r => r.json()).then(setCompanies)
  const fetchPendingCompanies = () => fetch(`${API}/pending-companies`).then(r => r.json()).then(setPendingCompanies)

  const seenDoneRef = useRef(new Set())
  const refreshJobs = () => {
    setJobsPage(0)
    const params = new URLSearchParams()
    params.set('offset', '0'); params.set('limit', String(JOBS_PAGE_SIZE))
    params.set('sort_by', sortBy); params.set('sort_dir', sortDir)
    if (filterCities.length) params.set('filter_cities', filterCities.join(','))
    if (filterCompanies.length) params.set('filter_companies', filterCompanies.join(','))
    if (filterMatches.length) params.set('filter_matches', filterMatches.join(','))
    if (filterWorkTypes.length) params.set('filter_work_types', filterWorkTypes.join(','))
    if (filterEmploymentTypes.length) params.set('filter_employment_types', filterEmploymentTypes.join(','))
    if (filterTech) params.set('filter_tech', filterTech)
    if (filterResponseStatus.length) params.set('filter_response_status', filterResponseStatus.join(','))
    if (filterApplied) params.set('filter_applied', 'true')
    fetch(`${API}/jobs?${params}`).then(r => r.json()).then(d => { setJobs(d.jobs || []); setJobsTotal(d.total || 0); setJobAgg(d.agg || {}) })
  }

  const loadMoreJobs = useCallback(async () => {
    if (loadingMore) return
    const nextPage = jobsPage + 1; const offset = nextPage * JOBS_PAGE_SIZE
    if (offset >= jobsTotal) return
    setLoadingMore(true)
    try {
      const params = new URLSearchParams()
      params.set('offset', String(offset)); params.set('limit', String(JOBS_PAGE_SIZE))
      params.set('sort_by', sortBy); params.set('sort_dir', sortDir)
      if (filterCities.length) params.set('filter_cities', filterCities.join(','))
      if (filterCompanies.length) params.set('filter_companies', filterCompanies.join(','))
      if (filterMatches.length) params.set('filter_matches', filterMatches.join(','))
      if (filterWorkTypes.length) params.set('filter_work_types', filterWorkTypes.join(','))
      if (filterEmploymentTypes.length) params.set('filter_employment_types', filterEmploymentTypes.join(','))
      if (filterTech) params.set('filter_tech', filterTech)
      if (filterResponseStatus.length) params.set('filter_response_status', filterResponseStatus.join(','))
      if (filterApplied) params.set('filter_applied', 'true')
      const res = await fetch(`${API}/jobs?${params}`); const data = await res.json()
      setJobs(prev => [...prev, ...(data.jobs || [])]); setJobsPage(nextPage)
    } finally { setLoadingMore(false) }
  }, [jobsPage, jobsTotal, loadingMore, sortBy, sortDir, filterCities, filterCompanies, filterMatches, filterWorkTypes, filterEmploymentTypes, filterTech, filterResponseStatus, filterApplied])

  useEffect(() => {
    let es
    const checkDone = (pendingList) => {
      const newlyDone = pendingList.filter(p => p.status === 'done' && !seenDoneRef.current.has(p.id))
      if (newlyDone.length > 0) { newlyDone.forEach(p => seenDoneRef.current.add(p.id)); refreshJobs() }
    }
    const connect = () => {
      es = new EventSource(`${API}/pending/stream`)
      es.onmessage = (e) => { try { const list = JSON.parse(e.data); setPending(list); checkDone(list) } catch {} }
      es.onerror = () => { es.close(); setTimeout(connect, 3000) }
    }
    connect()
    const poll = setInterval(() => { fetchPending().then(checkDone); refreshJobs() }, 5000)
    return () => { es?.close(); clearInterval(poll) }
  }, [sortBy, sortDir, filterCities, filterCompanies, filterMatches, filterWorkTypes, filterEmploymentTypes, filterTech, filterResponseStatus, filterApplied])

  // Pending companies SSE stream
  useEffect(() => {
    let es
    const connect = () => {
      es = new EventSource(`${API}/pending-companies/stream`)
      es.onmessage = (e) => { try { const list = JSON.parse(e.data); setPendingCompanies(list); if (list.some(p => p.status === 'done')) fetchCompanies() } catch {} }
      es.onerror = () => { es.close(); setTimeout(connect, 5000) }
    }
    connect()
    const poll = setInterval(() => { fetchPendingCompanies(); fetchCompanies() }, 5000)
    return () => { es?.close(); clearInterval(poll) }
  }, [])

  useEffect(() => {
    const onHash = () => {
      const { tab: newTab, id } = parseHash()
      if (newTab && newTab !== tab) setTab(newTab)
      if (id) setDeepLinkId(id)
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [tab])

  // Deep link: auto-open drawer when URL has an ID
  useEffect(() => {
    if (!deepLinkId) return
    if (tab === 'jobs' && jobs && !drawer) {
      openDrawer(deepLinkId)
      setDeepLinkId(null)
    }
    // companies deep linking is handled by CompaniesPage itself
  }, [deepLinkId, tab, jobs, drawer])

  // Listen for cross-entity navigation events (e.g. from CompanyDrawer -> JobDrawer)
  useEffect(() => {
    const handleOpenJob = (e) => {
      const num = e.detail
      if (num && tab !== 'jobs') {
        setTab('jobs')
      }
      if (num) {
        setTimeout(() => openDrawer(num), 100)
      }
    }
    window.addEventListener('openJob', handleOpenJob)
    return () => window.removeEventListener('openJob', handleOpenJob)
  }, [tab, jobs])

  useEffect(() => {
    const sentinel = jobsSentinelRef.current
    if (!sentinel) return
    const observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMoreJobs() }, { threshold: 0.1 })
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [loadMoreJobs])

  const fetchPending = () => fetch(`${API}/pending`).then(r => r.json()).then(list => { setPending(list); return list })

  const submitUrl = async () => {
    if (!urlInput.trim()) return; setUrlError(''); setSubmitting(true)
    const res = await fetch(`${API}/pending`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: urlInput.trim(), source: 'web' }) })
    const data = await res.json()
    if (res.ok && data.status === 'exists') { setDuplicateJob(data); setUrlInput(''); setSubmitting(false); return }
    if (!res.ok) { setUrlError(data.error || 'Failed to add URL'); setSubmitting(false); return }
    setUrlInput(''); setSubmitting(false); fetchPending()
    if (processImmediately && data.id) await processPending(data.id)
  }

  const deletePending = async (id) => { await fetch(`${API}/pending/${id}`, { method: 'DELETE' }); fetchPending() }
  const processPending = async (id) => { await fetch(`${API}/pending/${id}/process`, { method: 'POST' }); fetchPending() }
  const resetPending = async (id) => { await fetch(`${API}/pending/${id}/reset`, { method: 'PUT' }); fetchPending() }
  const pausePending = async (id) => { await fetch(`${API}/pending/${id}/pause`, { method: 'PUT' }); fetchPending() }
  const rescoreJob = async (num) => { await fetch(`${API}/jobs/${num}/rescore`, { method: 'POST' }); fetchPending(); refreshJobs() }

  const showConfirm = (title, message, confirmLabel, variant = 'danger') => {
    return new Promise(resolve => { setConfirmDialog({ title, message, confirmLabel, variant, resolve }) })
  }

  const deleteJob = async (num) => {
    const ok = await showConfirm('Delete Job', `Permanently delete job #${num}? This cannot be undone.`, 'Delete Forever')
    if (!ok) return; await fetch(`${API}/jobs/${num}`, { method: 'DELETE' }); refreshJobs()
  }

  const requeueJob = async (num) => {
    const ok = await showConfirm('Reprocess Job', `Reprocess job #${num} from scratch? The current version will be permanently deleted.`, 'Reprocess')
    if (!ok) return; await fetch(`${API}/jobs/${num}/requeue`, { method: 'POST' }); fetchPending(); refreshJobs()
  }

  const updateJob = async (num, fields) => {
    const res = await fetch(`${API}/jobs/${num}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fields) })
    if (res.ok) {
      const updated = await res.json()
      setJobs(prev => prev ? prev.map(j => j.num === num ? { ...j, ...updated } : j) : prev)
      setDrawer(prev => prev && prev.job.num === num ? { ...prev, job: { ...prev.job, ...updated } } : prev)
    }
  }

  const connectWorkflowWs = (pid) => {
    if (workflowWs.current) workflowWs.current.close()
    const ws = new WebSocket(`ws://${window.location.hostname}:8765`)
    workflowWs.current = ws
    ws.onopen = () => { ws.send(JSON.stringify({ action: 'watch', pid })) }
    ws.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data)
        if (evt.type === 'state') { setWorkflowLogs(evt.logs || []) }
        else if (evt.type === 'tool_output') {
          const { stream, data } = evt
          if (stream === 'input') setWorkflowLogs(prev => [...prev, { step: 'cmd', msg: data, ts: evt.ts }])
          else if (stream === 'output') data.split('\n').forEach(line => { if (line.trim()) setWorkflowLogs(prev => [...prev, { step: 'out', msg: line, ts: evt.ts }]) })
          else if (stream === 'error') setWorkflowLogs(prev => [...prev, { step: 'err', msg: data, ts: evt.ts }])
          else if (stream === 'text') setWorkflowLogs(prev => [...prev, { step: 'mimo', msg: data, ts: evt.ts }])
        }
        else if (evt.type === 'mimo_event' && evt.event?.type === 'step_finish') {
          const reason = evt.event.part?.reason || ''; const tokens = evt.event.part?.tokens?.total || 0
          setWorkflowLogs(prev => [...prev, { step: 'step', msg: `Step finished: ${reason} (${tokens} tokens)`, ts: evt.ts }])
        }
        else if (evt.type === 'mimo_raw') setWorkflowLogs(prev => [...prev, { step: 'raw', msg: evt.line, ts: evt.ts }])
        else if (evt.type === 'job_info') setPending(prev => prev.map(p => p.id === evt.pid ? { ...p, company: evt.company || p.company, title: evt.title } : p))
        else if (evt.type === 'step') setWorkflowLogs(prev => [...prev, { step: evt.step, msg: `[${evt.status}]`, ts: evt.ts }])
        else if (evt.type === 'complete') setWorkflowLogs(prev => [...prev, { step: 'done', msg: `Complete: ${evt.company} #${evt.num}`, ts: evt.ts }])
        else if (evt.type === 'error') setWorkflowLogs(prev => [...prev, { step: 'error', msg: evt.msg, ts: evt.ts }])
      } catch {}
    }
  }

  const openWorkflow = (item) => { setWorkflowLogs([]); setWorkflowDrawer(item); connectWorkflowWs(item.id) }

  const jobsWithLocations = useMemo(() => {
    if (!jobs) return []
    return jobs.map(j => {
      let locations = []
      if (j.locations) { try { locations = typeof j.locations === 'string' ? JSON.parse(j.locations) : j.locations } catch { locations = [] } }
      if (!locations.length && j.location) locations = [j.location]
      return { ...j, parsedLocations: locations }
    })
  }, [jobs])

  const allCities = jobsWithLocations ? [...new Set(jobsWithLocations.flatMap(j => j.parsedLocations))].sort() : []
  const allCompanies = jobsWithLocations ? [...new Set(jobsWithLocations.map(j => j.company))].sort() : []

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
        const aVal = parseInt(String(a.applicants).replace(/\D/g, '')) || 999; const bVal = parseInt(String(b.applicants).replace(/\D/g, '')) || 999
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal
      }
      if (sortBy === 'created_at' || sortBy === 'posted_at' || sortBy === 'apply_time' || sortBy === 'response_time') {
        const field = sortBy; const aVal = a[field] ? new Date(a[field]).getTime() : 0; const bVal = b[field] ? new Date(b[field]).getTime() : 0
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal
      }
      return 0
    })
    return r
  }, [jobsWithLocations, sortBy, sortDir])

  const activeFilterCount = filterCities.length + filterCompanies.length + filterMatches.length + filterWorkTypes.length + filterEmploymentTypes.length + filterResponseStatus.length + (filterTech ? 1 : 0) + (filterApplied ? 1 : 0)

  const openDrawer = async (num) => {
    if (!jobs) return
    const j = jobs.find(x => x.num === num); const s = summaries?.find(x => x.num === num)
    let fullJob = j
    try { const res = await fetch(`${API}/jobs/${num}`); if (res.ok) fullJob = await res.json() } catch {}
    const r = resumes?.find(x => x.job_num === num && !x.id.startsWith('cover_')) ||
              resumes?.find(x => !x.id.startsWith('original') && !x.id.startsWith('cover_') && fullJob.company.toLowerCase().includes((x.company || '').split(' ')[0].toLowerCase().replace(/[()]/g, '')))
    const cl = resumes?.find(x => x.job_num === num && x.id.startsWith('cover_'))
    setDrawer({ job: fullJob, summary: s, resume: r, coverLetter: cl }); setDrawerTab('details')
    window.history.replaceState(null, '', `#jobs/${num}`)
  }

  const openCompanyDrawer = async (id) => {
    try {
      const res = await fetch(`${API}/companies/${id}`)
      const data = await res.json()
      setCompanyDrawer(data)
    } catch (e) {
      console.error('Failed to load company', e)
    }
  }

  const deleteCompany = async (id) => {
    await fetch(`${API}/companies/${id}`, { method: 'DELETE' })
    setCompanyDrawer(null)
    fetchCompanies()
  }

  const reprocessCompany = async (id) => {
    await fetch(`${API}/companies/${id}/reprocess`, { method: 'POST' })
    setCompanyDrawer(null)
    fetchCompanies()
  }

  const [generatingResume, setGeneratingResume] = useState(false)
  const [generatingCover, setGeneratingCover] = useState(false)

  const generateResume = async (num) => {
    setGeneratingResume(true)
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-resume`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { setToast(data.error || 'Failed'); return }
      setDrawer(prev => ({ ...prev, resume: { id: data.id, content: data.content, job_num: num } }))
      fetch(`${API}/resumes`).then(r => r.json()).then(r => setResumes(r))
      setToast('Resume generated!')
    } catch (e) { setToast('Generation failed') }
    finally { setGeneratingResume(false) }
  }

  const generateCover = async (num) => {
    setGeneratingCover(true)
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-cover`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { setToast(data.error || 'Failed'); return }
      setDrawer(prev => ({ ...prev, coverLetter: { id: data.id, content: data.content, job_num: num } }))
      fetch(`${API}/resumes`).then(r => r.json()).then(r => setResumes(r))
      setToast('Cover letter generated!')
    } catch (e) { setToast('Generation failed') }
    finally { setGeneratingCover(false) }
  }

  const clearFilters = () => { setFilterCities([]); setFilterCompanies([]); setFilterTech(''); setFilterMatches([]); setFilterWorkTypes([]); setFilterEmploymentTypes([]); setFilterResponseStatus([]); setFilterApplied(false) }

  const filterChangeRef = useRef(false)
  useEffect(() => {
    if (!filterChangeRef.current) { filterChangeRef.current = true; return }
    setJobsPage(0)
    const params = new URLSearchParams()
    params.set('offset', '0'); params.set('limit', String(JOBS_PAGE_SIZE))
    params.set('sort_by', sortBy); params.set('sort_dir', sortDir)
    if (filterCities.length) params.set('filter_cities', filterCities.join(','))
    if (filterCompanies.length) params.set('filter_companies', filterCompanies.join(','))
    if (filterMatches.length) params.set('filter_matches', filterMatches.join(','))
    if (filterWorkTypes.length) params.set('filter_work_types', filterWorkTypes.join(','))
    if (filterEmploymentTypes.length) params.set('filter_employment_types', filterEmploymentTypes.join(','))
    if (filterTech) params.set('filter_tech', filterTech)
    if (filterResponseStatus.length) params.set('filter_response_status', filterResponseStatus.join(','))
    if (filterApplied) params.set('filter_applied', 'true')
    fetch(`${API}/jobs?${params}`).then(r => r.json()).then(d => { setJobs(d.jobs || []); setJobsTotal(d.total || 0); setJobAgg(d.agg || {}) })
  }, [sortBy, sortDir, filterCities, filterCompanies, filterTech, filterMatches, filterWorkTypes, filterEmploymentTypes, filterResponseStatus, filterApplied])

  const switchTab = (t) => { setTab(t); setDeepLinkId(null); window.location.hash = t }

  const tabs = [
    { id: 'jobs', icon: <Briefcase className="w-4 h-4" />, label: 'Jobs', badge: jobsTotal, section: 'jobs' },
    { id: 'companies', icon: <Buildings className="w-4 h-4" />, label: 'Companies', badge: companies.length, section: 'jobs' },
    { id: 'resume', icon: <FileText className="w-4 h-4" />, label: 'Resume', section: 'jobs' },
    { id: 'intelligence', icon: <Brain className="w-4 h-4" />, label: 'Intelligence', section: 'analysis' },
    { id: 'rules', icon: <Gear className="w-4 h-4" />, label: 'Rules', section: 'settings' },
  ]

  const refreshAnalysis = async () => { setRefreshing(r => ({ ...r, analysis: true })); try { await fetch(`${API}/intelligence/refresh`, { method: 'POST' }); } catch {} refreshJobs(); await fetchAnalysis(); setRefreshing(r => ({ ...r, analysis: false })) }
  const refreshStrategy = async () => { setRefreshing(r => ({ ...r, strategy: true })); try { await fetch(`${API}/intelligence/strategy/refresh`, { method: 'POST' }); } catch {} await fetchAnalysis(); setRefreshing(r => ({ ...r, strategy: false })) }
  const refreshNetworking = async () => { setRefreshing(r => ({ ...r, networking: true })); try { await fetch(`${API}/intelligence/networking/refresh`, { method: 'POST' }); } catch {} await fetchAnalysis(); setRefreshing(r => ({ ...r, networking: false })) }
  const refreshSkillsTab = async () => { setRefreshing(r => ({ ...r, skills: true })); try { await fetch(`${API}/intelligence/skills/refresh`, { method: 'POST' }); } catch {} await fetchAnalysis(); setRefreshing(r => ({ ...r, skills: false })) }
  const refreshMarket = async () => { setRefreshing(r => ({ ...r, market: true })); try { await fetch(`${API}/intelligence/market/refresh`, { method: 'POST' }); } catch {} await fetchAnalysis(); setRefreshing(r => ({ ...r, market: false })) }
  const refreshOpportunity = async () => { setRefreshing(r => ({ ...r, opportunity: true })); try { await fetch(`${API}/intelligence/opportunities/refresh`, { method: 'POST' }); } catch {} await fetchAnalysis(); setRefreshing(r => ({ ...r, opportunity: false })) }

  if (jobs === null) return <div className="flex items-center justify-center h-screen text-muted-foreground">Loading...</div>

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <Button variant="outline" size="icon" className="fixed top-3 left-3 z-[60] lg:hidden" onClick={() => setSidebarOpen(!sidebarOpen)}>
        {sidebarOpen ? <X className="w-4 h-4" /> : <Check className="w-4 h-4" />}
      </Button>

      <Sidebar sidebarOpen={sidebarOpen} tabs={tabs} tab={tab} onSwitchTab={switchTab} onClose={() => setSidebarOpen(false)} />

      <main className="flex-1 flex flex-col overflow-hidden">
        <Header jobAgg={jobAgg} jobsTotal={jobsTotal} resumes={resumes} theme={theme} onSwitchTab={switchTab} onToggleTheme={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} />

        <div className="flex-1 overflow-y-auto p-4 pt-16">
          <div className="max-w-[1400px] mx-auto">
            {tab === 'jobs' && (
              <JobsPage
                pending={pending} jobs={jobs} filteredJobs={filteredJobs} jobsTotal={jobsTotal} filteredJobsCount={filteredJobs.length}
                urlInput={urlInput} setUrlInput={setUrlInput} urlError={urlError} setUrlError={setUrlError}
                submitting={submitting} processImmediately={processImmediately} setProcessImmediately={setProcessImmediately}
                sortBy={sortBy} setSortBy={setSortBy} sortDir={sortDir} setSortDir={setSortDir}
                filterTech={filterTech} setFilterTech={setFilterTech} filterCities={filterCities} setFilterCities={setFilterCities}
                filterCompanies={filterCompanies} setFilterCompanies={setFilterCompanies}
                filterMatches={filterMatches} setFilterMatches={setFilterMatches}
                filterWorkTypes={filterWorkTypes} setFilterWorkTypes={setFilterWorkTypes}
                filterEmploymentTypes={filterEmploymentTypes} setFilterEmploymentTypes={setFilterEmploymentTypes}
                filterResponseStatus={filterResponseStatus} setFilterResponseStatus={setFilterResponseStatus}
                filterApplied={filterApplied} setFilterApplied={setFilterApplied}
                allCities={allCities} allCompanies={allCompanies} activeFilterCount={activeFilterCount}
                collapsedSections={collapsedSections} setCollapsedSections={setCollapsedSections}
                loadingMore={loadingMore} jobsScrollRef={jobsScrollRef} jobsSentinelRef={jobsSentinelRef}
                submitUrl={submitUrl} deletePending={deletePending} processPending={processPending}
                resetPending={resetPending} pausePending={pausePending} openWorkflow={openWorkflow}
                rescoreJob={rescoreJob} deleteJob={deleteJob} requeueJob={requeueJob}
                openDrawer={openDrawer} refreshJobs={refreshJobs} clearFilters={clearFilters} loadMoreJobs={loadMoreJobs}
              />
            )}
            {tab === 'companies' && (
              <CompaniesPage companies={companies} pendingCompanies={pendingCompanies} deepLinkId={deepLinkId} onClearDeepLink={() => setDeepLinkId(null)} onRefresh={() => { fetchCompanies(); fetchPendingCompanies() }} onOpenJob={openDrawer} onNavigateToJob={(num) => { setTab('jobs'); setTimeout(() => openDrawer(num), 100) }} onOpenCompany={openCompanyDrawer} />
            )}
            {tab === 'intelligence' && (
              <IntelligenceTab analysis={analysis} jobs={jobs} resumes={resumes} linkedinProfiles={linkedinProfiles} cities={cities} rules={rules} intelligenceSubTab={intelligenceSubTab} refreshing={refreshing} onSetIntelligenceSubTab={setIntelligenceSubTab} onRefreshAll={refreshAnalysis} onRefreshMarket={refreshMarket} onRefreshOpportunity={refreshOpportunity} onRefreshStrategy={refreshStrategy} onRefreshNetworking={refreshNetworking} onRefreshSkills={refreshSkillsTab} onOpenDrawer={openDrawer} />
            )}
            {tab === 'resume' && <ResumeTab resumes={resumes} linkedinProfiles={linkedinProfiles} onRefreshResumes={() => fetch(`${API}/resumes`).then(r => r.json()).then(r => setResumes(r))} onRefreshLinkedin={() => fetch(`${API}/linkedin`).then(r => r.json()).then(r => setLinkedinProfiles(r))} />}
            {tab === 'rules' && <RulesTab rules={rules} onUpdate={fetchRules} />}
          </div>
        </div>
      </main>

      <JobDrawer drawer={drawer} drawerTab={drawerTab} generatingResume={generatingResume} generatingCover={generatingCover} companies={companies} onClose={() => { setDrawer(null); window.history.replaceState(null, '', '#jobs') }} onSetDrawerTab={setDrawerTab} onRescoreJob={rescoreJob} onRequeueJob={requeueJob} onUpdateJob={updateJob} onSetToast={(msg) => { setToast(msg); if (msg) setTimeout(() => setToast(null), 2000) }} onGenerateResume={generateResume} onGenerateCover={generateCover} onLinkCompany={async (num, companyId) => { await fetch(`${API}/jobs/${num}/link-company`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ company_id: companyId }) }); const res = await fetch(`${API}/jobs/${num}`); const updated = await res.json(); setDrawer(prev => prev ? { ...prev, job: updated } : null) }} onOpenCompany={(id) => openCompanyDrawer(id)} onNavigateToCompany={(id) => { setTab('companies'); setTimeout(() => openCompanyDrawer(id), 100) }} />

      <CompanyDrawer company={companyDrawer} onClose={() => { setCompanyDrawer(null); window.history.replaceState(null, '', tab === 'companies' ? '#companies' : `#${tab}`) }} onDelete={deleteCompany} onReprocess={reprocessCompany} onOpenJob={(num) => openDrawer(num)} onNavigateToJob={(num) => { setTab('jobs'); setTimeout(() => openDrawer(num), 100) }} />

      <ConfirmDialog dialog={confirmDialog} onClose={() => setConfirmDialog(null)} />

      <DuplicateJobDialog duplicateJob={duplicateJob} setDuplicateJob={setDuplicateJob}
        onRescore={async (num) => { await fetch(`${API}/jobs/${num}/rescore`, { method: 'POST' }); fetchPending(); refreshJobs(); setDuplicateJob(null) }}
        onReprocess={async (num) => { await fetch(`${API}/jobs/${num}/requeue`, { method: 'POST' }); fetchPending(); refreshJobs(); setDuplicateJob(null) }} />

      <WorkflowTerminal workflowDrawer={workflowDrawer} workflowLogs={workflowLogs} workflowEndRef={workflowEndRef}
        onClose={() => { workflowWs.current?.close(); setWorkflowDrawer(null); setWorkflowLogs([]) }} />

      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[300] px-4 py-2 rounded-lg text-sm font-bold text-white shadow-lg transition-all duration-300 bg-green-500">
          {toast}
        </div>
      )}
    </div>
  )
}

export default App
