import { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import {
  Briefcase, ChartBar, Gear, Target, Brain, Sun, Moon,
  Clock, X, CheckCircle, Buildings, ArrowsClockwise,
  Rocket, FileText, Warning,
  House, Pause, Trash, Repeat,
  Users, Spinner, Stack, Check, CaretDown, Keyboard,
  MapPin, Copy,
  LinkedinLogo
} from '@phosphor-icons/react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle
} from '@/components/ui/alert-dialog'

import Sidebar from '@/components/Sidebar'
import Header from '@/components/Header'
import JobDrawer from '@/components/JobDrawer'
import DashboardTab from '@/components/DashboardTab'
import ProcessingItem from '@/components/ProcessingItem'
import { JobCard, getScoreColor, getMatchClass, LocationBadge, VisaBadge, WorkTypeTag, scoreRank } from '@/components/ProcessedCards'
import ResumeTab from '@/components/ResumeTab'
import RulesTab from '@/components/RulesTab'
import { MultiSelect } from '@/components/MultiSelect'

const API = '/api'

function App() {
  const [jobs, setJobs] = useState(null)
  const [summaries, setSummaries] = useState([])
  const [resumes, setResumes] = useState([])
  const [linkedinProfiles, setLinkedinProfiles] = useState([])
  const [cities, setCities] = useState([])
  const [tab, setTab] = useState(() => window.location.hash.replace('#', '') || 'jobs')
  const [drawer, setDrawer] = useState(null)
  const [drawerTab, setDrawerTab] = useState('details')
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
  const [dragOverCol, setDragOverCol] = useState(null)
  const JOBS_PAGE_SIZE = 30
  const [jobsPage, setJobsPage] = useState(0)
  const [jobsTotal, setJobsTotal] = useState(0)
  const [jobAgg, setJobAgg] = useState({ total: 0, high_match: 0, apply_now: 0, remote: 0 })
  const [loadingMore, setLoadingMore] = useState(false)
  const jobsScrollRef = useRef(null)
  const jobsSentinelRef = useRef(null)
  const [dragId, setDragId] = useState(null)
  const [workflowDrawer, setWorkflowDrawer] = useState(null)
  const [workflowLogs, setWorkflowLogs] = useState([])
  const workflowWs = useRef(null)
  const workflowEndRef = useRef(null)
  const [rules, setRules] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [dashboardSubTab, setDashboardSubTab] = useState('overview')
  const [refreshing, setRefreshing] = useState({})

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
    fetchPending(); fetchRules(); fetchAnalysis()
  }, [])

  const fetchRules = () => fetch(`${API}/rules`).then(r => r.json()).then(setRules)
  const fetchAnalysis = () => fetch(`${API}/analysis`).then(r => r.ok ? r.json() : null).then(data => setAnalysis(data)).catch(() => setAnalysis(null))

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

  useEffect(() => {
    const onHash = () => { const h = window.location.hash.replace('#', ''); if (h && h !== tab) setTab(h) }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [tab])

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
  const rescoreAll = async () => { await fetch(`${API}/jobs/rescore-all`, { method: 'POST' }); fetchPending(); refreshJobs() }

  const showConfirm = (title, message, confirmLabel, variant = 'danger') => {
    return new Promise(resolve => { setConfirmDialog({ title, message, confirmLabel, variant, resolve }) })
  }

  const reprocessAll = async () => {
    const ok = await showConfirm('Reprocess All', 'Reprocess ALL jobs? Every job will be re-queued for full processing from scratch.', 'Reprocess All')
    if (!ok) return; await fetch(`${API}/jobs/reprocess-all`, { method: 'POST' }); fetchPending()
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
          const { stream, tool, data } = evt
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

  useEffect(() => { workflowEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [workflowLogs])

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
      if (sortBy === 'score') {
        // Fit primary, success as tiebreaker
        const fitDiff = scoreRank(b.score) - scoreRank(a.score)
        if (fitDiff !== 0) return sortDir === 'desc' ? fitDiff : -fitDiff
        return sortDir === 'desc' ? scoreRank(b.success) - scoreRank(a.success) : scoreRank(a.success) - scoreRank(b.success)
      }
      if (sortBy === 'score_success') {
        // Success primary, fit as tiebreaker
        const successDiff = scoreRank(b.success) - scoreRank(a.success)
        if (successDiff !== 0) return sortDir === 'desc' ? successDiff : -successDiff
        return sortDir === 'desc' ? scoreRank(b.score) - scoreRank(a.score) : scoreRank(a.score) - scoreRank(b.score)
      }
      if (sortBy === 'score_combined') {
        // Combined sum of both scores
        return sortDir === 'desc' ? (scoreRank(b.score) + scoreRank(b.success)) - (scoreRank(a.score) + scoreRank(a.success)) : (scoreRank(a.score) + scoreRank(a.success)) - (scoreRank(b.score) + scoreRank(b.success))
      }
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

  const openDrawer = (num) => {
    if (!jobs) return
    const j = jobs.find(x => x.num === num); const s = summaries?.find(x => x.num === num)
    // Find the tailored resume and cover letter for this job
    const r = resumes?.find(x => x.job_num === num && !x.id.startsWith('cover_')) ||
              resumes?.find(x => !x.id.startsWith('original') && !x.id.startsWith('cover_') && j.company.toLowerCase().includes((x.company || '').split(' ')[0].toLowerCase().replace(/[()]/g, '')))
    const cl = resumes?.find(x => x.job_num === num && x.id.startsWith('cover_'))
    setDrawer({ job: j, summary: s, resume: r, coverLetter: cl }); setDrawerTab('details')
  }

  const [generatingResume, setGeneratingResume] = useState(false)
  const [generatingCover, setGeneratingCover] = useState(false)

  const generateResume = async (num) => {
    setGeneratingResume(true)
    try {
      const res = await fetch(`${API}/jobs/${num}/generate-resume`, { method: 'POST' })
      const data = await res.json()
      if (!res.ok) { setToast(data.error || 'Failed'); return }
      // Update drawer with new resume
      setDrawer(prev => ({ ...prev, resume: { id: data.id, content: data.content, job_num: num } }))
      // Refresh resumes list
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

  const switchTab = (t) => { setTab(t); window.location.hash = t }

  const tabs = [
    { id: 'jobs', icon: <Briefcase className="w-4 h-4" />, label: 'Jobs', badge: jobsTotal, section: 'jobs' },
    { id: 'resume', icon: <FileText className="w-4 h-4" />, label: 'Resume', section: 'jobs' },
    { id: 'dashboard', icon: <ChartBar className="w-4 h-4" />, label: 'Dashboard', section: 'analysis' },
    { id: 'rules', icon: <Gear className="w-4 h-4" />, label: 'Rules', section: 'settings' },
  ]

  const refreshAnalysis = async () => { setRefreshing(r => ({ ...r, analysis: true })); try { await fetch(`${API}/refresh/analysis`, { method: 'POST' }); } catch {} refreshJobs(); await fetchAnalysis(); setRefreshing(r => ({ ...r, analysis: false })) }
  const refreshStrategy = async () => { setRefreshing(r => ({ ...r, strategy: true })); try { await fetch(`${API}/refresh/dashboard`, { method: 'POST' }); } catch {} await fetchAnalysis(); setRefreshing(r => ({ ...r, strategy: false })) }
  const refreshNetworking = async () => { setRefreshing(r => ({ ...r, networking: true })); try { await fetch(`${API}/refresh/networking`, { method: 'POST' }); } catch {} await fetchAnalysis(); setRefreshing(r => ({ ...r, networking: false })) }
  const refreshSkillsTab = async () => { setRefreshing(r => ({ ...r, skills: true })); try { await fetch(`${API}/refresh/skills`, { method: 'POST' }); } catch {} await fetchAnalysis(); setRefreshing(r => ({ ...r, skills: false })) }

  if (jobs === null) return <div className="flex items-center justify-center h-screen text-muted-foreground">Loading...</div>

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {/* Mobile sidebar toggle */}
      <Button variant="outline" size="icon" className="fixed top-3 left-3 z-[60] lg:hidden" onClick={() => setSidebarOpen(!sidebarOpen)}>
        {sidebarOpen ? <X className="w-4 h-4" /> : <Check className="w-4 h-4" />}
      </Button>

      <Sidebar sidebarOpen={sidebarOpen} tabs={tabs} tab={tab} onSwitchTab={switchTab} onClose={() => setSidebarOpen(false)} />

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header jobAgg={jobAgg} jobsTotal={jobsTotal} resumes={resumes} theme={theme} onSwitchTab={switchTab} onToggleTheme={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} />

        <div className="flex-1 overflow-y-auto p-4 pt-16">
          <div className="max-w-[1400px] mx-auto">

            {/* === JOBS TAB === */}
            {tab === 'jobs' && (() => {
              const pendingCount = pending.filter(p => p.status === 'pending').length
              const queuedCount = pending.filter(p => p.status === 'queued').length
              const processingCount = pending.filter(p => p.status === 'processing').length
              const failedCount = pending.filter(p => p.status === 'failed').length
              const stackedTotal = pendingCount + queuedCount + processingCount + failedCount

              const handleDragStart = (e, id) => { setDragId(id); e.dataTransfer.effectAllowed = 'move' }
              const handleDragOver = (e, colId) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; setDragOverCol(colId) }
              const handleDragLeave = () => { setDragOverCol(null) }
              const handleDrop = (e, colId) => {
                e.preventDefault(); setDragOverCol(null)
                if (!dragId) return
                if (colId === 'pending') resetPending(dragId)
                else if (colId === 'queued') processPending(dragId)
                else if (colId === 'processing') processPending(dragId)
                setDragId(null)
              }

              return (
                <div className="flex gap-2 h-[calc(100vh-80px)]">
                  {/* Processing Jobs column */}
                  <div className="w-1/4 flex flex-col rounded-lg border overflow-hidden bg-card">
                    <div className="px-2 py-1.5 flex items-center gap-1 shrink-0 bg-gradient-to-r from-primary/10 to-primary/5 border-b border-primary/20">
                      <Gear className="w-4 h-4 text-primary" />
                      <span className="font-bold text-xs text-primary">Processing Jobs</span>
                      <Badge variant="default" className="ml-auto text-[0.5rem] h-4">{stackedTotal}</Badge>
                    </div>
                    <div className="flex flex-col flex-1 min-h-0 p-2">
                      {/* Add URL */}
                      <div className="rounded border p-1.5 shrink-0 mb-1 bg-muted min-w-0">
                        <Input type="url" value={urlInput} onChange={e => { setUrlInput(e.target.value); setUrlError('') }}
                          onKeyDown={e => e.key === 'Enter' && submitUrl()}
                          placeholder="Paste LinkedIn URL..."
                          className={cn("w-full h-7 rounded border text-[0.6rem] min-w-0", urlError && "border-destructive")} />
                        {urlError && <div className="text-[0.5rem] mt-1 px-0.5 flex items-center gap-1 text-destructive"><Warning className="w-2.5 h-2.5" /> {urlError}</div>}
                        <div className="flex items-center gap-1 mt-1">
                          <Button onClick={submitUrl} disabled={submitting || !urlInput.trim()} size="sm" className="flex-1 h-6 text-[0.55rem]">
                            {submitting ? '...' : processImmediately ? 'Add & Process' : 'Add'}
                          </Button>
                          <button
                            onClick={() => setProcessImmediately(v => !v)}
                            className={cn(
                              "shrink-0 h-6 px-1.5 rounded text-[0.5rem] font-medium border transition-colors",
                              processImmediately
                                ? "bg-primary text-primary-foreground border-primary"
                                : "bg-background text-muted-foreground border-border hover:bg-muted"
                            )}
                          >
                            {processImmediately ? 'Auto' : 'Queue'}
                          </button>
                        </div>
                      </div>
                      {/* Stacked sections */}
                      <div className="flex flex-col flex-1 min-h-0 gap-1">
                        {[
                          { id: 'pending', count: pendingCount, label: 'Pending', icon: <Clock className="w-3 h-3" />, color: 'gray', iconClass: 'text-gray-500', bgClass: 'bg-gradient-to-r from-gray-500/10 to-gray-500/5', borderClass: 'border-b border-gray-500/20', textClass: 'text-gray-600 dark:text-gray-400' },
                          { id: 'queued', count: queuedCount, label: 'Queued', icon: <Stack className="w-3 h-3" />, color: 'yellow', iconClass: 'text-yellow-500', bgClass: 'bg-gradient-to-r from-yellow-500/10 to-yellow-500/5', borderClass: 'border-b border-yellow-500/20', textClass: 'text-yellow-600 dark:text-yellow-500' },
                          { id: 'processing', count: processingCount, label: 'Processing', icon: <Gear className="w-3 h-3" />, color: 'blue', iconClass: 'text-blue-500', bgClass: 'bg-gradient-to-r from-blue-500/10 to-blue-500/5', borderClass: 'border-b border-blue-500/20', textClass: 'text-blue-600 dark:text-blue-500' },
                          { id: 'failed', count: failedCount, label: 'Failed', icon: <X className="w-3 h-3" />, color: 'red', iconClass: 'text-red-500', bgClass: 'bg-gradient-to-r from-red-500/10 to-red-500/5', borderClass: 'border-b border-red-500/20', textClass: 'text-red-600 dark:text-red-500' },
                        ].map(s => {
                          const isEmpty = s.count === 0
                          const isOpen = isEmpty ? false : !collapsedSections[s.id]
                          return (
                            <div key={s.id} className={cn("flex flex-col rounded-lg border min-w-0 max-w-full overflow-hidden", isOpen ? "flex-1 min-h-0" : "", isEmpty && "opacity-60")}>
                              <div onClick={() => !isEmpty && setCollapsedSections(prev => ({ ...prev, [s.id]: !prev[s.id] }))}
                                className={cn("px-2 py-1 flex items-center gap-1 shrink-0 transition", !isEmpty && "cursor-pointer select-none hover:bg-muted/50", s.bgClass, s.borderClass)}>
                                <span className={s.iconClass}>{s.icon}</span>
                                <span className={cn("font-bold text-[0.6rem] uppercase tracking-wider", s.textClass)}>{s.label}</span>
                                <Badge variant="secondary" className={cn("text-[0.5rem] h-4 ml-auto", isEmpty && "bg-muted text-muted-foreground")}>{s.count}</Badge>
                                {!isEmpty && <span className="text-[0.5rem] text-muted-foreground">{isOpen ? '▾' : '▸'}</span>}
                              </div>
                              {isOpen && s.id === 'pending' && (
                                <ScrollArea className="flex-1 min-h-0 min-w-0"
                                  onDragOver={e => handleDragOver(e, 'pending')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'pending')}>
                                  <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                                    {pending.filter(p => p.status === 'pending').map(p =>
                                      <ProcessingItem key={p.id} item={p} onProcess={() => processPending(p.id)} onDelete={() => deletePending(p.id)} onDragStart={e => handleDragStart(e, p.id)} onViewWorkflow={openWorkflow} />)}
                                  </div>
                                </ScrollArea>
                              )}
                              {isOpen && s.id === 'queued' && (
                                <ScrollArea className="flex-1 min-h-0 min-w-0"
                                  onDragOver={e => handleDragOver(e, 'queued')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'queued')}>
                                  <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                                    {pending.filter(p => p.status === 'queued').map(p =>
                                      <ProcessingItem key={p.id} item={p} onProcess={() => processPending(p.id)} onDelete={() => deletePending(p.id)} onReset={() => resetPending(p.id)} onDragStart={e => handleDragStart(e, p.id)} onViewWorkflow={openWorkflow} />)}
                                  </div>
                                </ScrollArea>
                              )}
                              {isOpen && s.id === 'processing' && (
                                <ScrollArea className="flex-1 min-h-0 min-w-0"
                                  onDragOver={e => handleDragOver(e, 'processing')} onDragLeave={handleDragLeave} onDrop={e => handleDrop(e, 'processing')}>
                                  <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                                    {pending.filter(p => p.status === 'processing').map(p =>
                                      <ProcessingItem key={p.id} item={p} onDragStart={e => handleDragStart(e, p.id)}
                                        onPause={() => pausePending(p.id)} onDelete={() => deletePending(p.id)} onViewWorkflow={openWorkflow} />)}
                                  </div>
                                </ScrollArea>
                              )}
                              {isOpen && s.id === 'failed' && (
                                <ScrollArea className="flex-1 min-h-0 min-w-0">
                                  <div className="p-1 space-y-1 min-w-0 max-w-full overflow-hidden">
                                    {pending.filter(p => p.status === 'failed').map(p =>
                                      <ProcessingItem key={p.id} item={p} onDelete={() => deletePending(p.id)} onProcess={() => processPending(p.id)} onReset={() => resetPending(p.id)} onViewWorkflow={openWorkflow} />)}
                                  </div>
                                </ScrollArea>
                              )}
                            </div>
                          )
                        })}
                      </div>
                      {stackedTotal === 0 && <div className="text-center py-8 text-[0.6rem] text-muted-foreground shrink-0">All jobs processed</div>}
                    </div>
                  </div>

                  {/* Processed Jobs column */}
                  <div className="w-3/4 flex flex-col rounded-lg border overflow-hidden bg-card">
                    <div className="px-2 py-1.5 flex items-center gap-1 shrink-0 bg-gradient-to-r from-green-500/10 to-green-500/5 border-b border-green-500/20">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="font-bold text-xs text-green-500">Processed Jobs</span>
                      <Badge variant="secondary" className="text-[0.5rem] h-4 bg-green-500/15 text-green-500">{filteredJobs.length}/{jobsTotal}</Badge>
                      <div className="flex items-center gap-0.5 ml-auto">
                        <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => refreshJobs()} title="Refresh"><ArrowsClockwise className="w-3 h-3 text-green-500" /></Button>
                        <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => rescoreAll()} title="Rescore all"><TrendUp className="w-3 h-3 text-primary" /></Button>
                        <Button variant="ghost" size="icon" className="h-5 w-5" onClick={() => reprocessAll()} title="Reprocess all"><Repeat className="w-3 h-3 text-yellow-500" /></Button>
                      </div>
                    </div>
                    <div ref={jobsScrollRef} className="flex-1 overflow-y-auto">
                      <div className="sticky top-0 z-10 bg-card p-2 pb-0">
                        <div className="flex items-center gap-1 mb-2">
                          <div className="relative flex-1">
                            <Input value={filterTech} onChange={e => setFilterTech(e.target.value)}
                              placeholder="Search by role, company, stack, or notes..."
                              className={cn("w-full h-7 text-xs", filterTech && "border-green-500 ring-1 ring-green-500/20")} />
                            {filterTech && <button onClick={() => setFilterTech('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-[0.55rem] text-muted-foreground">✕</button>}
                          </div>
                          {activeFilterCount > 0 && <Button variant="ghost" size="sm" className="h-7 text-[0.6rem] text-green-500 hover:text-green-600 hover:bg-green-500/10" onClick={clearFilters}>Clear all</Button>}
                        </div>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-1">
                            <Select value={sortBy} onValueChange={(v) => { setSortBy(v); setSortDir('desc') }}>
                              <SelectTrigger className="h-7 w-auto text-[0.6rem] border-green-500/30"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="created_at">Newest first</SelectItem>
                                <SelectItem value="posted_at">Posted date</SelectItem>
                                <SelectItem value="score">Score (Fit)</SelectItem>
                                <SelectItem value="score_success">Score (Success)</SelectItem>
                                <SelectItem value="score_combined">Score (Combined)</SelectItem>
                                <SelectItem value="applicants">Applicants</SelectItem>
                                <SelectItem value="company">Company</SelectItem>
                                <SelectItem value="location">Location</SelectItem>
                                <SelectItem value="apply_time">Applied date</SelectItem>
                                <SelectItem value="response_time">Response date</SelectItem>
                              </SelectContent>
                            </Select>
                            <Button variant="outline" size="sm" className="h-7 text-[0.6rem] border-green-500/30 text-green-500 hover:bg-green-500/10" onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')}>
                              {sortDir === 'desc' ? '↓' : '↑'}
                            </Button>
                          </div>
                          <div className="flex items-center gap-1 flex-wrap justify-end">
                            <MultiSelect value={filterCities} onChange={setFilterCities} placeholder="City" icon={<MapPin className="w-3 h-3" />} options={allCities.map(c => ({ value: c, label: c }))} />
                            <MultiSelect value={filterCompanies} onChange={setFilterCompanies} placeholder="Co" icon={<Buildings className="w-3 h-3" />} options={allCompanies.map(c => ({ value: c, label: c }))} />
                            <MultiSelect value={filterMatches} onChange={setFilterMatches} placeholder="Match" icon={<Target className="w-3 h-3" />} options={[{ value: 'High', label: 'High' }, { value: 'Medium', label: 'Medium' }, { value: 'Low', label: 'Low' }]} />
                            <MultiSelect value={filterWorkTypes} onChange={setFilterWorkTypes} placeholder="Work" icon={<HouseSimple className="w-3 h-3" />} options={[{ value: 'On-site', label: 'On-site' }, { value: 'Remote', label: 'Remote' }, { value: 'Hybrid', label: 'Hybrid' }]} />
                            <MultiSelect value={filterEmploymentTypes} onChange={setFilterEmploymentTypes} placeholder="Emp" icon={<Briefcase className="w-3 h-3" />} options={[{ value: 'Full-time', label: 'Full-time' }, { value: 'Part-time', label: 'Part-time' }, { value: 'Contract', label: 'Contract' }, { value: 'Internship', label: 'Internship' }, { value: 'Temporary', label: 'Temporary' }]} />
                            <MultiSelect value={filterResponseStatus} onChange={setFilterResponseStatus} placeholder="Status" icon={<CheckCircle className="w-3 h-3" />} options={[{ value: 'Interview', label: 'Interview' }, { value: 'Rejected', label: 'Rejected' }]} />
                            <Button variant={filterApplied ? "default" : "outline"} size="sm" className={cn("h-7 text-[0.6rem]", filterApplied && "bg-green-500/20 text-green-500 border-green-500/30 hover:bg-green-500/30")} onClick={() => setFilterApplied(f => !f)}>
                              <PaperPlaneRight className="w-3 h-3 mr-0.5" />Applied
                            </Button>
                          </div>
                        </div>
                      </div>
                      <div className="p-2">
                        <div className="grid gap-2" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
                          {filteredJobs.map((j, i) => <JobCard key={j.num} job={j} rank={i + 1} onClick={() => openDrawer(j.num)} onRescore={rescoreJob} onDelete={deleteJob} onRequeue={requeueJob} onViewWorkflow={openWorkflow} />)}
                        </div>
                        <div ref={jobsSentinelRef} className="h-1" />
                        {loadingMore && <div className="text-center py-2 text-[0.6rem] text-muted-foreground">Loading more...</div>}
                        {!loadingMore && filteredJobs.length >= jobsTotal && filteredJobs.length > 0 && <div className="text-center py-2 text-[0.55rem] text-muted-foreground opacity-50">All {jobsTotal} jobs loaded</div>}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })()}

            {/* === DASHBOARD TAB === */}
            {tab === 'dashboard' && (
              <DashboardTab analysis={analysis} jobs={jobs} resumes={resumes} linkedinProfiles={linkedinProfiles} cities={cities} rules={rules} dashboardSubTab={dashboardSubTab} refreshing={refreshing} onSetDashboardSubTab={setDashboardSubTab} onRefreshAnalysis={refreshAnalysis} onRefreshStrategy={refreshStrategy} onRefreshNetworking={refreshNetworking} onRefreshSkillsTab={refreshSkillsTab} onOpenDrawer={openDrawer} />
            )}

            {/* === RESUME === */}
            {tab === 'resume' && <ResumeTab resumes={resumes} linkedinProfiles={linkedinProfiles} onRefreshResumes={() => fetch(`${API}/resumes`).then(r => r.json()).then(r => setResumes(r))} onRefreshLinkedin={() => fetch(`${API}/linkedin`).then(r => r.json()).then(r => setLinkedinProfiles(r))} />}

            {/* === PREFERENCES === */}
            {tab === 'rules' && <RulesTab rules={rules} onUpdate={fetchRules} />}
          </div>
        </div>
      </main>

      <JobDrawer drawer={drawer} drawerTab={drawerTab} generatingResume={generatingResume} generatingCover={generatingCover} onClose={() => setDrawer(null)} onSetDrawerTab={setDrawerTab} onRescoreJob={rescoreJob} onRequeueJob={requeueJob} onUpdateJob={updateJob} onSetToast={(msg) => { setToast(msg); if (msg) setTimeout(() => setToast(null), 2000) }} onGenerateResume={generateResume} onGenerateCover={generateCover} />

      {/* Confirm Dialog */}
      <AlertDialog open={!!confirmDialog} onOpenChange={(open) => { if (!open && confirmDialog) { confirmDialog.resolve(false); setConfirmDialog(null) } }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmDialog?.title}</AlertDialogTitle>
            <AlertDialogDescription>{confirmDialog?.message}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => { confirmDialog?.resolve(false); setConfirmDialog(null) }}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => { confirmDialog?.resolve(true); setConfirmDialog(null) }}
              className={cn(confirmDialog?.variant === 'warning' ? 'bg-yellow-500 hover:bg-yellow-600' : confirmDialog?.variant === 'info' ? '' : 'bg-destructive hover:bg-destructive/90')}>
              {confirmDialog?.confirmLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Duplicate Job Dialog */}
      <Dialog open={!!duplicateJob} onOpenChange={(open) => !open && setDuplicateJob(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Warning className="w-5 h-5 text-yellow-500" />
              Job Already Exists
            </DialogTitle>
            <DialogDescription>How would you like to update this job?</DialogDescription>
          </DialogHeader>
          <Card className="p-3 bg-muted">
            <div className="text-sm font-bold">#{duplicateJob?.num} {duplicateJob?.company}</div>
            <div className="text-xs mt-1 text-muted-foreground">
              Score: <span className="font-bold" style={{ color: ['A','A+','A++'].includes(duplicateJob?.score) ? '#22c55e' : ['B','C'].includes(duplicateJob?.score) ? '#eab308' : '#ef4444' }}>{duplicateJob?.score}</span>
              {' · '}
              Match: <span className="font-bold text-primary">{duplicateJob?.match}</span>
            </div>
          </Card>
          <DialogFooter className="flex-row gap-2">
            <Button className="flex-1 gap-1" onClick={async () => { await fetch(`${API}/jobs/${duplicateJob.num}/rescore`, { method: 'POST' }); fetchPending(); refreshJobs(); setDuplicateJob(null) }}>
              <TrendUp className="w-3.5 h-3.5" /> Rescore
            </Button>
            <Button variant="outline" className="flex-1 gap-1" onClick={async () => { await fetch(`${API}/jobs/${duplicateJob.num}/requeue`, { method: 'POST' }); fetchPending(); refreshJobs(); setDuplicateJob(null) }}>
              <Repeat className="w-3.5 h-3.5" /> Reprocess
            </Button>
            <Button variant="ghost" onClick={() => setDuplicateJob(null)}>Cancel</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Workflow Terminal Drawer */}
      <Sheet open={!!workflowDrawer} onOpenChange={(open) => { if (!open) { workflowWs.current?.close(); setWorkflowDrawer(null); setWorkflowLogs([]) } }}>
        <SheetContent className="w-[min(600px,92vw)] sm:max-w-[600px] flex flex-col p-0">
          <SheetHeader className="px-4 py-2.5 border-b">
            <div className="flex items-center gap-2">
              <span className="text-sm">💻</span>
              <SheetTitle className="text-sm">Workflow Terminal</SheetTitle>
              <Badge variant="secondary" className="text-[0.6rem]">{workflowDrawer?.company || 'Job'} #{workflowDrawer?.job_num || '?'}</Badge>
              {workflowDrawer?.status === 'processing' && (
                <Badge variant="default" className="text-[0.55rem] animate-pulse">● LIVE</Badge>
              )}
            </div>
          </SheetHeader>

          {/* Step progress */}
          <div className="px-4 py-2 flex gap-1 border-b bg-muted overflow-x-auto">
            {['fetch', 'validate', 'extract_raw', 'extract_struct', 'summary', 'resume', 'score', 'done'].map((s, i) => {
              const stepVal = workflowDrawer?.[`step_${s}`]
              const isDone = stepVal === 1
              const isActive = !isDone && workflowLogs.some(l => l.step === s)
              return (
                <div key={s} className="flex items-center gap-0.5 shrink-0">
                  <div className={cn(
                    "w-4 h-4 rounded-full flex items-center justify-center text-[0.45rem] font-bold transition-all border",
                    isDone ? "bg-green-500 text-white border-green-500" :
                    isActive ? "bg-primary text-primary-foreground border-primary" :
                    "bg-background text-muted-foreground border-border"
                  )}>
                    {isDone ? <Check className="w-2.5 h-2.5" /> : isActive ? <Spinner className="w-2.5 h-2.5 animate-spin" /> : i + 1}
                  </div>
                  {i < 7 && <div className={cn("h-[1px] w-3 rounded-full", isDone ? "bg-green-500" : "bg-border")} />}
                </div>
              )
            })}
          </div>

          {/* Terminal output */}
          <ScrollArea ref={workflowEndRef} className="flex-1 font-mono text-[0.7rem] leading-relaxed bg-[#0d1117] text-[#c9d1d9]">
            <div className="p-3">
              {workflowLogs.length === 0 && (
                <div className="text-center py-12 text-[#484f58]">
                  <Spinner className="w-8 h-8 animate-spin mx-auto mb-2" />
                  <div>Waiting for workflow output...</div>
                  <div className="text-[0.6rem] mt-1 text-[#21262d]">WebSocket connecting to stream server...</div>
                </div>
              )}
              {workflowLogs.map((log, i) => {
                const isCmd = log.step === 'cmd'; const isOut = log.step === 'out'; const isErr = log.step === 'err'
                const isMimo = log.step === 'mimo'; const isStep = log.step === 'step'; const isError = log.step === 'error'; const isDone = log.step === 'done'
                return (
                  <div key={i} className={cn("mb-0.5", isError || isErr ? "bg-red-500/10 -mx-3 px-3 py-0.5 rounded" : "")}>
                    {isCmd ? <div className="flex gap-2"><span className="text-[#484f58] shrink-0">{log.ts}</span><span className="text-[#58a6ff]">$</span><span className="text-[#58a6ff]">{log.msg}</span></div> :
                     isOut ? <div className="pl-[70px] text-[#8b949e]">{log.msg}</div> :
                     isErr ? <div className="flex gap-2"><span className="text-[#484f58] shrink-0">{log.ts}</span><span className="text-[#f85149]">✗</span><span className="text-[#f85149]">{log.msg}</span></div> :
                     <div className="flex gap-2">
                       <span className="text-[#484f58] shrink-0">{log.ts}</span>
                       {!isMimo && !isStep && <span className="font-bold uppercase shrink-0 text-[#58a6ff]" style={{ minWidth: '50px' }}>[{log.step}]</span>}
                       <span className={isMimo ? 'whitespace-pre-wrap' : ''} style={{ color: isError ? '#f85149' : isDone || isStep ? '#3fb950' : '#c9d1d9' }}>
                         {isStep ? <><span className="text-[#3fb950]">✓</span> {log.msg}</> : isDone ? <><Confetti className="w-4 h-4 inline text-[#3fb950]" /> {log.msg}</> : log.msg}
                       </span>
                     </div>}
                  </div>
                )
              })}
              {workflowDrawer?.status === 'processing' && (
                <div className="flex gap-2 mt-1">
                  <span className="text-[#484f58]">{new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                  <span className="text-[#22c55e]">$</span>
                  <span className="animate-pulse text-[#22c55e]">█</span>
                </div>
              )}
            </div>
          </ScrollArea>
        </SheetContent>
      </Sheet>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[300] px-4 py-2 rounded-lg text-sm font-bold text-white shadow-lg transition-all duration-300 bg-green-500">
          {toast}
        </div>
      )}
    </div>
  )
}

export default App
